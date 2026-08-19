import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from sqlalchemy.exc import SQLAlchemyError

from app.core.settings import settings
from app.database.session import SessionLocal
from app.repositories.chat_repository import ChatSessionRepository
from app.services.document.ingestion_service import DocumentIngestionService
from app.services.llm.llm_service import LLMService
from app.services.llm.model_registry import LLMModelRegistry
from app.services.rag.query_router import QueryIntentRouter
from app.services.vector.chroma_service import ChromaService
from app.services.vector.embedding_service import EmbeddingService

print(f"Using embedding model: {settings.EMBEDDING_MODEL}")
logger = logging.getLogger(__name__)


async def prune_expired_chat_sessions() -> None:
    """Keep expiration cleanup off the request path during normal operation."""
    interval_seconds = max(settings.CHAT_PRUNE_INTERVAL_MINUTES, 1) * 60
    while True:
        db = SessionLocal()
        try:
            ChatSessionRepository(db).prune_expired()
        except SQLAlchemyError:
            logger.exception("Unable to prune expired chat sessions")
        finally:
            db.close()
        await asyncio.sleep(interval_seconds)

@asynccontextmanager
async def lifespan(app):
    print("🚀 Starting AI Knowledge Assistant")


    # --------------------------------------------------
    # Shared embedding service
    # --------------------------------------------------
    print(
        f"Loading embedding model: "
        f"{settings.EMBEDDING_MODEL}"
    )

    embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL)


    # --------------------------------------------------
    # Shared LLM service
    # --------------------------------------------------
    llm_model_registry = LLMModelRegistry()
    default_model = llm_model_registry.resolve(check_availability=False)
    print(f"Configuring LLM: {default_model.provider} / {default_model.model}")

    llm_service = LLMService(
        provider=default_model.provider,
        model=default_model.model,
    )


    # --------------------------------------------------
    # Shared vector database service
    # --------------------------------------------------
    chroma_service = ChromaService()


    document_ingestion_service = DocumentIngestionService(
        embedding_service=embedding_service,
        chroma_service=chroma_service,
    )

    query_router = QueryIntentRouter(
        embedding_service=embedding_service,
        conversation_threshold=0.55,
        document_threshold=0.55,
    )

    app.state.embedding_service = embedding_service
    app.state.llm_service = llm_service
    app.state.llm_model_registry = llm_model_registry
    app.state.chroma_service = chroma_service
    app.state.document_ingestion_service = document_ingestion_service
    app.state.query_router = query_router

    cleanup_task = asyncio.create_task(prune_expired_chat_sessions())
    print("✅ AI Knowledge Assistant ready")
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task
        print("🛑 Shutting down AI Knowledge Assistant")
