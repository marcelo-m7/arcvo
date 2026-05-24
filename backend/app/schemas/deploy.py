from typing import Any

from pydantic import BaseModel


class OperationsStatus(BaseModel):
    available: bool
    agents_total: int | None = None
    agents_available: int | None = None
    assignments_open: int | None = None
    assignments_blocked: int | None = None
    tasks_requiring_agent: int | None = None
    audit_total: int | None = None
    error: str | None = None


class ProductionStatus(BaseModel):
    branch: str
    commit: str
    dirty: bool
    coolify_health: dict[str, Any]
    coolify_api: dict[str, Any]
    ollama_ok: bool
    ollama_health: dict[str, Any]
    operations: OperationsStatus


class CoolifyDeployResult(BaseModel):
    configured: bool
    triggered: bool
    status_code: int | None = None
    body: str | None = None
