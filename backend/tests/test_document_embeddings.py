from app.services.vector.embedding_service import EmbeddingService


def test_document_chunk_embeddings():

    chunks = [
        {
            "text": "The Transformer is a neural network architecture based entirely on attention mechanisms.",
            "metadata": {
                "source": "sample.pdf",
                "page": 1,
                "chunk_index": 0,
            },
        },
        {
            "text": "The Transformer architecture eliminates recurrence and convolutions and relies on self-attention.",
            "metadata": {
                "source": "sample.pdf",
                "page": 2,
                "chunk_index": 1,
            },
        },
        {
            "text": "The model achieves strong results on machine translation tasks while being more parallelizable.",
            "metadata": {
                "source": "sample.pdf",
                "page": 3,
                "chunk_index": 2,
            },
        },
    ]

    service = EmbeddingService("qwen-0.6b")

    texts = [chunk["text"] for chunk in chunks]

    embeddings = service.embed_documents(texts)

    assert len(embeddings) == len(chunks)

    for embedding in embeddings:
        assert len(embedding) == service.dimension
        assert all(isinstance(value, float) for value in embedding)