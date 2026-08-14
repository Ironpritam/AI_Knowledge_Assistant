from contextlib import asynccontextmanager

from app.core.settings import settings
from app.services.vector.embedding_service import EmbeddingService
from app.services.vector.chroma_service import ChromaService
from app.services.llm.llm_service import LLMService
from app.services.llm.model_registry import LLMModelRegistry
from app.services.document.ingestion_service import DocumentIngestionService



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
    default_model = llm_model_registry.resolve()
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

    app.state.embedding_service = embedding_service
    app.state.llm_service = llm_service
    app.state.llm_model_registry = llm_model_registry
    app.state.chroma_service = chroma_service
    app.state.document_ingestion_service = document_ingestion_service

    print("✅ AI Knowledge Assistant ready")
    yield
    print("🛑 Shutting down AI Knowledge Assistant")
