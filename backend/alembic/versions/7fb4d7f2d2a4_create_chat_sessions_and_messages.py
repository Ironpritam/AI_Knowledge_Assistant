"""create chat sessions and chat messages tables

Revision ID: 7fb4d7f2d2a4
Revises: 281c633b97ed
Create Date: 2026-08-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "7fb4d7f2d2a4"
down_revision = "281c633b97ed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column(
            "last_message_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_table(
        "chat_messages",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["chat_sessions.id"],
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_chat_messages_session_id",
        "chat_messages",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_chat_messages_session_id_created_at",
        "chat_messages",
        ["session_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_chat_messages_session_id_created_at", table_name="chat_messages")
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
