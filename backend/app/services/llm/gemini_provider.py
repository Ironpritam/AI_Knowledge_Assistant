from fastapi import HTTPException
from google import genai
from google.genai import types

from app.services.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    def generate(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
    ) -> str:
        prompt = "\n\n".join(
            f"{message['role'].upper()}: {message['content']}"
            for message in messages
        )

        try:
            generation_config = (
                types.GenerateContentConfig(max_output_tokens=max_tokens)
                if max_tokens is not None
                else None
            )
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=generation_config,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="Gemini LLM service is unavailable or rejected the request.",
            ) from exc

        if not response.text:
            raise HTTPException(
                status_code=502,
                detail="Gemini returned an empty response.",
            )

        return response.text

    def is_available(self) -> bool:
        return bool(self.api_key)
