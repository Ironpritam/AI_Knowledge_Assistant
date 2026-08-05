from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app):
    print("🚀 Starting AI Knowledge Assistant")
    yield
    print("🛑 Shutting down AI Knowledge Assistant")