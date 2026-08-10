from pathlib import Path

from app.services.document.ingestion_service import (DocumentIngestionService,)


def test_qwen_ingestion():

    pdf_path = Path("storage/documents/uploaded/sample.pdf")

    service = DocumentIngestionService(
        embedding_model="qwen-0.6b",
        collection_name="test_ingestion_qwen",
    )

    result = service.ingest(pdf_path)

    print("\nQwen ingestion result:")
    print(result)

    assert result["embedding_model"] == "qwen-0.6b"
    assert result["embedding_dimension"] == 1024
    assert result["chunk_count"] > 0
    assert result["vector_count"] > 0