from fastapi import APIRouter

# router = APIRouter(prefix="/health", tags=["Health"])
router = APIRouter(prefix="/api/v1/health", tags=["Health"])


@router.get("/")
def health_check():
    return {
        "status": "healthy",
        "message": "AI Knowledge Assistant API is running"
    }