from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin


class LLMModel(Base, TimestampMixin):
    __tablename__ = "llm_models"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    label: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
