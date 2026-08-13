from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    source: str
    page: int
    chunk_index: int


class DocumentChunk(BaseModel):
    text: str
    metadata: ChunkMetadata


class DocumentUploadResponse(BaseModel):
    message: str
    original_filename: str
    stored_filename: str
    collection_name: str

    page_count: int
    chunk_count: int

    embedding_model: str
    embedding_dimension: int
    vector_count: int