from typing import Any
from pydantic import BaseModel, Field


class ComponentStatus(BaseModel):
    status: str = Field(..., description="Component status: healthy, degraded, or unhealthy")
    latency_ms: float | None = Field(default=None, description="Response latency in milliseconds")
    details: dict[str, Any] | None = Field(default=None, description="Additional component metadata")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall system health: healthy, degraded, or unhealthy")
    service: str
    version: str
    timestamp: str
    components: dict[str, ComponentStatus]
