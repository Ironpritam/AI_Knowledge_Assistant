from pathlib import Path

from app.services.document.ingestion_service import (
    DocumentIngestionService,
)


def test_real_document_ingestion():

    pdf_path = Path(
        "storage/documents/uploaded/sample.pdf"
    )

    service = DocumentIngestionService(
        embedding_model="bge-small",
        collection_name="test_ingestion_bge",
    )

    result = service.ingest(pdf_path)

    print("\nIngestion result:")
    print(result)

    assert result["page_count"] == 15
    assert result["chunk_count"] > 0
    assert result["vector_count"] == result["chunk_count"]