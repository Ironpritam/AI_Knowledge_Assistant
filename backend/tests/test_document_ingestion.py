from pathlib import Path

from app.services.document.ingestion_service import (DocumentIngestionService,)
from app.services.vector.chroma_service import ChromaService
from app.services.vector.embedding_service import EmbeddingService


def test_real_document_ingestion():

    pdf_path = Path(
        "storage/documents/uploaded/sample.pdf"
    )

    embedding_service = EmbeddingService(model_name="bge-small")

    chroma_service = ChromaService()

    ingestion_service = DocumentIngestionService(
        embedding_service=embedding_service,
        chroma_service=chroma_service,
    )

    result = ingestion_service.ingest(pdf_path, collection_name="test_documents_bge",)

    print("\nIngestion result:")
    print(result)

    assert result["page_count"] == 15
    assert result["chunk_count"] > 0
    assert result["vector_count"] == result["chunk_count"]