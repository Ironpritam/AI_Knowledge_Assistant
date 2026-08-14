from pydantic import BaseModel


class LLMModelResponse(BaseModel):
    id: str
    label: str
    provider: str
    enabled: bool
    available: bool
    default: bool


class LLMModelsResponse(BaseModel):
    default_model_id: str
    models: list[LLMModelResponse]
