from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.services import get_llm_model_registry, get_rag_service
from app.repositories.document_repository import DocumentRepository
from app.schemas.rag import RAGAskRequest, RAGAskResponse
from app.services.llm.llm_service import LLMService
from app.services.llm.model_registry import LLMModelRegistry
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
    model_registry: LLMModelRegistry = Depends(get_llm_model_registry),
    db: Session = Depends(get_db),
):
    documents: list = []
    if request.document_ids:
        repository = DocumentRepository(db)
        documents = repository.get_all(request.document_ids)

        if len(documents) != len(set(request.document_ids)):
            raise HTTPException(
                status_code=404,
                detail="One or more requested documents were not found."
            )

        for document in documents:
            if document.collection_name != request.collection_name:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Document {document.id} does not belong "
                        f"to collection '{request.collection_name}'."
                    ),
                )

            if document.status != "processed":
                raise HTTPException(
                    status_code=409,
                    detail=f"Document {document.id} is not processed.",
                )
            
    selected_model = model_registry.resolve(request.model_id)
    rag_service = RAGService(
        retrieval_service=rag_service.retrieval_service,
        llm_service=LLMService(
            provider=selected_model.provider,
            model=selected_model.model,
        ),
        db=db,
        query_router=rag_service.query_router,
    )

    return rag_service.ask(
        question=request.question,
        collection_name=request.collection_name,
        top_k=request.top_k,
        document_ids=[str(doc.id) for doc in documents] if request.document_ids else None,
        model_id=selected_model.id,
    )
