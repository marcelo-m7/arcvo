from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Odoo FastAPI Template"
    app_env: str = "development"
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    odoo_url: str = "http://localhost:8069"
    odoo_db: str = ""
    odoo_user: str = ""
    odoo_api_key: str = ""
    odoo_allow_self_signed_ssl: bool = False

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in {"dev", "development", "local"}

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _normalize_cors_origins(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value)

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def has_odoo_credentials(self) -> bool:
        return bool(self.odoo_url and self.odoo_db and self.odoo_user and self.odoo_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
