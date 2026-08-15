import logging
import shutil
from pathlib import Path
from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.services import get_chroma_service, get_ingestion_service
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentMetadataResponse, DocumentUploadResponse
from app.services.document.ingestion_service import DocumentIngestionService
from app.services.vector.chroma_service import ChromaService

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)

UPLOAD_DIR = Path("storage/documents/uploaded")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf"}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = Query("test_all_0.0.0.0"),
    ingestion_service: DocumentIngestionService = Depends(get_ingestion_service),
    db: Session = Depends(get_db),
):
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

    document = Document(
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=str(destination),
        collection_name=collection_name,
        status="processing",
    )
    repository = DocumentRepository(db)
    document = repository.create(document)

    try:
        result = ingestion_service.ingest(
            pdf_path=destination,
            collection_name=collection_name,
            document_id=str(document.id),
            source_filename=file.filename,
        )
    except Exception:
        try:
            ingestion_service.chroma_service.delete_document_chunks(
                collection_name=collection_name,
                document_id=str(document.id),
            )
        except Exception:
            logger.exception(
                "Failed to remove partially indexed vectors for document %s.",
                document.id,
            )

        destination.unlink(missing_ok=True)
        document.status = "failed"
        repository.update(document)
        raise

    document.page_count = result["page_count"]
    document.chunk_count = result["chunk_count"]
    document.embedding_model = result["embedding_model"]
    document.embedding_dimension = result["embedding_dimension"]
    document.vector_count = result["vector_count"]
    document.status = "processed"
    document = repository.update(document)

    return {
        "message": "Document uploaded and indexed successfully",
        "document_id": str(document.id),
        "original_filename": file.filename,
        "stored_filename": stored_filename,
        "collection_name": collection_name,
        "status": document.status,
        **result,
    }


@router.get("", response_model=list[DocumentMetadataResponse])
def list_documents(db: Session = Depends(get_db)):
    return DocumentRepository(db).get_all()


@router.get("/{document_id}", response_model=DocumentMetadataResponse)
def get_document(document_id: UUID, db: Session = Depends(get_db)):
    document = DocumentRepository(db).get_by_id(document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    return document


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    chroma_service: ChromaService = Depends(get_chroma_service),
):
    repository = DocumentRepository(db)
    document = repository.get_by_id(document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    previous_status = document.status
    document.status = "deleting"
    repository.update(document)

    try:
        if previous_status == "processed":
            # Verify chunks exist before attempting deletion
            chunk_count = chroma_service.get_document_chunks_count(
                collection_name=document.collection_name,
                document_id=str(document.id),
            )
            
            if chunk_count == 0:
                logger.warning(
                    f"No chunks found for document {document.id} in collection {document.collection_name}. "
                    f"Document may have already been deleted or was never indexed."
                )
            
            # Delete from vector database
            chroma_service.delete_document_chunks(
                collection_name=document.collection_name,
                document_id=str(document.id),
            )

        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()

        repository.delete(document)
    except Exception as exc:
        document.status = "deletion_failed"
        repository.update(document)
        raise HTTPException(
            status_code=500,
            detail="Document deletion could not be completed.",
        ) from exc

    return Response(status_code=204)
