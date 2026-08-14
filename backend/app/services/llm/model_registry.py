from dataclasses import dataclass

from fastapi import HTTPException

from app.core.settings import Settings, settings
from app.services.llm.llm_service import LLMService


@dataclass(frozen=True)
class RegisteredModel:
    id: str
    label: str
    provider: str
    model: str
    enabled: bool


class LLMModelRegistry:
    def __init__(self, app_settings: Settings = settings):
        self.settings = app_settings
        self._models = self._build_models()

    def _build_models(self) -> dict[str, RegisteredModel]:
        models: dict[str, RegisteredModel] = {}

        for model in self._split_models(self.settings.OLLAMA_MODELS):
            registered = RegisteredModel(
                id=f"ollama:{model}",
                label=f"{model} (Local)",
                provider="ollama",
                model=model,
                enabled=True,
            )
            models[registered.id] = registered

        gemini_enabled = bool(self.settings.GEMINI_API_KEY or self.settings.GOOGLE_API_KEY)
        for model in self._split_models(self.settings.GEMINI_MODELS):
            registered = RegisteredModel(
                id=f"gemini:{model}",
                label=f"{model} (Gemini)",
                provider="gemini",
                model=model,
                enabled=gemini_enabled,
            )
            models[registered.id] = registered

        return models

    @staticmethod
    def _split_models(configured_models: str) -> list[str]:
        return [model.strip() for model in configured_models.split(",") if model.strip()]

    @property
    def default_model_id(self) -> str:
        configured_default = self.settings.LLM_DEFAULT_MODEL_ID
        if configured_default:
            return configured_default
        return f"{self.settings.LLM_PROVIDER}:{self.settings.LLM_MODEL}"

    def resolve(self, model_id: str | None = None) -> RegisteredModel:
        selected_model_id = model_id or self.default_model_id
        model = self._models.get(selected_model_id)

        if model is None:
            raise HTTPException(status_code=400, detail="The requested model is not whitelisted.")
        if not model.enabled:
            raise HTTPException(status_code=503, detail="The requested model is not enabled.")

        return model

    def list_models(self) -> list[dict]:
        models = []
        for model in self._models.values():
            available = model.enabled and LLMService(
                provider=model.provider,
                model=model.model,
            ).provider.is_available()
            models.append(
                {
                    "id": model.id,
                    "label": model.label,
                    "provider": model.provider,
                    "enabled": model.enabled,
                    "available": available,
                    "default": model.id == self.default_model_id,
                }
            )
        return models
