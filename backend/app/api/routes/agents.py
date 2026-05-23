"""Agent management and task routing APIs."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.integrations.odoo.client import OdooClient, OdooClientError
from app.services.odoo_service import get_odoo_service

router = APIRouter()


class AgentInfo(BaseModel):
    """Agent information."""

    id: int
    name: str
    agent_type: str
    status: str
    capabilities: list[str]
    current_workload: int
    max_concurrent_tasks: int
    is_available: bool
    last_heartbeat: str | None = None


class AgentHeartbeatRequest(BaseModel):
    """Agent heartbeat (keep-alive) request."""

    agent_id: int = Field(..., description="ID of agent sending heartbeat")
    status: str = Field(default="available", description="Current status")


class TaskAssignmentRequest(BaseModel):
    """Request to assign task to agent."""

    agent_id: int = Field(..., description="Agent ID to claim task")
    task_id: int = Field(..., description="Task ID to claim")


class TaskProgressReport(BaseModel):
    """Agent reports task progress."""

    agent_id: int
    task_id: int
    progress_percentage: int = Field(ge=0, le=100)
    notes: str | None = None
    log_entry: str | None = None


class TaskCompletionReport(BaseModel):
    """Agent completes a task."""

    agent_id: int
    task_id: int
    result: dict[str, Any] | None = None
    logs: str | None = None
    actual_hours: float | None = None


# Dependency
def get_odoo_client() -> OdooClient:
    """Get authenticated Odoo client."""
    from app.core.config import get_settings

    sett = get_settings()
    from app.integrations.odoo.client import OdooCredentials

    credentials = OdooCredentials(
        url=sett.odoo_url,
        database=sett.odoo_db,
        username=sett.odoo_user,
        api_key=sett.odoo_api_key,
        allow_self_signed_ssl=sett.odoo_allow_self_signed_ssl,
    )
    client = OdooClient(credentials)
    client.authenticate()
    return client


@router.get("/agents", response_model=list[AgentInfo])
def list_agents(
    status: str | None = Query(None, description="Filter by status"),
    client: OdooClient = Depends(get_odoo_client),
) -> list[AgentInfo]:
    """List all agents in the registry."""
    try:
        domain = []
        if status:
            domain.append(["status", "=", status])

        agents = client.search_read(
            "agent.agent",
            domain=domain,
            fields=[
                "id",
                "name",
                "agent_type",
                "status",
                "current_workload",
                "max_concurrent_tasks",
                "is_available",
                "last_heartbeat",
                "capabilities_ids",
            ],
            limit=100,
        )

        return [
            AgentInfo(
                id=agent["id"],
                name=agent["name"],
                agent_type=agent["agent_type"],
                status=agent["status"],
                capabilities=agent.get("capabilities_ids", []),
                current_workload=agent["current_workload"],
                max_concurrent_tasks=agent["max_concurrent_tasks"],
                is_available=agent["is_available"],
                last_heartbeat=agent.get("last_heartbeat"),
            )
            for agent in agents
        ]
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/agents/{agent_id}")
def get_agent(
    agent_id: int,
    client: OdooClient = Depends(get_odoo_client),
) -> dict[str, Any]:
    """Get specific agent details."""
    try:
        agent = client.search_read(
            "agent.agent",
            domain=[["id", "=", agent_id]],
            fields=[
                "id",
                "name",
                "agent_type",
                "status",
                "current_workload",
                "max_concurrent_tasks",
                "is_available",
                "last_heartbeat",
                "capabilities_ids",
            ],
            limit=1,
        )
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent[0]
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/agents/heartbeat")
def agent_heartbeat(
    payload: AgentHeartbeatRequest,
    client: OdooClient = Depends(get_odoo_client),
) -> dict[str, Any]:
    """Agent sends keep-alive heartbeat."""
    try:
        # Update agent's last_heartbeat and status
        client.write(
            "agent.agent",
            payload.agent_id,
            {
                "last_heartbeat": __import__("datetime").datetime.now().isoformat(),
                "status": payload.status,
            },
        )

        # Log audit entry
        client.create(
            "agent.audit_log",
            {
                "agent_id": payload.agent_id,
                "action_type": "heartbeat",
                "status_code": 200,
            },
        )

        return {"status": "ok", "message": "Heartbeat recorded"}
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/tasks/me/pending")
def get_pending_tasks(
    agent_id: int = Query(..., description="Agent ID"),
    client: OdooClient = Depends(get_odoo_client),
) -> list[dict[str, Any]]:
    """Get pending tasks for an agent based on their capabilities."""
    try:
        # Get agent capabilities
        agent = client.search_read(
            "agent.agent",
            domain=[["id", "=", agent_id]],
            fields=["capabilities_ids"],
        )
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # TODO: Query project.task with matching required_capabilities
        # For now, return empty list (requires project addon extension)
        return []
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/claim")
def claim_task(
    task_id: int,
    payload: TaskAssignmentRequest,
    client: OdooClient = Depends(get_odoo_client),
) -> dict[str, Any]:
    """Agent claims a task."""
    try:
        # Create assignment record
        assignment_id = client.create(
            "agent.assignment",
            {
                "agent_id": payload.agent_id,
                "task_id": task_id,
                "status": "claimed",
            },
        )

        # Log audit
        client.create(
            "agent.audit_log",
            {
                "agent_id": payload.agent_id,
                "task_id": task_id,
                "action_type": "claimed",
                "status_code": 200,
            },
        )

        # Increment agent workload
        agent = client.search_read(
            "agent.agent",
            domain=[["id", "=", payload.agent_id]],
            fields=["current_workload"],
        )[0]
        client.write(
            "agent.agent",
            payload.agent_id,
            {"current_workload": agent["current_workload"] + 1},
        )

        return {
            "assignment_id": assignment_id,
            "task_id": task_id,
            "message": "Task claimed successfully",
        }
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/report")
def report_progress(
    task_id: int,
    payload: TaskProgressReport,
    client: OdooClient = Depends(get_odoo_client),
) -> dict[str, Any]:
    """Agent reports task progress."""
    try:
        # Update assignment progress
        assignments = client.search(
            "agent.assignment",
            [["agent_id", "=", payload.agent_id], ["task_id", "=", task_id]],
        )
        if assignments:
            client.write(
                "agent.assignment",
                assignments[0],
                {
                    "progress_percentage": payload.progress_percentage,
                    "status": "in_progress",
                    "notes": payload.notes or "",
                },
            )

        # Log audit
        client.create(
            "agent.audit_log",
            {
                "agent_id": payload.agent_id,
                "task_id": task_id,
                "action_type": "progress",
                "action_details": {
                    "progress": payload.progress_percentage,
                    "notes": payload.notes,
                },
                "status_code": 200,
            },
        )

        return {"message": "Progress reported", "progress": payload.progress_percentage}
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: int,
    payload: TaskCompletionReport,
    client: OdooClient = Depends(get_odoo_client),
) -> dict[str, Any]:
    """Agent marks task as complete."""
    try:
        # Update assignment
        assignments = client.search(
            "agent.assignment",
            [["agent_id", "=", payload.agent_id], ["task_id", "=", task_id]],
        )
        if assignments:
            client.write(
                "agent.assignment",
                assignments[0],
                {
                    "status": "completed",
                    "progress_percentage": 100,
                    "completed_at": __import__(
                        "datetime"
                    ).datetime.now().isoformat(),
                    "actual_hours": payload.actual_hours or 0,
                },
            )

        # Log audit
        client.create(
            "agent.audit_log",
            {
                "agent_id": payload.agent_id,
                "task_id": task_id,
                "action_type": "completed",
                "action_details": payload.result or {},
                "status_code": 200,
            },
        )

        # Decrement workload
        agent = client.search_read(
            "agent.agent",
            domain=[["id", "=", payload.agent_id]],
            fields=["current_workload"],
        )[0]
        client.write(
            "agent.agent",
            payload.agent_id,
            {"current_workload": max(0, agent["current_workload"] - 1)},
        )

        return {
            "task_id": task_id,
            "message": "Task completed successfully",
            "result": payload.result,
        }
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/audit/{agent_id}")
def get_agent_audit_log(
    agent_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    client: OdooClient = Depends(get_odoo_client),
) -> list[dict[str, Any]]:
    """Get audit log for an agent."""
    try:
        logs = client.search_read(
            "agent.audit_log",
            domain=[["agent_id", "=", agent_id]],
            fields=[
                "id",
                "action_type",
                "task_id",
                "timestamp",
                "status_code",
                "error_msg",
                "action_details",
            ],
            limit=limit,
            offset=0,
        )
        return logs
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
