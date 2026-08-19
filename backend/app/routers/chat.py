from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.repositories.chat_repository import (
    ChatMessageRepository,
    ChatSessionRepository,
)
from app.schemas.chat import (
    ChatMessageCreateRequest,
    ChatMessageResponse,
    ChatSessionCreateRequest,
    ChatSessionPageResponse,
    ChatSessionResponse,
)

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"],
)


def _session_repo(db: Session) -> ChatSessionRepository:
    repo = ChatSessionRepository(db)
    if not repo.schema_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Chat tables are not ready yet. "
                "Run `uv run alembic upgrade head` to create them."
            ),
        )
    repo.prune_expired()
    return repo


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    payload: ChatSessionCreateRequest,
    db: Session = Depends(get_db),
):
    repo = _session_repo(db)
    session = repo.create(title=payload.title)
    return repo.get_by_id(session.id, include_messages=True)


@router.get("/sessions", response_model=ChatSessionPageResponse)
def list_sessions(
    limit: int = 50,
    cursor: UUID | None = None,
    db: Session = Depends(get_db),
):
    items, next_cursor = _session_repo(db).list_page(limit=min(limit, 100), cursor=cursor)
    return {"items": items, "next_cursor": next_cursor}


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionResponse,
)
def get_session(
    session_id: UUID,
    message_limit: int = 100,
    before: UUID | None = None,
    db: Session = Depends(get_db),
):
    repo = _session_repo(db)
    session = repo.get_by_id(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    messages, next_before = ChatMessageRepository(db).get_messages_page(
        session_id=session.id,
        limit=min(message_limit, 200),
        before=before,
    )
    return {"id": session.id, "title": session.title, "created_at": session.created_at,
            "updated_at": session.updated_at, "last_message_at": session.last_message_at,
            "expires_at": session.expires_at, "messages": messages, "next_before": next_before}


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_message(
    session_id: UUID,
    payload: ChatMessageCreateRequest,
    db: Session = Depends(get_db),
):
    session_repo = _session_repo(db)
    session = session_repo.get_by_id(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    message = ChatMessageRepository(db).add_message(
        session=session,
        role=payload.role,
        content=payload.content,
    )
    return message


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
):
    if not _session_repo(db).delete(session_id):
        raise HTTPException(status_code=404, detail="Chat session not found.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
