from pathlib import Path
import shutil
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)

UPLOAD_DIR = Path("storage/documents/uploaded")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf"}


@router.post("/upload")
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

    return {
        "message": "Document uploaded successfully",
        "original_filename": file.filename,
        "stored_filename": stored_filename,
        "content_type": file.content_type,
    }