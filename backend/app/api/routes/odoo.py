from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.integrations.odoo.client import OdooClientError
from app.schemas.odoo import OdooHealth, OdooRecordCreate, OdooRecordList, OdooRecordUpdate
from app.services.odoo_service import OdooService, get_odoo_service

router = APIRouter()
odoo_service_dependency = Depends(get_odoo_service)


@router.get("/health", response_model=OdooHealth)
def odoo_health(service: OdooService = odoo_service_dependency) -> OdooHealth:
    try:
        return service.health()
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/models/{model}/records", response_model=OdooRecordList)
def list_records(
    model: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: OdooService = odoo_service_dependency,
) -> OdooRecordList:
    try:
        return service.list_records(model=model, limit=limit, offset=offset)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/models/{model}/records")
def create_record(
    model: str,
    payload: OdooRecordCreate,
    service: OdooService = odoo_service_dependency,
) -> dict[str, Any]:
    try:
        record_id = service.create_record(model=model, values=payload.values)
        return {"id": record_id, "model": model}
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.patch("/models/{model}/records/{record_id}")
def update_record(
    model: str,
    record_id: int,
    payload: OdooRecordUpdate,
    service: OdooService = odoo_service_dependency,
) -> dict[str, Any]:
    try:
        updated = service.update_record(model=model, record_id=record_id, values=payload.values)
        return {"id": record_id, "model": model, "updated": updated}
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
