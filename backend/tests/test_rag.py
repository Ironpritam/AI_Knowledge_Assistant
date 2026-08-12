from app.services.rag.rag_service import RAGService
from app.services.vector.embedding_service import EmbeddingService
from app.services.vector.chroma_service import ChromaService
from app.services.vector.retrieval_service import RetrievalService
from app.services.llm.llm_service import LLMService

embedding_service = EmbeddingService(model_name="bge-small")

chroma_service = ChromaService()

retrieval_service = RetrievalService(embedding_service=embedding_service,chroma_service=chroma_service,)

llm_service = LLMService(provider="ollama",model="qwen3:8b",)

rag_service = RAGService(retrieval_service=retrieval_service,llm_service=llm_service,)

def test_rag_question():
    # rag = RAGService(
    #     embedding_model="bge-small",
    #     llm_provider="ollama",
    #     llm_model="qwen3:8b",
    #     collection_name="test_ingestion_bge",
    # )

    result = rag_service.ask(
        question=(
            "Why did the authors propose "
            "the Transformer architecture?"
        ),
        collection_name="test_ingestion_bge",
        top_k=5,
    )

    assert result["answer"]
    assert len(result["sources"]) == 5

    print("\n" + "=" * 80)
    print("QUESTION")
    print("=" * 80)

    print(result["question"])

    print("\n" + "=" * 80)
    print("ANSWER")
    print("=" * 80)

    print(result["answer"])

    print("\n" + "=" * 80)
    print("SOURCES")
    print("=" * 80)

    for source in result["sources"]:
        print(
            f"Page {source['page']} | "
            f"Chunk {source['chunk_index']}"
        )

def test_rag_rejects_unanswerable_question():
    # rag = RAGService(
    #     embedding_model="bge-small",
    #     llm_provider="ollama",
    #     llm_model="qwen3:8b",
    #     collection_name="test_ingestion_bge",
    # )

    result = rag_service.ask(
        question="What is the capital of France?",
        collection_name="test_ingestion_bge",
        top_k=5,
    )

    print("\n" + "=" * 80)
    print("UNANSWERABLE QUESTION")
    print("=" * 80)

    print(result["answer"])

    assert result["answer"]

def test_rag_question_2():
    # rag = RAGService(
    #     embedding_model="bge-small",
    #     llm_provider="ollama",
    #     llm_model="qwen3:8b",
    #     collection_name="test_ingestion_bge",
    # )

    result = rag_service.ask(
        question=("What are the main components of the Transformer architecture?"),
        collection_name="test_ingestion_bge",
        top_k=5,
    )

    assert result["answer"]
    assert len(result["sources"]) == 5

    print("\n" + "=" * 80)
    print("QUESTION")
    print("=" * 80)

    print(result["question"])

    print("\n" + "=" * 80)
    print("ANSWER")
    print("=" * 80)

    print(result["answer"])

    print("\n" + "=" * 80)
    print("SOURCES")
    print("=" * 80)

    for source in result["sources"]:
        print(
            f"Page {source['page']} | "
            f"Chunk {source['chunk_index']}"
        )

