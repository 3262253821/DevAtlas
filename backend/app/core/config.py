from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    database_url: str = ""
    jwt_secret_key: str = ""

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"

    chroma_persist_dir: Path = PROJECT_ROOT / "others" / "chroma"
    upload_dir: Path = PROJECT_ROOT / "others" / "uploads"
    embedding_model: str = "BAAI/bge-small-zh-v1.5"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def missing_required(self) -> list[str]:
        required_settings = {
            "database_url": self.database_url,
            "jwt_secret_key": self.jwt_secret_key,
            "deepseek_api_key": self.deepseek_api_key,
        }

        return [
            name
            for name, value in required_settings.items()
            if not value.strip()
        ]

    def require(self, *names: str) -> None:
        missing_names = []

        for name in names:
            value = getattr(self, name, "")

            if not isinstance(value, str) or not value.strip():
                missing_names.append(name)

        if missing_names:
            raise RuntimeError(
                "Missing required settings: "
                + ", ".join(missing_names)
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()