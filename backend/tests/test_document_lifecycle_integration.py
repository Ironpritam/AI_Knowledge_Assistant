import os
from pathlib import Path

os.environ["DEBUG"] = "true"

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.dependencies.database import get_db
from app.dependencies.services import (
    get_chroma_service,
    get_ingestion_service,
    get_llm_model_registry,
    get_rag_service,
)
from app.models.document import Document
from app.routers import document as document_router_module
from app.routers.document import router as document_router
from app.routers.rag import router as rag_router
from app.services.document.ingestion_service import DocumentIngestionService
from app.services.rag.rag_service import RAGService
from app.services.vector.chroma_service import ChromaService
from app.services.vector.retrieval_service import RetrievalService


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_knowledge_test",
)


class FakeEmbeddingService:
    model_key = "test-embedding"
    dimension = 3

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, query: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeLLMService:
    def generate(self, messages: list[dict]) -> str:
        return "Grounded test answer."


class EmptyRetrievalService:
    def retrieve(self, **kwargs) -> list[dict]:
        return []


class FailingLLMService:
    def generate(self, messages: list[dict]) -> str:
        raise AssertionError("The LLM must not be called when retrieval is empty.")


class FakeModelRegistry:
    default_model_id = "test:default"

    def resolve(self, model_id: str | None = None):
        resolved_id = model_id or self.default_model_id
        return type(
            "Model",
            (),
            {
                "id": resolved_id,
                "label": "Test model",
                "provider": "ollama",
                "model": "qwen3:8b",
                "enabled": True,
                "is_default": True,
            },
        )()


class FailingIngestionService:
    def __init__(self, chroma_service: ChromaService):
        self.chroma_service = chroma_service

    def ingest(
        self,
        pdf_path: Path,
        collection_name: str,
        document_id: str,
        source_filename: str | None = None,
    ) -> dict:
        collection = self.chroma_service.get_collection(
            collection_name=collection_name,
            embedding_model="test-embedding",
            embedding_dimension=3,
        )
        self.chroma_service.add_chunks(
            collection=collection,
            chunks=[
                {
                    "text": "Partial vector that must be removed.",
                    "metadata": {
                        "source": pdf_path.name,
                        "page": 1,
                        "chunk_index": 0,
                        "document_id": document_id,
                    },
                }
            ],
            embeddings=[[0.1, 0.2, 0.3]],
        )
        raise RuntimeError("Simulated ingestion failure")


@pytest.fixture
def database_session() -> Session:
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_upload_ask_and_delete_document_lifecycle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    database_session: Session,
) -> None:
    upload_directory = tmp_path / "uploads"
    upload_directory.mkdir()
    monkeypatch.setattr(document_router_module, "UPLOAD_DIR", upload_directory)

    embedding_service = FakeEmbeddingService()
    chroma_service = ChromaService(persist_directory=tmp_path / "chroma")
    ingestion_service = DocumentIngestionService(
        embedding_service=embedding_service,
        chroma_service=chroma_service,
    )
    rag_service = RAGService(
        retrieval_service=RetrievalService(embedding_service, chroma_service),
        llm_service=FakeLLMService(),
    )

    app = FastAPI()
    app.include_router(document_router)
    app.include_router(rag_router)
    app.dependency_overrides[get_db] = lambda: database_session
    app.dependency_overrides[get_ingestion_service] = lambda: ingestion_service
    app.dependency_overrides[get_chroma_service] = lambda: chroma_service
    app.dependency_overrides[get_rag_service] = lambda: rag_service
    app.dependency_overrides[get_llm_model_registry] = FakeModelRegistry

    sample_pdf = Path("tests/data/sample.pdf")
    collection_name = "lifecycle-test"

    with TestClient(app) as client, sample_pdf.open("rb") as file:
        upload_response = client.post(
            "/api/v1/documents/upload",
            params={"collection_name": collection_name},
            files={"file": (sample_pdf.name, file, "application/pdf")},
        )

        assert upload_response.status_code == 200
        uploaded = upload_response.json()
        document_id = uploaded["document_id"]
        assert uploaded["vector_count"] == uploaded["chunk_count"]

        document = database_session.get(Document, document_id)
        assert document is not None
        assert document.status == "processed"
        assert Path(document.file_path).exists()

        collection = chroma_service.client.get_collection(collection_name)
        stored_chunks = collection.get(where={"document_id": document_id})
        assert len(stored_chunks["ids"]) == document.chunk_count

        ask_response = client.post(
            "/api/v1/rag/ask",
            json={
                "question": "What is this document about?",
                "collection_name": collection_name,
                "document_id": document_id,
                "top_k": 1,
            },
        )
        assert ask_response.status_code == 200
        answer = ask_response.json()
        assert answer["answer"] == "Grounded test answer."
        assert answer["model_id"] == "test:default"
        assert answer["sources"]
        assert answer["sources"][0]["document_id"] == document_id
        assert answer["sources"][0]["source"] == sample_pdf.name

        with sample_pdf.open("rb") as second_file:
            second_upload = client.post(
                "/api/v1/documents/upload",
                params={"collection_name": "other-collection"},
                files={"file": (sample_pdf.name, second_file, "application/pdf")},
            )
        assert second_upload.status_code == 200
        other_document_id = second_upload.json()["document_id"]

        collection_response = client.post(
            "/api/v1/rag/ask",
            json={
                "question": "What is this document about?",
                "collection_name": collection_name,
                "top_k": 1,
            },
        )
        assert collection_response.status_code == 200
        assert collection_response.json()["sources"][0]["document_id"] == document_id

        delete_response = client.delete(f"/api/v1/documents/{document_id}")
        assert delete_response.status_code == 204
        assert database_session.get(Document, document_id) is None
        assert not Path(document.file_path).exists()
        assert collection.get(where={"document_id": document_id})["ids"] == []
        assert database_session.get(Document, other_document_id) is not None


