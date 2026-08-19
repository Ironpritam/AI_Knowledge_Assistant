import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin


class ChatRun(Base, TimestampMixin):
    __tablename__ = "chat_runs"
    __table_args__ = (
        UniqueConstraint("session_id", "client_request_id", name="uq_chat_runs_session_request"),
        Index("ix_chat_runs_session_created_at", "session_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    client_request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
