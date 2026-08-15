import requests
from fastapi import HTTPException

from app.services.llm.base import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    """Universal provider supporting any OpenAI-compatible /v1/chat/completions API."""

    def __init__(self,
        model: str,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 60,
    ):
        self.model = model
        self.api_key = api_key or ""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, messages: list[dict]) -> str:
        if not self.api_key and "localhost" not in self.base_url and "127.0.0.1" not in self.base_url:
            raise HTTPException(status_code=503, detail=f"API key missing for provider at {self.base_url}.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as exc:
            detail = f"LLM API request failed at {self.base_url}: {exc}"
            if exc.response is not None:
                detail = f"LLM API returned {exc.response.status_code}: {exc.response.text}"
            raise HTTPException(status_code=503, detail=detail) from exc

    def is_available(self) -> bool:
        if not self.api_key and "localhost" not in self.base_url and "127.0.0.1" not in self.base_url:
            return False

        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            # Standard OpenAI /v1/models endpoint check
            res = requests.get(f"{self.base_url}/models", headers=headers, timeout=5)
            return res.status_code == 200
        except Exception:
            return False
