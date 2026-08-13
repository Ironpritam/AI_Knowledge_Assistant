from pydantic import BaseModel, Field


class RAGAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    collection_name: str = "documents"
    top_k: int = Field(default=5, ge=1, le=20)


class RAGSource(BaseModel):
    source: str
    page: int
    chunk_index: int


class RAGAskResponse(BaseModel):
    question: str
    answer: str
    sources: list[RAGSource]