from app.services.llm.base import LLMProvider
from app.services.llm.ollama_provider import OllamaProvider


class LLMService:
    def __init__(self,provider: str = "ollama",model: str = "qwen3:8b",):
        self.provider_name = provider
        self.provider = self._create_provider(provider=provider,model=model,)

    def _create_provider(self,provider: str,model: str,) -> LLMProvider:
        if provider == "ollama":
            return OllamaProvider(model=model,)
        raise ValueError(f"Unsupported LLM provider: {provider}")

    def generate(self,messages: list[dict],) -> str:
        return self.provider.generate(messages)