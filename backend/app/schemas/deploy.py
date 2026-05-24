from typing import Any

from pydantic import BaseModel


class SupportStatus(BaseModel):
    available: bool
    helpdesk_total: int | None = None
    helpdesk_open: int | None = None
    helpdesk_sla_breached: int | None = None
    knowledge_total: int | None = None
    knowledge_published: int | None = None
    error: str | None = None


class ProductionStatus(BaseModel):
    branch: str
    commit: str
    dirty: bool
    coolify_health: dict[str, Any]
    coolify_api: dict[str, Any]
    ollama_ok: bool
    ollama_health: dict[str, Any]
    support: SupportStatus


class CoolifyDeployResult(BaseModel):
    configured: bool
    triggered: bool
    status_code: int | None = None
    body: str | None = None
