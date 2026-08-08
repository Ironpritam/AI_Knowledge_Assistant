from app.services.vector.embedding_service import EmbeddingService


def test_single_embedding():

    service = EmbeddingService()

    text = "The Transformer architecture uses self-attention."

    embedding = service.embed_text(text)

    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(value, float) for value in embedding)