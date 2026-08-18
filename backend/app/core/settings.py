from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Knowledge Assistant"
    APP_VERSION: str = "1.0.0"

    DEBUG: bool = True

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    DATABASE_URL: str
    
    GOOGLE_API_KEY: str | None = None

    # Embedding configuration
    EMBEDDING_MODEL: str = "nomic-v1.5"

    # LLM configuration
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "qwen3:8b"
    LLM_DEFAULT_MODEL_ID: str | None = None

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODELS: str = "qwen3:8b,deepseek-coder-v2:16b"

    GEMINI_API_KEY: str | None = None
    GEMINI_MODELS: str = ""

    # RAG configuration
    DEFAULT_COLLECTION: str = "documents"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
