from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


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


class LLMModelStatusResponse(BaseModel):
    id: str
    provider: str
    model: str
    enabled: bool
    available: bool


class LLMModelCreateRequest(BaseModel):
    id: str = Field(..., example="ollama:llama3:8b")
    provider: str = Field(..., example="ollama")
    model_name: str = Field(..., example="llama3:8b")
    label: str = Field(..., example="Llama 3 8B (Local)")
    description: str | None = None
    is_enabled: bool = True
    is_default: bool = False


class LLMModelUpdateRequest(BaseModel):
    label: str | None = None
    description: str | None = None
    is_enabled: bool | None = None
    is_default: bool | None = None


class LLMAdminModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider: str
    model_name: str
    label: str
    description: str | None
    is_enabled: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
