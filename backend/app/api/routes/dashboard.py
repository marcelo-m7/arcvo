from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.internal_access import require_internal_request
from app.integrations.odoo.client import OdooClientError
from app.services.dashboard_service import DashboardService, get_dashboard_service

router = APIRouter(dependencies=[Depends(require_internal_request)])
dashboard_service_dependency = Depends(get_dashboard_service)


@router.get("/status")
def dashboard_status() -> dict[str, object]:
    return {
        "enabled": settings.hermes_dashboard_enabled,
        "host": settings.hermes_dashboard_host,
        "port": settings.hermes_dashboard_port,
        "provider": settings.hermes_provider,
        "model": settings.hermes_model,
        "internal_networks": settings.dashboard_internal_network_list,
        "start_command": "uv run python -m scripts.run_hermes_dashboard",
    }


@router.get("/overview")
async def dashboard_overview(
    service: DashboardService = dashboard_service_dependency,
) -> dict[str, object]:
    try:
        return await service.overview()
    except OdooClientError as exc:
        return {
            "error": "odoo_unavailable",
            "detail": str(exc),
        }
