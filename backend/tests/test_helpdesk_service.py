from typing import Any

from app.schemas.helpdesk import HelpdeskTicketCreate, HelpdeskTicketTransition
from app.services.helpdesk_service import HelpdeskService


class FakeOdooClient:
    def __init__(self) -> None:
        self.created: list[tuple[str, dict[str, Any]]] = []
        self.writes: list[tuple[str, int, dict[str, Any]]] = []
        self.exec_calls: list[tuple[str, str, list[Any], dict[str, Any]]] = []

    def search_read(
        self,
        model: str,
        domain: list[Any] | None = None,
        fields: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if model == "arcvo.helpdesk.ticket":
            return [
                {
                    "id": 11,
                    "ticket_ref": "TKT-00011",
                    "name": "Pipeline failed",
                    "stage_id": [1, "In Progress"],
                    "state": "in_progress",
                    "priority": "2",
                    "requester_partner_id": [10, "Marcelo"],
                    "assignee_agent_id": [7, "Backend Operator"],
                    "task_id": [55, "Fix prod"],
                    "assignment_id": [9, "A-9"],
                    "sla_deadline": False,
                    "sla_breached": False,
                    "response_time_hours": 2.0,
                    "resolution_time_hours": 0.0,
                }
            ]
        if model == "arcvo.helpdesk.comment":
            return [
                {
                    "id": 1,
                    "ticket_id": [11, "TKT-00011"],
                    "author_id": [2, "Admin"],
                    "comment_type": "note",
                    "body": "ok",
                    "created_at": False,
                }
            ]
        return []

    def create(self, model: str, values: dict[str, Any]) -> int:
        self.created.append((model, values))
        return 11

    def write(self, model: str, record_id: int, values: dict[str, Any]) -> bool:
        self.writes.append((model, record_id, values))
        return True

    def execute_kw(
        self,
        model: str,
        method: str,
        args: list[Any],
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        self.exec_calls.append((model, method, args, kwargs or {}))
        return True


def test_create_ticket_writes_expected_model_values() -> None:
    client = FakeOdooClient()
    service = HelpdeskService(client)  # type: ignore[arg-type]

    ticket = service.create_ticket(
        HelpdeskTicketCreate(name="Pipeline failed", task_id=55, assignee_agent_id=7)
    )

    assert ticket.id == 11
    assert client.created[0][0] == "arcvo.helpdesk.ticket"
    assert client.created[0][1]["name"] == "Pipeline failed"


def test_transition_ticket_calls_odoo_domain_method() -> None:
    client = FakeOdooClient()
    service = HelpdeskService(client)  # type: ignore[arg-type]

    service.transition_ticket(
        11,
        HelpdeskTicketTransition(action="assign_agent", note="sync now"),
    )

    assert client.exec_calls
    model, method, args, kwargs = client.exec_calls[0]
    assert model == "arcvo.helpdesk.ticket"
    assert method == "action_assign_agent"
    assert args == [[11]]
    assert kwargs["note"] == "sync now"
