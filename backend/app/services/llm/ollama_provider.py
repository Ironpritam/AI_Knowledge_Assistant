import requests
from fastapi import HTTPException

from app.services.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self,model: str = "qwen3:8b",base_url: str = "http://localhost:11434",):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self,messages: list[dict],) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_predict": 512,
                        "temperature": 0.2,
                        "top_p": 0.9,
                    },
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Ollama LLM service is unavailable at {self.base_url}. Please ensure Ollama is running and the model '{self.model}' is available.",
            ) from exc

        if "message" not in data or "content" not in data["message"]:
            raise HTTPException(
                status_code=502,
                detail="Ollama returned an unexpected response payload.",
            )

        return data["message"]["content"]

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get("models", [])
        except requests.exceptions.RequestException:
            return False

        return any(
            model.get("name") == self.model or model.get("model") == self.model
            for model in models
        )
