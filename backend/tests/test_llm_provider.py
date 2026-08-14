import requests
import pytest
from fastapi import HTTPException

from app.services.llm.llm_service import LLMService


def test_ollama_provider_requests_longer_outputs(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"message": {"content": "Detailed answer"}}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr("requests.post", fake_post)

    llm = LLMService(
        provider="ollama",
        model="qwen3:8b",
    )

    llm.generate(
        messages=[
            {
                "role": "user",
                "content": "Explain RAG in one sentence.",
            }
        ]
    )

    assert captured["json"]["options"]["num_predict"] >= 512
    assert captured["json"]["options"]["temperature"] <= 0.5


def test_ollama_provider_handles_connection_errors(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Connection refused")

    monkeypatch.setattr("requests.post", fake_post)

    llm = LLMService(
        provider="ollama",
        model="qwen3:8b",
    )

    with pytest.raises(HTTPException) as exc:
        llm.generate(
            messages=[
                {
                    "role": "user",
                    "content": "Explain RAG in one sentence.",
                }
            ]
        )

    assert exc.value.status_code == 503
    assert "Ollama" in exc.value.detail


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