from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def test_dotenv_overrides_os_environment_for_embedding_model(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("EMBEDDING_MODEL=qwen-0.6b\n", encoding="utf-8")
    monkeypatch.setenv("EMBEDDING_MODEL", "bge-small")

    class Settings(BaseSettings):
        EMBEDDING_MODEL: str = "default"

        model_config = SettingsConfigDict(
            env_file=env_file,
            extra="ignore",
            case_sensitive=False,
        )

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls,
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                dotenv_settings,
                env_settings,
                file_secret_settings,
            )

    assert Settings().EMBEDDING_MODEL == "qwen-0.6b"
