from app.services.llm.llm_service import LLMService


def test_ollama_provider():
    llm = LLMService(
        provider="ollama",
        model="qwen3:8b",
    )

    response = llm.generate(
        messages=[
            {
                "role": "user",
                "content": "Explain RAG in one sentence.",
            }
        ]
    )

    assert isinstance(response, str)
    assert len(response.strip()) > 0

    print("\nLLM response:")
    print(response)