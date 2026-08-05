from fastapi import FastAPI
from app.core.settings import settings
from app.routers.api import api_router
from app.core.lifespan import lifespan

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)
app.include_router(api_router)

@app.get("/")
def home():
    return {
        "message": "AI Knowledge Assistant Backend Running"
    }