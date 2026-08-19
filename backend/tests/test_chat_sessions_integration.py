import os

os.environ["DEBUG"] = "true"

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.dependencies.database import get_db
from app.dependencies.services import get_llm_model_registry, get_rag_service
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.routers.chat import router as chat_router
from app.routers.rag import router as rag_router
from app.services.rag.rag_service import RAGService


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_knowledge_test",
)


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


def test_chat_session_lifecycle_and_rag_persistence(
    database_session: Session,
) -> None:
    app = FastAPI()
    app.include_router(chat_router)
    app.include_router(rag_router)
    app.dependency_overrides[get_db] = lambda: database_session
    app.dependency_overrides[get_rag_service] = lambda: RAGService(
        retrieval_service=EmptyRetrievalService(),
        llm_service=FailingLLMService(),
    )
    app.dependency_overrides[get_llm_model_registry] = FakeModelRegistry

    with TestClient(app, raise_server_exceptions=False) as client:
        create_response = client.post(
            "/api/v1/chat/sessions",
            json={},
        )

        assert create_response.status_code == 201
        session_id = create_response.json()["id"]

        ask_response = client.post(
            "/api/v1/rag/ask",
            json={
                "question": "What is normalization?",
                "collection_name": "knowledge-base",
                "top_k": 5,
                "session_id": session_id,
            },
        )

        assert ask_response.status_code == 200
        ask_body = ask_response.json()
        assert ask_body["answer"] == (
            "No relevant document chunks were found in the selected collection."
        )

        history_response = client.get(f"/api/v1/chat/sessions/{session_id}")
        assert history_response.status_code == 200

        history = history_response.json()
        assert history["title"] == "What is normalization?"
        assert len(history["messages"]) == 2
        assert history["messages"][0]["role"] == "user"
        assert history["messages"][0]["content"] == "What is normalization?"
        assert history["messages"][1]["role"] == "assistant"

        message_response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={
                "role": "user",
                "content": "Explain 3NF.",
            },
        )
        assert message_response.status_code == 201

        list_response = client.get("/api/v1/chat/sessions")
        assert list_response.status_code == 200
        assert len(list_response.json()["items"]) == 1

        delete_response = client.delete(f"/api/v1/chat/sessions/{session_id}")
        assert delete_response.status_code == 204

        missing_response = client.get(f"/api/v1/chat/sessions/{session_id}")
        assert missing_response.status_code == 404

    assert database_session.query(ChatSession).count() == 0
    assert database_session.query(ChatMessage).count() == 0
