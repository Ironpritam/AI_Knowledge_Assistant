from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI Knowledge Assistant"
    APP_VERSION: str = "1.0.0"

    DEBUG: bool = True

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    DATABASE_URL: str

    GOOGLE_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()