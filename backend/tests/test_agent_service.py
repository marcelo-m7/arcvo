from typing import Any

from app.schemas.agents import AgentAssignmentCreate, AgentHeartbeat
from app.services.agent_service import AgentService


class FakeOdooClient:
    def __init__(self) -> None:
        self.created: list[tuple[str, dict[str, Any]]] = []
        self.writes: list[tuple[str, int, dict[str, Any]]] = []
        self.search_results: list[int] = []

    def search_read(
        self,
        model: str,
        domain: list[Any] | None = None,
        fields: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if model == "arcvo.agent":
            return [
                {
                    "id": 7,
                    "name": "odoo_agent",
                    "role": "odoo",
                    "state": "idle",
                    "description": "Odoo specialist",
                    "capability_ids": [1, 2],
                    "max_concurrent_tasks": 3,
                    "open_assignment_count": 0,
                    "completed_assignment_count": 4,
                    "success_rate": 100.0,
                    "is_available": True,
                    "last_heartbeat": False,
                }
            ]
        return []

    def search(
        self,
        model: str,
        domain: list[Any] | None = None,
        limit: int | None = None,
    ) -> list[int]:
        return self.search_results

    def create(self, model: str, values: dict[str, Any]) -> int:
        self.created.append((model, values))
        return len(self.created)

    def write(self, model: str, record_id: int, values: dict[str, Any]) -> bool:
        self.writes.append((model, record_id, values))
        return True


def test_list_agents_reads_arcvo_agent_model() -> None:
    service = AgentService(FakeOdooClient())  # type: ignore[arg-type]

    agents = service.list_agents()

    assert agents[0].id == 7
    assert agents[0].role == "odoo"
    assert agents[0].capability_ids == [1, 2]


def test_record_heartbeat_writes_agent_and_audit_log() -> None:
    client = FakeOdooClient()
    service = AgentService(client)  # type: ignore[arg-type]

    response = service.record_heartbeat(7, AgentHeartbeat(state="idle", message="ok"))

    assert response.status == "ok"
    assert client.writes[0][0] == "arcvo.agent"
    assert client.created[0][0] == "arcvo.agent.audit.log"
    assert client.created[0][1]["action"] == "heartbeat"


def test_assign_task_is_idempotent_for_open_assignment() -> None:
    client = FakeOdooClient()
    client.search_results = [42]
    service = AgentService(client)  # type: ignore[arg-type]

    response = service.assign_task(99, AgentAssignmentCreate(agent_id=7, notes="go"))

    assert response.assignment_id == 42
    assert response.created is False
    assert (
        "project.task",
        99,
        {"arcvo_agent_id": 7, "arcvo_requires_agent": True},
    ) in client.writes
    assert all(model != "arcvo.agent.assignment" for model, _values in client.created)
