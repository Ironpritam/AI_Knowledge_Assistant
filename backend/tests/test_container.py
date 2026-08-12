from app.core.container import ApplicationContainer


def test_application_container():
    container = ApplicationContainer()

    assert container.embedding_service is not None
    assert container.llm_service is not None
    assert container.rag_service is not None

    result = container.rag_service.ask(
        question="Why did the authors propose the Transformer architecture?",
        top_k=5,
    )

    assert result["answer"]

    print("\n" + "=" * 80)
    print("ANSWER")
    print("=" * 80)

    print(result["answer"])