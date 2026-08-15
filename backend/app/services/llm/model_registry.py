from dataclasses import dataclass
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.settings import Settings, settings
from app.repositories.llm_repository import LLMRepository
from app.services.llm.llm_service import LLMService


@dataclass(frozen=True)
class RegisteredModel:
    id: str
    label: str
    provider: str
    model: str
    enabled: bool
    is_default: bool = False


class LLMModelRegistry:
    def __init__(self, db: Session | None = None, app_settings: Settings = settings):
        self.db = db
        self.settings = app_settings
        self._models = self._build_models()

    def _build_models(self) -> dict[str, RegisteredModel]:
        models: dict[str, RegisteredModel] = {}

        # 1. Load from DB if session provided and records exist
        if self.db is not None:
            repo = LLMRepository(self.db)
            db_models = repo.get_all()
            if db_models:
                for record in db_models:
                    models[record.id] = RegisteredModel(
                        id=record.id,
                        label=record.label,
                        provider=record.provider,
                        model=record.model_name,
                        enabled=record.is_enabled,
                        is_default=record.is_default,
                    )
                return models

        # 2. Fallback to settings / environment configuration
        ollama_models = set(self._split_models(self.settings.OLLAMA_MODELS))
        if self.settings.LLM_PROVIDER == "ollama" and self.settings.LLM_MODEL:
            ollama_models.add(self.settings.LLM_MODEL.strip())

        for model in ollama_models:
            reg_id = f"ollama:{model}"
            models[reg_id] = RegisteredModel(
                id=reg_id,
                label=f"{model} (Local)",
                provider="ollama",
                model=model,
                enabled=True,
                is_default=(reg_id == self._get_configured_default_id()),
            )

        gemini_enabled = bool(self.settings.GEMINI_API_KEY or self.settings.GOOGLE_API_KEY)
        gemini_models = set(self._split_models(self.settings.GEMINI_MODELS))
        if self.settings.LLM_PROVIDER == "gemini" and self.settings.LLM_MODEL:
            gemini_models.add(self.settings.LLM_MODEL.strip())

        for model in gemini_models:
            reg_id = f"gemini:{model}"
            models[reg_id] = RegisteredModel(
                id=reg_id,
                label=f"{model} (Gemini)",
                provider="gemini",
                model=model,
                enabled=gemini_enabled,
                is_default=(reg_id == self._get_configured_default_id()),
            )

        return models

    def _get_configured_default_id(self) -> str:
        if self.settings.LLM_DEFAULT_MODEL_ID:
            return self.settings.LLM_DEFAULT_MODEL_ID
        return f"{self.settings.LLM_PROVIDER}:{self.settings.LLM_MODEL}"

    @staticmethod
    def _split_models(configured_models: str) -> list[str]:
        return [model.strip() for model in configured_models.split(",") if model.strip()]

    @property
    def default_model_id(self) -> str:
        for model in self._models.values():
            if model.is_default and model.enabled:
                return model.id
        return self._get_configured_default_id()

    def resolve(self, model_id: str | None = None, check_availability: bool = True) -> RegisteredModel:
        selected_model_id = model_id or self.default_model_id
        model = self._models.get(selected_model_id)

        if model is None:
            for registered in self._models.values():
                if registered.model == selected_model_id:
                    model = registered
                    break

        if model is None:
            raise HTTPException(status_code=400, detail="The requested model is not whitelisted.")
        if not model.enabled:
            raise HTTPException(status_code=503, detail="The requested model is not enabled.")

        if check_availability:
            available = LLMService(
                provider=model.provider,
                model=model.model,
            ).provider.is_available()
            if not available:
                raise HTTPException(
                    status_code=503,
                    detail=f"The requested model '{model.id}' is configured but not currently running or cannot be loaded.",
                )

        return model

    def get_status(self, model_id: str) -> dict:
        model = self._models.get(model_id)
        if model is None:
            for registered in self._models.values():
                if registered.model == model_id:
                    model = registered
                    break

        if model is None:
            raise HTTPException(status_code=404, detail="Model not found in whitelist.")

        available = model.enabled and LLMService(
            provider=model.provider,
            model=model.model,
        ).provider.is_available()

        return {
            "id": model.id,
            "provider": model.provider,
            "model": model.model,
            "enabled": model.enabled,
            "available": available,
        }

    def list_models(self) -> list[dict]:
        models = []
        default_id = self.default_model_id
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
                    "default": model.id == default_id,
                }
            )
        return models
