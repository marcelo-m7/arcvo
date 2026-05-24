from datetime import UTC, datetime

from app.core.config import settings
from app.integrations.odoo.client import OdooClient, OdooCredentials
from app.schemas.agents import (
    AgentAssignmentCreate,
    AgentAssignmentResponse,
    AgentAuditLog,
    AgentHeartbeat,
    AgentHeartbeatResponse,
    AgentInfo,
)

AGENT_MODEL = "arcvo.agent"
ASSIGNMENT_MODEL = "arcvo.agent.assignment"
AUDIT_MODEL = "arcvo.agent.audit.log"
TASK_MODEL = "project.task"


class AgentService:
    def __init__(self, client: OdooClient) -> None:
        self.client = client

    def list_agents(self, state: str | None = None) -> list[AgentInfo]:
        domain = [["state", "=", state]] if state else []
        records = self.client.search_read(
            AGENT_MODEL,
            domain=domain,
            fields=self._agent_fields(),
            limit=200,
        )
        return [self._agent_from_record(record) for record in records]

    def get_agent(self, agent_id: int) -> AgentInfo | None:
        records = self.client.search_read(
            AGENT_MODEL,
            domain=[["id", "=", agent_id]],
            fields=self._agent_fields(),
            limit=1,
        )
        return self._agent_from_record(records[0]) if records else None

    def record_heartbeat(self, agent_id: int, payload: AgentHeartbeat) -> AgentHeartbeatResponse:
        values = {"last_heartbeat": self._odoo_now()}
        if payload.state:
            values["state"] = payload.state
        self.client.write(AGENT_MODEL, agent_id, values)
        self.client.create(
            AUDIT_MODEL,
            {
                "agent_id": agent_id,
                "action": "heartbeat",
                "message": payload.message or "Heartbeat recorded from Arcvo API.",
            },
        )
        return AgentHeartbeatResponse(
            agent_id=agent_id,
            status="ok",
            message="Heartbeat recorded",
        )

    def assign_task(
        self,
        task_id: int,
        payload: AgentAssignmentCreate,
    ) -> AgentAssignmentResponse:
        existing = self.client.search(
            ASSIGNMENT_MODEL,
            domain=[
                ["agent_id", "=", payload.agent_id],
                ["task_id", "=", task_id],
                ["status", "in", ["assigned", "in_progress", "blocked"]],
            ],
            limit=1,
        )
        if existing:
            assignment_id = existing[0]
            created = False
        else:
            assignment_id = self.client.create(
                ASSIGNMENT_MODEL,
                {
                    "agent_id": payload.agent_id,
                    "task_id": task_id,
                    "status": "assigned",
                    "notes": payload.notes or "",
                },
            )
            created = True

        self.client.write(
            TASK_MODEL,
            task_id,
            {
                "arcvo_agent_id": payload.agent_id,
                "arcvo_requires_agent": True,
            },
        )
        self.client.create(
            AUDIT_MODEL,
            {
                "agent_id": payload.agent_id,
                "task_id": task_id,
                "assignment_id": assignment_id,
                "action": "assigned",
                "message": "Task assigned through Arcvo API.",
                "payload": {"created": created},
            },
        )
        return AgentAssignmentResponse(
            assignment_id=assignment_id,
            task_id=task_id,
            agent_id=payload.agent_id,
            status="assigned",
            created=created,
        )

    def list_audit_logs(
        self,
        agent_id: int | None = None,
        task_id: int | None = None,
        limit: int = 50,
    ) -> list[AgentAuditLog]:
        domain = []
        if agent_id is not None:
            domain.append(["agent_id", "=", agent_id])
        if task_id is not None:
            domain.append(["task_id", "=", task_id])
        records = self.client.search_read(
            AUDIT_MODEL,
            domain=domain,
            fields=[
                "id",
                "agent_id",
                "task_id",
                "assignment_id",
                "action",
                "message",
                "payload",
                "created_at",
            ],
            limit=limit,
        )
        return [AgentAuditLog(**record) for record in records]

    @staticmethod
    def _agent_fields() -> list[str]:
        return [
            "id",
            "name",
            "role",
            "state",
            "description",
            "capability_ids",
            "max_concurrent_tasks",
            "open_assignment_count",
            "completed_assignment_count",
            "success_rate",
            "is_available",
            "last_heartbeat",
        ]

    @staticmethod
    def _agent_from_record(record: dict) -> AgentInfo:
        return AgentInfo(
            id=record["id"],
            name=record["name"],
            role=record["role"],
            state=record["state"],
            description=record.get("description") or None,
            capability_ids=record.get("capability_ids") or [],
            max_concurrent_tasks=record["max_concurrent_tasks"],
            open_assignment_count=record["open_assignment_count"],
            completed_assignment_count=record["completed_assignment_count"],
            success_rate=record["success_rate"],
            is_available=record["is_available"],
            last_heartbeat=record.get("last_heartbeat") or None,
        )

    @staticmethod
    def _odoo_now() -> str:
        return datetime.now(UTC).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")


def get_agent_service() -> AgentService:
    credentials = OdooCredentials(
        url=settings.odoo_url,
        database=settings.odoo_db,
        username=settings.odoo_user,
        api_key=settings.odoo_api_key,
        allow_self_signed_ssl=settings.odoo_allow_self_signed_ssl,
    )
    return AgentService(OdooClient(credentials))
