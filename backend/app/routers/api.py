from fastapi import APIRouter

from app.routers.health import router as health_router
from app.routers.llm import router as llm_router
from app.routers.document import router as document_router
from app.routers.rag import router as rag_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(llm_router)
api_router.include_router(document_router)
api_router.include_router(rag_router)
