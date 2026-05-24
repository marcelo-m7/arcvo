from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import require_admin
from app.integrations.odoo.client import OdooClientError
from app.schemas.agents import (
    AgentAssignmentCreate,
    AgentAssignmentResponse,
    AgentAuditLog,
    AgentExecution,
    AgentHeartbeat,
    AgentHeartbeatResponse,
    AgentInfo,
    AgentRunRequest,
)
from app.services.agent_runner import AgentRunner, get_agent_runner
from app.services.agent_service import AgentService, get_agent_service

router = APIRouter(dependencies=[Depends(require_admin)])
agent_service_dependency = Depends(get_agent_service)
agent_runner_dependency = Depends(get_agent_runner)


@router.get("", response_model=list[AgentInfo])
def list_agents(
    state: str | None = Query(default=None),
    service: AgentService = agent_service_dependency,
) -> list[AgentInfo]:
    try:
        return service.list_agents(state=state)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/audit", response_model=list[AgentAuditLog])
def list_audit_logs(
    agent_id: int | None = Query(default=None),
    task_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    service: AgentService = agent_service_dependency,
) -> list[AgentAuditLog]:
    try:
        return service.list_audit_logs(agent_id=agent_id, task_id=task_id, limit=limit)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/run-pending", response_model=list[AgentExecution])
async def run_pending_agents(
    payload: AgentRunRequest,
    runner: AgentRunner = agent_runner_dependency,
) -> list[AgentExecution]:
    try:
        return await runner.run_pending(limit=payload.limit)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/executions", response_model=list[AgentAuditLog])
def list_executions(
    limit: int = Query(default=50, ge=1, le=200),
    runner: AgentRunner = agent_runner_dependency,
) -> list[AgentAuditLog]:
    try:
        return [AgentAuditLog(**record) for record in runner.list_executions(limit=limit)]
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{agent_id}", response_model=AgentInfo)
def get_agent(
    agent_id: int,
    service: AgentService = agent_service_dependency,
) -> AgentInfo:
    try:
        agent = service.get_agent(agent_id)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/{agent_id}/heartbeat", response_model=AgentHeartbeatResponse)
def record_heartbeat(
    agent_id: int,
    payload: AgentHeartbeat,
    service: AgentService = agent_service_dependency,
) -> AgentHeartbeatResponse:
    try:
        return service.record_heartbeat(agent_id=agent_id, payload=payload)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/{agent_id}/run", response_model=list[AgentExecution])
async def run_agent(
    agent_id: int,
    payload: AgentRunRequest,
    runner: AgentRunner = agent_runner_dependency,
) -> list[AgentExecution]:
    try:
        return await runner.run_agent(agent_id=agent_id, limit=payload.limit)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/assign", response_model=AgentAssignmentResponse)
def assign_task(
    task_id: int,
    payload: AgentAssignmentCreate,
    service: AgentService = agent_service_dependency,
) -> AgentAssignmentResponse:
    try:
        return service.assign_task(task_id=task_id, payload=payload)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
