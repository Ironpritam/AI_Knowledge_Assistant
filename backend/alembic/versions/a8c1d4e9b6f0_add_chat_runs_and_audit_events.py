"""add chat runs and audit events

Revision ID: a8c1d4e9b6f0
Revises: 7fb4d7f2d2a4
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a8c1d4e9b6f0"
down_revision = "7fb4d7f2d2a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_runs",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("model_id", sa.String(length=255)),
        sa.Column("answer", sa.Text()),
        sa.Column("sources", postgresql.JSONB()),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("error_message", sa.Text()),
        sa.Column("feedback_rating", sa.Integer()),
        sa.Column("feedback_comment", sa.Text()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("session_id", "client_request_id", name="uq_chat_runs_session_request"),
    )
    op.create_index("ix_chat_runs_session_created_at", "chat_runs", ["session_id", "created_at"])
    op.create_table(
        "chat_audit_events",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True)),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("details", postgresql.JSONB()),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["chat_runs.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_chat_audit_events_session_created_at", "chat_audit_events", ["session_id", "created_at"])


def downgrade() -> None:
    op.drop_table("chat_audit_events")
    op.drop_table("chat_runs")
