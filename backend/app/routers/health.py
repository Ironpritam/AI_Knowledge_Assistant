from datetime import datetime, timezone
import time
import logging
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.dependencies.database import get_db
from app.dependencies.services import (
    get_chroma_service,
    get_embedding_service,
    get_llm_model_registry,
)
from app.schemas.health import ComponentStatus, HealthResponse
from app.services.llm.model_registry import LLMModelRegistry
from app.services.vector.chroma_service import ChromaService
from app.services.vector.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Comprehensive Readiness Health Check",
    description="Actively verifies PostgreSQL, ChromaDB, Embedding models, and LLM Provider connectivity.",
)
@router.get(
    "/",
    response_model=HealthResponse,
    include_in_schema=False,
)
def health_check(
    response: Response,
    db: Session = Depends(get_db),
    chroma_service: ChromaService = Depends(get_chroma_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    model_registry: LLMModelRegistry = Depends(get_llm_model_registry),
):
    components: dict[str, ComponentStatus] = {}
    is_critical_healthy = True
    is_degraded = False

    # ----------------------------------------------------
    # 1. PostgreSQL Database Check
    # ----------------------------------------------------
    try:
        start_db = time.perf_counter()
        db.execute(text("SELECT 1"))
        latency_db = round((time.perf_counter() - start_db) * 1000, 2)
        components["database"] = ComponentStatus(
            status="healthy",
            latency_ms=latency_db,
            details={"engine": "PostgreSQL"},
        )
    except Exception as exc:
        logger.error(f"Health check failed for Database: {exc}")
        components["database"] = ComponentStatus(
            status="unhealthy",
            details={"error": str(exc)},
        )
        is_critical_healthy = False

    # ----------------------------------------------------
    # 2. ChromaDB (Vector Store) Check
    # ----------------------------------------------------
    try:
        start_chroma = time.perf_counter()
        heartbeat = chroma_service.client.heartbeat()
        latency_chroma = round((time.perf_counter() - start_chroma) * 1000, 2)
        components["vector_store"] = ComponentStatus(
            status="healthy",
            latency_ms=latency_chroma,
            details={"type": "ChromaDB", "heartbeat": heartbeat},
        )
    except Exception as exc:
        logger.error(f"Health check failed for ChromaDB: {exc}")
        components["vector_store"] = ComponentStatus(
            status="unhealthy",
            details={"error": str(exc)},
        )
        is_critical_healthy = False

    # ----------------------------------------------------
    # 3. Embedding Service Check
    # ----------------------------------------------------
    try:
        components["embedding_service"] = ComponentStatus(
            status="healthy",
            details={
                "model_key": embedding_service.model_key,
                "dimension": embedding_service.dimension,
            },
        )
    except Exception as exc:
        logger.error(f"Health check failed for EmbeddingService: {exc}")
        components["embedding_service"] = ComponentStatus(
            status="unhealthy",
            details={"error": str(exc)},
        )
        is_critical_healthy = False

    # ----------------------------------------------------
    # 4. Default LLM Provider Check
    # ----------------------------------------------------
    try:
        start_llm = time.perf_counter()
        default_model_id = model_registry.default_model_id
        model_status = model_registry.get_status(default_model_id)
        latency_llm = round((time.perf_counter() - start_llm) * 1000, 2)

        if model_status.get("available"):
            components["llm_provider"] = ComponentStatus(
                status="healthy",
                latency_ms=latency_llm,
                details={
                    "model_id": default_model_id,
                    "provider": model_status.get("provider"),
                    "available": True,
                },
            )
        else:
            components["llm_provider"] = ComponentStatus(
                status="degraded",
                latency_ms=latency_llm,
                details={
                    "model_id": default_model_id,
                    "provider": model_status.get("provider"),
                    "available": False,
                    "warning": "Default LLM model configured but not responding or currently reachable.",
                },
            )
            is_degraded = True
    except Exception as exc:
        logger.warning(f"Health check warning for LLM provider: {exc}")
        components["llm_provider"] = ComponentStatus(
            status="degraded",
            details={"error": str(exc)},
        )
        is_degraded = True

    # ----------------------------------------------------
    # Determine Overall System Status & HTTP Status Code
    # ----------------------------------------------------
    if not is_critical_healthy:
        overall_status = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif is_degraded:
        overall_status = "degraded"
        response.status_code = status.HTTP_200_OK
    else:
        overall_status = "healthy"
        response.status_code = status.HTTP_200_OK

    return HealthResponse(
        status=overall_status,
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        components=components,
    )


@router.get(
    "/live",
    summary="Liveness Probe",
    description="Lightweight liveness probe to verify that the application process is running.",
)
def liveness_probe():
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }