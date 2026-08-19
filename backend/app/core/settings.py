from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Knowledge Assistant"
    APP_VERSION: str = "1.0.0"

    DEBUG: bool = True

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value):
        """Accept common deployment labels from Windows/process environments."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "production", "prod", "off", "no"}:
                return False
            if normalized in {"debug", "development", "dev", "on", "yes"}:
                return True
        return value

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
    LLM_MAX_OUTPUT_TOKENS: int = 1024

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODELS: str = "qwen3:8b,deepseek-coder-v2:16b"

    GEMINI_API_KEY: str | None = None
    GEMINI_MODELS: str = ""

    # RAG configuration
    DEFAULT_COLLECTION: str = "documents"
    RAG_COVERAGE_MAX_OUTPUT_TOKENS: int = 1536
    RAG_COVERAGE_MIN_TOKENS_PER_DOCUMENT: int = 180
    RAG_COVERAGE_TEXT_CHARS_FOR_MAX_OUTPUT: int = 24000

    # Chat session configuration
    CHAT_SESSION_TTL_HOURS: int = 72
    CHAT_HISTORY_MAX_TURNS: int = 4
    CHAT_HISTORY_MAX_CHARS: int = 12000
    CHAT_SESSION_PAGE_SIZE: int = 50
    CHAT_MESSAGE_PAGE_SIZE: int = 100
    CHAT_PRUNE_INTERVAL_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
