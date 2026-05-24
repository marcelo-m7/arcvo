from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Arcvo API"
    app_env: str = "development"
    app_secret_key: str = Field(default="change-me-in-production", min_length=16)
    app_admin_password: str = Field(default="change-me-admin", min_length=8)
    app_jwt_expires_minutes: int = 720
    cors_origins: str = "http://localhost:8010,http://127.0.0.1:8010"

    odoo_url: str = "https://marcelo-m7.com"
    odoo_db: str = "odoo19"
    odoo_user: str = ""
    odoo_api_key: str = ""
    odoo_integration_mode: str = "xmlrpc"
    odoo_yolo: str = "read"
    odoo_allow_self_signed_ssl: bool = False
    supabase_project_id: str = "wvkjainfwsyiyfcmbtid"
    supabase_url: str = "https://wvkjainfwsyiyfcmbtid.supabase.co"
    supabase_publishable_key: str = ""

    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    ollama_uri: str = ""
    ollama_base_url: str = "https://api.ollama.monynha.me"
    ollama_model: str = "qwen2.5:1.5b"
    ollama_timeout_seconds: float = 90.0
    ollama_ui_senha: str = ""

    coolify_host: str = ""
    coolify_api_key: str = ""
    coolify_arcvo_webhook: str = ""

    hermes_dashboard_enabled: bool = False
    hermes_dashboard_host: str = "127.0.0.1"
    hermes_dashboard_port: int = 8010
    hermes_dashboard_internal_networks: str = "127.0.0.1/32,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
    hermes_provider: str = "gemini"
    hermes_model: str = "gemini-2.0-flash"

    agent_command_allowlist: str = (
        "git status,git branch,git rev-parse,make validate-arcvo-agents,"
        "make lint,make test,make odoo-health"
    )

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in {"dev", "development", "local"}

    @field_validator("ollama_timeout_seconds", mode="before")
    @classmethod
    def _normalize_ollama_timeout(cls, value: object) -> object:
        if value == "" or value is None:
            return 90.0
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def ollama_url(self) -> str:
        return (self.ollama_uri or self.ollama_base_url).rstrip("/")

    @property
    def allowed_agent_commands(self) -> list[str]:
        return [
            command.strip()
            for command in self.agent_command_allowlist.split(",")
            if command.strip()
        ]

    @property
    def dashboard_internal_network_list(self) -> list[str]:
        return [
            network.strip()
            for network in self.hermes_dashboard_internal_networks.split(",")
            if network.strip()
        ]

    @property
    def has_odoo_credentials(self) -> bool:
        return bool(self.odoo_url and self.odoo_db and self.odoo_user and self.odoo_api_key)

    @property
    def has_llm_configured(self) -> bool:
        return bool(self.gemini_api_key or self.openrouter_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
