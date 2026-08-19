from app.services.rag.query_router import (
    DocumentRetrievalStrategy,
    QueryIntentRouter,
)
from app.services.rag.rag_service import RAGService
from app.services.vector.retrieval_service import RetrievalService


class FakeEmbeddingService:
    model_key = "test-model"
    dimension = 3

    def embed_query(self, query: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeChromaService:
    def __init__(self) -> None:
        self.search_calls: list[dict] = []

    def get_collection(self, **kwargs):
        return object()

    def search(self, *, top_k: int, where=None, **kwargs) -> list[dict]:
        self.search_calls.append({"top_k": top_k, "where": where})
        document_id = (
            where["document_id"]
            if where and "document_id" in where
            else "relevance-result"
        )
        return [
            {
                "text": f"{document_id} chunk {index}",
                "metadata": {"document_id": document_id},
                "distance": float(index),
            }
            for index in range(top_k)
        ]


def test_selected_documents_each_contribute_to_retrieval_context() -> None:
    chroma_service = FakeChromaService()
    service = RetrievalService(FakeEmbeddingService(), chroma_service)

    results = service.retrieve(
        query="summarize the selected documents",
        top_k=5,
        document_ids=["first", "second"],
        ensure_document_coverage=True,
    )

    assert chroma_service.search_calls == [
        {"top_k": 3, "where": {"document_id": "first"}},
        {"top_k": 3, "where": {"document_id": "second"}},
    ]
    assert [item["metadata"]["document_id"] for item in results] == [
        "first", "second", "first", "second", "first", "second"
    ]


def test_normal_question_uses_pooled_relevance_ranking() -> None:
    chroma_service = FakeChromaService()
    service = RetrievalService(FakeEmbeddingService(), chroma_service)

    service.retrieve(
        query="What is the resignation notice period?",
        top_k=5,
        document_ids=["first", "second"],
    )

    assert chroma_service.search_calls == [
        {
            "top_k": 5,
            "where": {
                "$or": [
                    {"document_id": "first"},
                    {"document_id": "second"},
                ]
            },
        }
    ]


def test_single_document_uses_a_direct_chroma_filter() -> None:
    chroma_service = FakeChromaService()
    service = RetrievalService(FakeEmbeddingService(), chroma_service)

    service.retrieve(
        query="Summarize this document.",
        top_k=5,
        document_ids=["only-document"],
    )

    assert chroma_service.search_calls == [
        {"top_k": 5, "where": {"document_id": "only-document"}}
    ]


def test_document_retrieval_strategy_only_requires_coverage_for_explicit_overviews() -> None:
    assert QueryIntentRouter.document_retrieval_strategy(
        "Summarize all selected documents.", 3
    ) == DocumentRetrievalStrategy.COVERAGE
    assert QueryIntentRouter.document_retrieval_strategy(
        "What is the resignation notice period?", 3
    ) == DocumentRetrievalStrategy.RELEVANCE


class SingleResultRetrievalService:
    def retrieve(self, **kwargs) -> list[dict]:
        return [
            {
                "text": "A selected document chunk.",
                "metadata": {
                    "source": "selected.pdf",
                    "page": 1,
                    "chunk_index": 0,
                    "document_id": "selected",
                },
                "distance": 0.1,
            }
        ]


class EmptyAnswerLLMService:
    def __init__(self) -> None:
        self.call_count = 0

    def generate(self, messages: list[dict]) -> str:
        self.call_count += 1
        return "   "


def test_empty_llm_answer_is_retried_and_has_a_safe_message() -> None:
    llm_service = EmptyAnswerLLMService()
    service = RAGService(SingleResultRetrievalService(), llm_service)

    response = service.ask(question="Summarize the document.")

    assert llm_service.call_count == 2
    assert response["answer"] == (
        "The language model returned an empty response. "
        "Please retry your question."
    )


class TwoDocumentRetrievalService:
    def retrieve(self, **kwargs) -> list[dict]:
        return [
            {
                "text": "First document text.",
                "metadata": {
                    "source": "first.pdf",
                    "page": 1,
                    "chunk_index": 0,
                    "document_id": "first",
                },
                "distance": 0.1,
            },
            {
                "text": "Second document text.",
                "metadata": {
                    "source": "second.pdf",
                    "page": 1,
                    "chunk_index": 0,
                    "document_id": "second",
                },
                "distance": 0.2,
            },
        ]


class CapturingLLMService:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    def generate(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
    ) -> str:
        self.messages = messages
        self.max_tokens = max_tokens
        return "A complete answer."


def test_coverage_prompt_requires_each_document_and_excludes_history() -> None:
    llm_service = CapturingLLMService()
    service = RAGService(TwoDocumentRetrievalService(), llm_service)

    service.ask(
        question="Summarize all selected documents.",
        document_ids=["first", "second"],
        conversation_history=[{"role": "assistant", "content": "Old answer."}],
    )

    prompt = llm_service.messages[0]["content"]
    assert "first.pdf: approximately" in prompt
    assert "second.pdf: approximately" in prompt
    assert "Do not omit a document" in prompt
    assert "Old answer." not in prompt
    assert 1024 <= llm_service.max_tokens <= 1536
