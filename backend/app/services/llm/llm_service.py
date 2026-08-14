from app.services.llm.base import LLMProvider
from app.core.settings import settings
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.ollama_provider import OllamaProvider


class LLMService:
    def __init__(self,provider: str = "ollama",model: str = "qwen3:8b",):
        self.provider_name = provider
        self.provider = self._create_provider(provider=provider,model=model,)

    def _create_provider(self,provider: str,model: str,) -> LLMProvider:
        if provider == "ollama":
            return OllamaProvider(model=model, base_url=settings.OLLAMA_BASE_URL)
        if provider == "gemini":
            api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
            if not api_key:
                raise ValueError("GEMINI_API_KEY must be configured to use Gemini.")
            return GeminiProvider(model=model, api_key=api_key)
        raise ValueError(f"Unsupported LLM provider: {provider}")

    def generate(self,messages: list[dict],) -> str:
        return self.provider.generate(messages)
