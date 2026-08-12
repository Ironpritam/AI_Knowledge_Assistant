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
    EMBEDDING_MODEL: str = "bge-small"

    # LLM configuration
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "qwen3:8b"

    # RAG configuration
    DEFAULT_COLLECTION: str = "documents"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()