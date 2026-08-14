from uuid import UUID

from pydantic import BaseModel, Field


class RAGAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    collection_name: str = "test_ingestion_bge"
    top_k: int = Field(default=5, ge=1, le=20)
    document_id: UUID | None = None
    model_id: str | None = Field(default=None, min_length=1, max_length=255)


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
