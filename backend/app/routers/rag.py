import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.dependencies.database import get_db
from app.dependencies.services import get_llm_model_registry, get_rag_service
from app.repositories.chat_repository import (
    ChatMessageRepository,
    ChatSessionRepository,
)
from app.repositories.chat_run_repository import ChatRunRepository
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
    chat_session_repository = ChatSessionRepository(db)
    chat_message_repository = ChatMessageRepository(db)
    chat_run_repository = ChatRunRepository(db)
    chat_session_repository.prune_expired()

    documents: list = []
    if request.document_ids:
        repository = DocumentRepository(db)
        documents = repository.get_all(request.document_ids)

        if len(documents) != len(set(request.document_ids)):
            raise HTTPException(
                status_code=404, detail="One or more requested documents were not found."
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

    conversation_history: list[dict] = []
    chat_session = None
    if request.session_id is not None:
        chat_session = chat_session_repository.get_by_id(
            request.session_id,
            include_messages=True,
        )
        if chat_session is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found.",
            )

        conversation_history = [
            {"role": message.role, "content": message.content}
            for message in chat_message_repository.get_history_for_session(
                session_id=chat_session.id,
                max_turns=settings.CHAT_HISTORY_MAX_TURNS,
                max_chars=settings.CHAT_HISTORY_MAX_CHARS,
            )
        ]

        if request.client_request_id is not None:
            existing_run = chat_run_repository.get(chat_session.id, request.client_request_id)
            if existing_run is not None:
                if existing_run.status == "completed":
                    return {
                        "question": request.question,
                        "answer": existing_run.answer,
                        "model_id": existing_run.model_id,
                        "sources": existing_run.sources or [],
                    }
                raise HTTPException(
                    status_code=409, detail="This chat request is already being processed."
                )

    selected_model = model_registry.resolve(request.model_id)
    llm_service = (
        rag_service.llm_service
        if request.model_id is None or selected_model.id == model_registry.default_model_id
        else LLMService(
            provider=selected_model.provider,
            model=selected_model.model,
        )
    )

    rag_service = RAGService(
        retrieval_service=rag_service.retrieval_service,
        llm_service=llm_service,
        db=db,
        query_router=rag_service.query_router,
    )

    run = None
    if chat_session is not None and request.client_request_id is not None:
        run = chat_run_repository.start(
            chat_session.id, request.client_request_id, selected_model.id
        )

    started_at = time.perf_counter()
    try:
        response = rag_service.ask(
            question=request.question,
            collection_name=request.collection_name,
            top_k=request.top_k,
            document_ids=[str(doc.id) for doc in documents] if request.document_ids else None,
            model_id=selected_model.id,
            conversation_history=conversation_history,
        )
    except Exception as exc:
        if run is not None:
            chat_run_repository.fail(run, str(exc))
        raise

    if chat_session is not None:
        chat_message_repository.add_turn(
            session=chat_session,
            question=request.question,
            answer=response["answer"],
        )
    if run is not None:
        chat_run_repository.complete(
            run,
            response["answer"],
            response["sources"],
            int((time.perf_counter() - started_at) * 1000),
        )

    return response
