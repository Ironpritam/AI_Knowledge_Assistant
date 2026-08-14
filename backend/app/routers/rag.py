from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.dependencies.database import get_db
from app.dependencies.services import get_rag_service
from app.repositories.document_repository import DocumentRepository
from app.schemas.rag import RAGAskRequest, RAGAskResponse
from app.services.llm.llm_service import LLMService
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
    db: Session = Depends(get_db),
):
    if request.document_id is not None:
        document = DocumentRepository(db).get_by_id(request.document_id)

        if document is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        if document.collection_name != request.collection_name:
            raise HTTPException(
                status_code=400,
                detail="The selected document does not belong to this collection.",
            )
        if document.status != "processed":
            raise HTTPException(
                status_code=409,
                detail="The selected document is not ready for questions.",
            )

    if request.llm_provider != settings.LLM_PROVIDER or request.llm_model is not None:
        rag_service = RAGService(
            retrieval_service=rag_service.retrieval_service,
            llm_service=LLMService(
                provider=request.llm_provider,
                model=request.llm_model or settings.LLM_MODEL,
            ),
        )

    return rag_service.ask(
        question=request.question,
        collection_name=request.collection_name,
        top_k=request.top_k,
        document_id=str(request.document_id) if request.document_id is not None else None,
    )
