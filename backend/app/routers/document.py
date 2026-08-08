from pathlib import Path
import shutil
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.document.pdf_service import PDFService
from app.schemas.document import DocumentUploadResponse
from app.services.document.chunker import DocumentChunker


router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)

UPLOAD_DIR = Path("storage/documents/uploaded")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf"}


@router.post("/upload",response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    stored_filename = f"{uuid4()}{extension}"
    destination = UPLOAD_DIR / stored_filename

    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    pdf_data = PDFService.extract_document(destination)
    # with open("text_data.txt", "w", encoding="utf-8") as text_file:
    #     text_file.write(pdf_data["text"])

    chunker = DocumentChunker()
    chunks = chunker.chunk_pages(
        pages=pdf_data["pages"],
        source_filename=file.filename,
    )

    return {
        "message": "Document uploaded successfully",
        "original_filename": file.filename,
        "stored_filename": stored_filename,
        "page_count": pdf_data["page_count"],
        "text_length": sum(
            len(page["text"])
            for page in pdf_data["pages"]
        ),
        "chunk_count": len(chunks),
        "sample_chunks": chunks[:3],
    }