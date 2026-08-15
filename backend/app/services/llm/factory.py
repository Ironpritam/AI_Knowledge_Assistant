import os
from typing import Any
from app.core.settings import settings
from app.services.llm.base import LLMProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openai_provider import OpenAICompatibleProvider


class ProviderFactory:
    _instances: dict[str, LLMProvider] = {}
    _ENDPOINT_MAP = {
        "openai": "https://api.openai.com/v1",
        "groq": "https://api.groq.com/openai/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "openrouter": "https://openrouter.ai/api/v1",
    }

    _KEY_ENV_MAP = {
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }

    @classmethod
    def create(cls, provider: str, model: str, **kwargs: Any) -> LLMProvider:
        provider_key = provider.lower()

        if provider_key == "ollama":
            base_url = kwargs.get("base_url") or settings.OLLAMA_BASE_URL
            return OllamaProvider(model=model, base_url=base_url)

        if provider_key == "gemini":
            api_key = kwargs.get("api_key") or settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
            return GeminiProvider(model=model, api_key=api_key)

        if provider_key in cls._ENDPOINT_MAP or provider_key == "openai_compatible":
            base_url = kwargs.get("base_url") or cls._ENDPOINT_MAP.get(provider_key, "https://api.openai.com/v1")
            env_var = cls._KEY_ENV_MAP.get(provider_key, "OPENAI_API_KEY")
            api_key = kwargs.get("api_key") or os.getenv(env_var, "")
            return OpenAICompatibleProvider(model=model, api_key=api_key, base_url=base_url)

        raise ValueError(f"Unsupported LLM provider: {provider}")

    @classmethod
    def get_or_create(cls, provider: str, model: str, **kwargs) -> LLMProvider:
        cache_key = f"{provider.lower()}:{model}"
        if cache_key not in cls._instances:
            cls._instances[cache_key] = cls.create(provider, model, **kwargs)
        return cls._instances[cache_key]
