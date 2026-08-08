from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):

    message: str

    original_filename: str

    stored_filename: str

    page_count: int

    text_length: int


    