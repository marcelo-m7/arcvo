from typing import Any

from pydantic import BaseModel


class ProductionStatus(BaseModel):
    branch: str
    commit: str
    dirty: bool
    coolify_health: dict[str, Any]
    coolify_api: dict[str, Any]
    ollama_ok: bool
    ollama_health: dict[str, Any]


class CoolifyDeployResult(BaseModel):
    configured: bool
    triggered: bool
    status_code: int | None = None
    body: str | None = None
