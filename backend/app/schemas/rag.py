from uuid import UUID

from pydantic import BaseModel, Field


class RAGAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    collection_name: str = "test_all_0.0.0.0"
    top_k: int = Field(default=5, ge=1, le=20)
    document_ids: list[UUID] = Field(default_factory=list)
    model_id: str | None = Field(default=None, min_length=1, max_length=255)
    session_id: UUID | None = None
    client_request_id: UUID | None = None


class RAGSource(BaseModel):
    source: str
    page: int
    chunk_index: int
    document_id: UUID | None = None
    collection_name: str
    distance: float


class RAGAskResponse(BaseModel):
    question: str
    answer: str
    model_id: str | None
    sources: list[RAGSource]
