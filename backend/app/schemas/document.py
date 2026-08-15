from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

class ChunkMetadata(BaseModel):
    source: str
    page: int
    chunk_index: int


class DocumentChunk(BaseModel):
    text: str
    metadata: ChunkMetadata


class DocumentUploadResponse(BaseModel):
    message: str
    document_id: UUID
    original_filename: str
    stored_filename: str
    collection_name: str
    status: str

    page_count: int
    chunk_count: int

    embedding_model: str
    embedding_dimension: int
    vector_count: int


class DocumentMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    stored_filename: str
    collection_name: str
    page_count: int | None
    chunk_count: int | None
    embedding_model: str | None
    embedding_dimension: int | None
    vector_count: int | None
    status: str
    created_at: datetime
    updated_at: datetime
