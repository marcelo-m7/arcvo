from __future__ import annotations

import json
from dataclasses import asdict

from app.core.config import settings
from app.schemas.agents import AgentAssignmentCreate
from app.services.agent_runner import get_agent_runner
from app.services.agent_service import get_agent_service
from app.services.deploy_service import get_deploy_service
from app.services.odoo_service import get_odoo_service


class ArcvoDashboardTools:
    """Operational tools exposed to Hermes dashboard sessions."""

    @staticmethod
    def list_agents(state: str = "", limit: int = 50) -> str:
        service = get_agent_service()
        rows = service.list_agents(state=state or None)[:limit]
        return json.dumps([row.model_dump() for row in rows], ensure_ascii=False)

    @staticmethod
    def list_agent_audit(limit: int = 20) -> str:
        service = get_agent_service()
        rows = service.list_audit_logs(limit=limit)
        return json.dumps([row.model_dump() for row in rows], ensure_ascii=False)

    @staticmethod
    def assign_task(agent_id: int, task_id: int, notes: str = "") -> str:
        service = get_agent_service()
        result = service.assign_task(task_id, AgentAssignmentCreate(agent_id=agent_id, notes=notes))
        return json.dumps(result.model_dump(), ensure_ascii=False)

    @staticmethod
    async def run_pending(limit: int = 5) -> str:
        runner = get_agent_runner()
        rows = await runner.run_pending(limit=limit)
        return json.dumps([row.model_dump() for row in rows], ensure_ascii=False)

    @staticmethod
    async def run_agent(agent_id: int, limit: int = 1) -> str:
        runner = get_agent_runner()
        rows = await runner.run_agent(agent_id=agent_id, limit=limit)
        return json.dumps([row.model_dump() for row in rows], ensure_ascii=False)

    @staticmethod
    async def get_production_status() -> str:
        service = get_deploy_service()
        status = await service.status()
        return json.dumps(status.model_dump(), ensure_ascii=False)

    @staticmethod
    def get_odoo_health() -> str:
        service = get_odoo_service()
        health = service.health()
        return json.dumps(asdict(health), ensure_ascii=False)

    @staticmethod
    def system_context() -> str:
        return (
            "Arcvo ops dashboard. Use Odoo as source of truth with arcvo.* models. "
            f"Odoo URL: {settings.odoo_url}. DB: {settings.odoo_db}."
        )


__all__ = ["ArcvoDashboardTools"]
