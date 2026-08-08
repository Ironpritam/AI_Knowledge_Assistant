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
    page_count: int
    text_length: int
    chunk_count: int
    sample_chunks: list[DocumentChunk]