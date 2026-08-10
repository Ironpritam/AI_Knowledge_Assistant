from app.services.vector.chroma_service import ChromaService


def test_chroma_add_and_search():
    service = ChromaService(collection_name="test_collection")

    chunks = [
        {
            "text": "The Transformer architecture uses self-attention.",
            "metadata": {
                "source": "test.pdf",
                "page": 1,
                "chunk_index": 0,
            },
        },
        {
            "text": "The Transformer eliminates recurrence and relies on attention.",
            "metadata": {
                "source": "test.pdf",
                "page": 2,
                "chunk_index": 1,
            },
        },
        {
            "text": "The weather forecast predicts heavy rainfall.",
            "metadata": {
                "source": "test.pdf",
                "page": 3,
                "chunk_index": 2,
            },
        },
    ]

    embeddings = [
        [1.0, 0.0, 0.0],
        [0.9, 0.1, 0.0],
        [0.0, 0.0, 1.0],
    ]

    service.add_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    results = service.search(
        query_embedding=[1.0, 0.0, 0.0],
        top_k=2,
    )

    assert len(results["documents"][0]) == 2
    assert results["documents"][0][0] == chunks[0]["text"]