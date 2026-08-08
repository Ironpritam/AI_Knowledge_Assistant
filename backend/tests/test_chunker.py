from app.services.document.chunker import DocumentChunker


def test_chunk_pages():
    pages = [
        {
            "page": 1,
            "text": (
                "This is a test document. "
                "It contains enough text to verify "
                "that our chunking service works correctly."
            ),
        }
    ]

    chunker = DocumentChunker(chunk_size=50,chunk_overlap=10,)
    chunks = chunker.chunk_pages(pages,"test.pdf",)

    assert len(chunks) > 0
    assert chunks[0]["metadata"]["source"] == "test.pdf"
    assert chunks[0]["metadata"]["page"] == 1