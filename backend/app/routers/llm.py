from fastapi import APIRouter, Depends

from app.dependencies.services import get_llm_model_registry
from app.schemas.llm import LLMModelsResponse
from app.services.llm.model_registry import LLMModelRegistry


router = APIRouter(
    prefix="/api/v1/llm",
    tags=["LLM"],
)


@router.get("/models", response_model=LLMModelsResponse)
def list_models(
    model_registry: LLMModelRegistry = Depends(get_llm_model_registry),
):
    return {
        "default_model_id": model_registry.default_model_id,
        "models": model_registry.list_models(),
    }
