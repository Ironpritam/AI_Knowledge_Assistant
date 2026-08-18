from fastapi import Depends,Request

from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.services.llm.llm_service import LLMService
from app.services.llm.model_registry import LLMModelRegistry
from app.services.rag.rag_service import RAGService
from app.services.vector.chroma_service import ChromaService
from app.services.vector.embedding_service import EmbeddingService
from app.services.vector.retrieval_service import RetrievalService
from app.services.document.ingestion_service import DocumentIngestionService


def get_embedding_service(request: Request) -> EmbeddingService:
    return request.app.state.embedding_service


def get_chroma_service(request: Request) -> ChromaService:
    return request.app.state.chroma_service


def get_llm_service(request: Request) -> LLMService:
    return request.app.state.llm_service


def get_llm_model_registry(request: Request,
    db: Session = Depends(get_db),
) -> LLMModelRegistry:

    return LLMModelRegistry(db=db, app_settings=request.app.state.llm_model_registry.settings)


def get_retrieval_service(request: Request) -> RetrievalService:
    return RetrievalService(
        embedding_service=get_embedding_service(request),
        chroma_service=get_chroma_service(request),
    )


def get_rag_service(request: Request, db: Session = Depends(get_db)) -> RAGService:
    return RAGService(
        retrieval_service=get_retrieval_service(request),
        llm_service=get_llm_service(request),
        db=db,
        query_router=request.app.state.query_router,
    )

def get_ingestion_service(request: Request,) -> DocumentIngestionService:
    # return DocumentIngestionService(
    #     embedding_service=get_embedding_service(request),
    #     chroma_service=get_chroma_service(request),
    # )
    return request.app.state.document_ingestion_service
