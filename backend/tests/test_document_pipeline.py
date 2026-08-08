from pathlib import Path

from app.services.document.pdf_service import PDFService
from app.services.document.chunker import DocumentChunker


def test_pdf_to_chunks():
    pdf_path = Path("tests/data/sample.pdf")

    document = PDFService.extract_document(pdf_path)

    assert document["page_count"] > 0
    assert len(document["pages"]) > 0

    chunker = DocumentChunker(
        chunk_size=800,
        chunk_overlap=120,
    )

    chunks = chunker.chunk_pages(
        document["pages"],
        source_filename=pdf_path.name,
    )

    assert len(chunks) > 0

    first_chunk = chunks[0]

    assert "text" in first_chunk
    assert "metadata" in first_chunk

    assert first_chunk["metadata"]["source"] == "sample.pdf"
    assert "page" in first_chunk["metadata"]
    assert "chunk_index" in first_chunk["metadata"]

    print(f"\nPages: {document['page_count']}")
    print(f"Chunks: {len(chunks)}")
    chunk_lengths = [
        len(chunk["text"])
        for chunk in chunks
    ]

    print(f"Min chunk length: {min(chunk_lengths)}")
    print(f"Max chunk length: {max(chunk_lengths)}")
    print(
        f"Average chunk length: "
        f"{sum(chunk_lengths) / len(chunk_lengths):.1f}"
    )
    print(f"First chunk:\n{first_chunk['text'][:500]}")