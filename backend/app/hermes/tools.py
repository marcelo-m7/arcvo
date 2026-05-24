from __future__ import annotations

import json

from app.core.config import settings
from app.schemas.agents import AgentAssignmentCreate, AgentMessageCreate
from app.services.agent_runner import get_agent_runner
from app.services.agent_service import get_agent_service
from app.services.deploy_service import get_deploy_service
from app.services.odoo_service import get_odoo_service


class ArcvoHermesTools:
    """Small Odoo-backed tools exposed to Hermes sessions."""

    @staticmethod
    def system_context() -> str:
        return (
            "Arcvo uses Odoo as the single source of truth for agents, tasks, "
            "Discuss messages, chatter, audit, and deploy status. "
            f"Odoo URL: {settings.odoo_url}. DB: {settings.odoo_db}."
        )

    @staticmethod
    def list_agents(state: str = "", limit: int = 50) -> str:
        service = get_agent_service()
        rows = service.list_agents(state=state or None)[:limit]
        return json.dumps([row.model_dump() for row in rows], ensure_ascii=False)

    @staticmethod
    def list_agent_audit(
        agent_id: int | None = None,
        task_id: int | None = None,
        limit: int = 20,
    ) -> str:
        service = get_agent_service()
        rows = service.list_audit_logs(agent_id=agent_id, task_id=task_id, limit=limit)
        return json.dumps([row.model_dump() for row in rows], ensure_ascii=False)

    @staticmethod
    def assign_task(agent_id: int, task_id: int, notes: str = "") -> str:
        service = get_agent_service()
        result = service.assign_task(task_id, AgentAssignmentCreate(agent_id=agent_id, notes=notes))
        return json.dumps(result.model_dump(), ensure_ascii=False)

    @staticmethod
    def send_agent_message(
        agent_id: int,
        body: str,
        task_id: int | None = None,
        assignment_id: int | None = None,
    ) -> str:
        service = get_agent_service()
        result = service.send_agent_message(
            agent_id,
            AgentMessageCreate(body=body, task_id=task_id, assignment_id=assignment_id),
        )
        return json.dumps(result.model_dump(), ensure_ascii=False)

    @staticmethod
    def list_agent_messages(agent_id: int, limit: int = 20) -> str:
        service = get_agent_service()
        rows = service.list_agent_messages(agent_id=agent_id, limit=limit)
        return json.dumps([row.model_dump() for row in rows], ensure_ascii=False)

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
        return json.dumps(health.model_dump(), ensure_ascii=False)


__all__ = ["ArcvoHermesTools"]

