from fastapi import APIRouter, Depends, HTTPException

from app.integrations.odoo.client import OdooClientError
from app.schemas.odoo import OdooHealth
from app.services.odoo_service import OdooService, get_odoo_service

router = APIRouter()
odoo_service_dependency = Depends(get_odoo_service)


@router.get("/health", response_model=OdooHealth)
def odoo_health(service: OdooService = odoo_service_dependency) -> OdooHealth:
    try:
        return service.health()
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
