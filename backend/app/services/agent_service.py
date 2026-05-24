from app.core.config import settings
from app.integrations.odoo.client import OdooClient, OdooCredentials
from app.schemas.agents import (
    AgentAssignmentCreate,
    AgentAssignmentResponse,
    AgentAuditLog,
    AgentDiscussMessage,
    AgentHeartbeat,
    AgentHeartbeatResponse,
    AgentInfo,
    AgentMessageCreate,
    AgentMessageResponse,
)

AGENT_MODEL = "arcvo.agent"
ASSIGNMENT_MODEL = "arcvo.agent.assignment"
AUDIT_MODEL = "arcvo.agent.audit.log"
TASK_MODEL = "project.task"
MAIL_MESSAGE_MODEL = "mail.message"


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
        self.client.execute_kw(
            AGENT_MODEL,
            "action_heartbeat",
            [[agent_id]],
            {"state": payload.state, "message": payload.message},
        )

        return AgentHeartbeatResponse(
            agent_id=agent_id,
            status="ok",
            message="Heartbeat recorded",
        )

    def send_agent_message(
        self,
        agent_id: int,
        payload: AgentMessageCreate,
    ) -> AgentMessageResponse:
        self.client.execute_kw(
            AGENT_MODEL,
            "action_post_discuss_message",
            [[agent_id]],
            {
                "body": payload.body,
                "task_id": payload.task_id,
                "assignment_id": payload.assignment_id,
            },
        )
        return AgentMessageResponse(
            agent_id=agent_id,
            status="ok",
            message="Message posted to agent Discuss channel",
        )

    def list_agent_messages(self, agent_id: int, limit: int = 20) -> list[AgentDiscussMessage]:
        agent = self._read_agent_record(agent_id, fields=["id", "discuss_channel_id"])
        if not agent:
            return []

        channel_id = self._many2one_id(agent.get("discuss_channel_id"))
        if not channel_id:
            self.client.execute_kw(AGENT_MODEL, "action_ensure_discuss_channel", [[agent_id]], {})
            agent = self._read_agent_record(agent_id, fields=["id", "discuss_channel_id"])
            channel_id = self._many2one_id(agent.get("discuss_channel_id")) if agent else None
        if not channel_id:
            return []

        records = self.client.search_read(
            MAIL_MESSAGE_MODEL,
            domain=[
                ["model", "=", "discuss.channel"],
                ["res_id", "=", channel_id],
                ["message_type", "=", "comment"],
            ],
            fields=["id", "body", "date", "author_id"],
            limit=limit,
        )
        return [AgentDiscussMessage(**record) for record in records]

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
                "created_at",
            ],
            limit=limit,
        )
        return [AgentAuditLog(**{**record, "payload": None}) for record in records]

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
            "discuss_channel_id",
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
            discuss_channel_id=record.get("discuss_channel_id") or None,
        )

    def _read_agent_record(self, agent_id: int, fields: list[str]) -> dict | None:
        records = self.client.search_read(
            AGENT_MODEL,
            domain=[["id", "=", agent_id]],
            fields=fields,
            limit=1,
        )
        return records[0] if records else None

    @staticmethod
    def _many2one_id(value: object) -> int | None:
        if isinstance(value, list) and value:
            return int(value[0])
        if isinstance(value, int):
            return value
        return None


def get_agent_service() -> AgentService:
    credentials = OdooCredentials(
        url=settings.odoo_url,
        database=settings.odoo_db,
        username=settings.odoo_user,
        api_key=settings.odoo_api_key,
        allow_self_signed_ssl=settings.odoo_allow_self_signed_ssl,
    )
    return AgentService(OdooClient(credentials))
