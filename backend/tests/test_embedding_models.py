import pytest

from app.services.vector.embedding_service import EmbeddingService


@pytest.mark.parametrize(
    "model_name",
    ["bge-small", "qwen-0.6b"],
)
def test_embedding_models(model_name):
    service = EmbeddingService(model_name=model_name)

    text = "The Transformer architecture uses self-attention."

    embedding = service.embed_document(text)

    assert isinstance(embedding, list)
    assert len(embedding) == service.dimension
    assert all(isinstance(value, float) for value in embedding)

@pytest.mark.parametrize(
    "model_name",
    ["bge-small", "qwen-0.6b"],
)
def test_query_and_document_embeddings(model_name):
    service = EmbeddingService(model_name=model_name)

    document = service.embed_document(
        "The Transformer architecture uses self-attention."
    )

    query = service.embed_query(
        "How does the Transformer use attention?"
    )

    assert len(document) == service.dimension
    assert len(query) == service.dimension
