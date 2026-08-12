import requests

from app.services.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self,model: str = "qwen3:8b",base_url: str = "http://localhost:11434",):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self,messages: list[dict],) -> str:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]