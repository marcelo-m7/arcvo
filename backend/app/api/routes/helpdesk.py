from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import require_admin
from app.integrations.odoo.client import OdooClientError
from app.schemas.helpdesk import (
    HelpdeskComment,
    HelpdeskCommentCreate,
    HelpdeskTicket,
    HelpdeskTicketCreate,
    HelpdeskTicketTransition,
    HelpdeskTicketUpdate,
)
from app.services.helpdesk_service import HelpdeskService, get_helpdesk_service

router = APIRouter(dependencies=[Depends(require_admin)])
helpdesk_service_dependency = Depends(get_helpdesk_service)


@router.get("/tickets", response_model=list[HelpdeskTicket])
def list_tickets(
    state: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    service: HelpdeskService = helpdesk_service_dependency,
) -> list[HelpdeskTicket]:
    try:
        return service.list_tickets(state=state, limit=limit)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/tickets/{ticket_id}", response_model=HelpdeskTicket)
def get_ticket(
    ticket_id: int,
    service: HelpdeskService = helpdesk_service_dependency,
) -> HelpdeskTicket:
    try:
        ticket = service.get_ticket(ticket_id)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("/tickets", response_model=HelpdeskTicket)
def create_ticket(
    payload: HelpdeskTicketCreate,
    service: HelpdeskService = helpdesk_service_dependency,
) -> HelpdeskTicket:
    try:
        return service.create_ticket(payload)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.patch("/tickets/{ticket_id}", response_model=HelpdeskTicket)
def update_ticket(
    ticket_id: int,
    payload: HelpdeskTicketUpdate,
    service: HelpdeskService = helpdesk_service_dependency,
) -> HelpdeskTicket:
    try:
        return service.update_ticket(ticket_id, payload)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/tickets/{ticket_id}/transition", response_model=HelpdeskTicket)
def transition_ticket(
    ticket_id: int,
    payload: HelpdeskTicketTransition,
    service: HelpdeskService = helpdesk_service_dependency,
) -> HelpdeskTicket:
    try:
        return service.transition_ticket(ticket_id, payload)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/tickets/{ticket_id}/comments", response_model=list[HelpdeskComment])
def list_comments(
    ticket_id: int,
    limit: int = Query(default=100, ge=1, le=300),
    service: HelpdeskService = helpdesk_service_dependency,
) -> list[HelpdeskComment]:
    try:
        return service.list_comments(ticket_id=ticket_id, limit=limit)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/tickets/{ticket_id}/comments", response_model=HelpdeskComment)
def create_comment(
    ticket_id: int,
    payload: HelpdeskCommentCreate,
    service: HelpdeskService = helpdesk_service_dependency,
) -> HelpdeskComment:
    try:
        return service.create_comment(ticket_id=ticket_id, payload=payload)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
