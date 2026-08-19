from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.chat_audit_event import ChatAuditEvent
from app.models.chat_run import ChatRun


class ChatRunRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, session_id: UUID, client_request_id: UUID) -> ChatRun | None:
        return (
            self.db.query(ChatRun)
            .filter(
                ChatRun.session_id == session_id, ChatRun.client_request_id == client_request_id
            )
            .first()
        )

    def start(self, session_id: UUID, client_request_id: UUID, model_id: str | None) -> ChatRun:
        run = ChatRun(session_id=session_id, client_request_id=client_request_id, model_id=model_id)
        self.db.add(run)
        self.db.flush()
        self.db.add(
            ChatAuditEvent(session_id=session_id, run_id=run.id, event_type="generation_started")
        )
        self.db.commit()
        self.db.refresh(run)
        return run

    def complete(self, run: ChatRun, answer: str, sources: list, latency_ms: int) -> None:
        run.status = "completed"
        run.answer = answer
        run.sources = sources
        run.latency_ms = latency_ms
        run.completed_at = datetime.now(UTC)
        self.db.add(
            ChatAuditEvent(
                session_id=run.session_id,
                run_id=run.id,
                event_type="generation_completed",
                details={"latency_ms": latency_ms},
            )
        )
        self.db.commit()

    def fail(self, run: ChatRun, error_message: str) -> None:
        run.status = "failed"
        run.error_message = error_message[:2000]
        run.completed_at = datetime.now(UTC)
        self.db.add(
            ChatAuditEvent(session_id=run.session_id, run_id=run.id, event_type="generation_failed")
        )
        self.db.commit()
