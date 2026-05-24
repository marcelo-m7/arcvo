from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.services.agent_runner import get_agent_runner
from app.services.agent_service import get_agent_service
from app.services.deploy_service import get_deploy_service
from app.services.odoo_service import get_odoo_service


class DashboardService:
    async def overview(self) -> dict[str, Any]:
        agent_service = get_agent_service()
        runner = get_agent_runner()
        deploy_service = get_deploy_service()
        odoo_service = get_odoo_service()

        agents = agent_service.list_agents()
        audit = agent_service.list_audit_logs(limit=10)
        executions = runner.list_executions(limit=10)
        deploy = await deploy_service.status()
        odoo_health = odoo_service.health()

        return {
            "agents": {
                "total": len(agents),
                "available": sum(1 for item in agents if item.is_available),
                "open_assignments": sum(item.open_assignment_count for item in agents),
                "rows": [item.model_dump() for item in agents],
            },
            "audit": [item.model_dump() for item in audit],
            "executions": executions,
            "deploy": deploy.model_dump(),
            "odoo": asdict(odoo_health),
        }


def get_dashboard_service() -> DashboardService:
    return DashboardService()
