from fastapi import Request

from app.services.llm.llm_service import LLMService
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


def get_retrieval_service(request: Request) -> RetrievalService:
    return RetrievalService(
        embedding_service=get_embedding_service(request),
        chroma_service=get_chroma_service(request),
    )


def get_rag_service(request: Request) -> RAGService:
    return RAGService(
        retrieval_service=get_retrieval_service(request),
        llm_service=get_llm_service(request),
    )

def get_ingestion_service(request: Request,) -> DocumentIngestionService:
    # return DocumentIngestionService(
    #     embedding_service=get_embedding_service(request),
    #     chroma_service=get_chroma_service(request),
    # )
    return request.app.state.document_ingestion_service