def test_ask_with_multiple_document_ids_works(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    database_session: Session,
) -> None:
    upload_directory = tmp_path / "uploads"
    upload_directory.mkdir()
    monkeypatch.setattr(document_router_module, "UPLOAD_DIR", upload_directory)

    embedding_service = FakeEmbeddingService()
    chroma_service = ChromaService(persist_directory=tmp_path / "chroma")
    ingestion_service = DocumentIngestionService(
        embedding_service=embedding_service,
        chroma_service=chroma_service,
    )
    rag_service = RAGService(
        retrieval_service=RetrievalService(embedding_service, chroma_service),
        llm_service=FakeLLMService(),
    )

    app = FastAPI()
    app.include_router(document_router)
    app.include_router(rag_router)
    app.dependency_overrides[get_db] = lambda: database_session
    app.dependency_overrides[get_ingestion_service] = lambda: ingestion_service
    app.dependency_overrides[get_chroma_service] = lambda: chroma_service
    app.dependency_overrides[get_rag_service] = lambda: rag_service
    app.dependency_overrides[get_llm_model_registry] = FakeModelRegistry

    sample_pdf = Path("tests/data/sample.pdf")
    collection_name = "multi-doc-test"

    with TestClient(app) as client, sample_pdf.open("rb") as file_one, sample_pdf.open("rb") as file_two:
        first_upload = client.post(
            "/api/v1/documents/upload",
            params={"collection_name": collection_name},
            files={"file": ("one.pdf", file_one, "application/pdf")},
        )
        second_upload = client.post(
            "/api/v1/documents/upload",
            params={"collection_name": collection_name},
            files={"file": ("two.pdf", file_two, "application/pdf")},
        )

    assert first_upload.status_code == 200
    assert second_upload.status_code == 200

    first_id = first_upload.json()["document_id"]
    second_id = second_upload.json()["document_id"]

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/rag/ask",
            json={
                "question": "What is this document about?",
                "collection_name": collection_name,
                "document_ids": [first_id, second_id],
                "top_k": 1,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "What is this document about?"
    assert isinstance(body["answer"], str) and body["answer"]
    assert len(body["sources"]) >= 1


def test_failed_upload_keeps_a_failed_record_and_cleans_the_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    database_session: Session,
) -> None:
    upload_directory = tmp_path / "uploads"
    upload_directory.mkdir()
    monkeypatch.setattr(document_router_module, "UPLOAD_DIR", upload_directory)

    chroma_service = ChromaService(persist_directory=tmp_path / "chroma")
    app = FastAPI()
    app.include_router(document_router)
    app.dependency_overrides[get_db] = lambda: database_session
    app.dependency_overrides[get_ingestion_service] = lambda: FailingIngestionService(
        chroma_service
    )

    sample_pdf = Path("tests/data/sample.pdf")
    with TestClient(app, raise_server_exceptions=False) as client, sample_pdf.open("rb") as file:
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": (sample_pdf.name, file, "application/pdf")},
        )

    assert response.status_code == 500
    failed_document = database_session.query(Document).one()
    assert failed_document.status == "failed"
    assert not Path(failed_document.file_path).exists()
    assert list(upload_directory.iterdir()) == []
    collection = chroma_service.client.get_collection("test_all_0.0.0.0")
    assert collection.get(where={"document_id": str(failed_document.id)})["ids"] == []


def test_rag_returns_a_safe_response_when_retrieval_is_empty() -> None:
    rag_service = RAGService(
        retrieval_service=EmptyRetrievalService(),
        llm_service=FailingLLMService(),
    )

    response = rag_service.ask(question="What is in this collection?")

    assert response == {
        "question": "What is in this collection?",
        "answer": "No relevant document chunks were found in the selected collection.",
        "model_id": None,
        "sources": [],
    }
