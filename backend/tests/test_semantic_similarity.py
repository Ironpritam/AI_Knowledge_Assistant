from sentence_transformers import util

from app.services.vector.embedding_service import EmbeddingService


def test_semantic_similarity():

    service = EmbeddingService()

    text_a = "The Transformer architecture uses self-attention."
    text_b = "Transformers rely on attention mechanisms."
    text_c = "The weather forecast predicts heavy rainfall."

    embeddings = service.embed_documents([text_a, text_b, text_c])

    similarity_ab = util.cos_sim(embeddings[0],embeddings[1],).item()

    similarity_ac = util.cos_sim(embeddings[0],embeddings[2],).item()

    print(f"\nSimilarity A-B: {similarity_ab:.4f}")
    print(f"Similarity A-C: {similarity_ac:.4f}")

    assert similarity_ab > similarity_ac