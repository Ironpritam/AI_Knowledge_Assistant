from fastapi import APIRouter
from datetime import datetime
from app.core.settings import settings


# router = APIRouter(prefix="/health", tags=["Health"])
router = APIRouter(prefix="/api/v1/health", tags=["Health"])


@router.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Knowledge Assistant",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(datetime.timezone.utc).isoformat()
    }