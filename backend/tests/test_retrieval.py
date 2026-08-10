from app.services.vector.retrieval_service import (RetrievalService,)


def test_real_semantic_retrieval():
    service = RetrievalService(
        embedding_model="qwen-0.6b",
        collection_name="test_ingestion_qwen",
    )

    results = service.search(
        query=(
            "Why did the authors propose "
            "the Transformer architecture?"
        ),
        top_k=5,
    )

    assert len(results) == 5

    for result in results:
        assert result["text"]
        assert result["metadata"]

    print("\nTop retrieved chunks:")

    for index, result in enumerate(results, start=1):
        print(
            f"\n#{index}"
            f" | Page: {result['metadata']['page']}"
            f" | Chunk: {result['metadata']['chunk_index']}"
            f" | Distance: {result['distance']:.4f}"
        )

        print(result["text"][:300])