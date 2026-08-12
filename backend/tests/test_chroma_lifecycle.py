from app.services.vector.chroma_service import ChromaService


def test_chroma_reuses_client():
    chroma = ChromaService()

    collection_a = chroma.get_collection(
        collection_name="lifecycle_test_a",
        embedding_model="bge-small",
        embedding_dimension=384,
    )

    collection_b = chroma.get_collection(
        collection_name="lifecycle_test_b",
        embedding_model="bge-small",
        embedding_dimension=384,
    )

    assert collection_a.name == "lifecycle_test_a"
    assert collection_b.name == "lifecycle_test_b"

    assert chroma.client is not None