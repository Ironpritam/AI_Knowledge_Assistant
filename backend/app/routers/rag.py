from fastapi import APIRouter, Depends

from app.dependencies.services import get_rag_service
from app.schemas.rag import RAGAskRequest, RAGAskResponse
from app.services.rag.rag_service import RAGService

router = APIRouter(
    prefix="/api/v1/rag",
    tags=["RAG"],
)


@router.post(
    "/ask",
    response_model=RAGAskResponse,
)
def ask(
    request: RAGAskRequest,
    rag_service: RAGService = Depends(get_rag_service),
):
    return rag_service.ask(
        question=request.question,
        collection_name=request.collection_name,
        top_k=request.top_k,
    )