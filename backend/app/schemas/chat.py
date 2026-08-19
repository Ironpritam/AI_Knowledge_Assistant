from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ChatMessageCreateRequest(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime


class ChatSessionSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime
    expires_at: datetime | None


class ChatSessionResponse(ChatSessionSummaryResponse):
    messages: list[ChatMessageResponse] = Field(default_factory=list)
    next_before: UUID | None = None


class ChatSessionPageResponse(BaseModel):
    items: list[ChatSessionSummaryResponse]
    next_cursor: UUID | None = None
