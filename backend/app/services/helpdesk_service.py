from typing import Any

from app.core.config import settings
from app.integrations.odoo.client import OdooClient, OdooCredentials
from app.schemas.helpdesk import (
    HelpdeskComment,
    HelpdeskCommentCreate,
    HelpdeskTicket,
    HelpdeskTicketCreate,
    HelpdeskTicketTransition,
    HelpdeskTicketUpdate,
)

TICKET_MODEL = "arcvo.helpdesk.ticket"
COMMENT_MODEL = "arcvo.helpdesk.comment"


class HelpdeskService:
    def __init__(self, client: OdooClient) -> None:
        self.client = client

    def list_tickets(self, state: str | None = None, limit: int = 100) -> list[HelpdeskTicket]:
        domain = [["state", "=", state]] if state else []
        records = self.client.search_read(
            TICKET_MODEL,
            domain=domain,
            fields=self._ticket_fields(),
            limit=limit,
            offset=0,
        )
        return [self._ticket_from_record(record) for record in records]

    def get_ticket(self, ticket_id: int) -> HelpdeskTicket | None:
        rows = self.client.search_read(
            TICKET_MODEL,
            domain=[["id", "=", ticket_id]],
            fields=self._ticket_fields(),
            limit=1,
        )
        return self._ticket_from_record(rows[0]) if rows else None

    def create_ticket(self, payload: HelpdeskTicketCreate) -> HelpdeskTicket:
        values: dict[str, Any] = {
            "name": payload.name,
            "description": payload.description or "",
            "priority": payload.priority,
        }
        if payload.requester_partner_id:
            values["requester_partner_id"] = payload.requester_partner_id
        if payload.assignee_agent_id:
            values["assignee_agent_id"] = payload.assignee_agent_id
        if payload.task_id:
            values["task_id"] = payload.task_id
        if payload.assignment_id:
            values["assignment_id"] = payload.assignment_id
        if payload.sla_deadline:
            values["sla_deadline"] = payload.sla_deadline.strftime("%Y-%m-%d %H:%M:%S")
        if payload.knowledge_article_ids:
            values["knowledge_article_ids"] = [(6, 0, payload.knowledge_article_ids)]

        ticket_id = self.client.create(TICKET_MODEL, values)
        return self.get_ticket(ticket_id)  # type: ignore[return-value]

    def update_ticket(self, ticket_id: int, payload: HelpdeskTicketUpdate) -> HelpdeskTicket:
        values: dict[str, Any] = {}
        for field in (
            "name",
            "description",
            "priority",
            "requester_partner_id",
            "assignee_agent_id",
            "task_id",
            "assignment_id",
            "stage_id",
        ):
            value = getattr(payload, field)
            if value is not None:
                values[field] = value

        if payload.sla_deadline is not None:
            values["sla_deadline"] = payload.sla_deadline.strftime("%Y-%m-%d %H:%M:%S")
        if payload.knowledge_article_ids is not None:
            values["knowledge_article_ids"] = [(6, 0, payload.knowledge_article_ids)]

        if values:
            self.client.write(TICKET_MODEL, ticket_id, values)
        return self.get_ticket(ticket_id)  # type: ignore[return-value]

    def transition_ticket(
        self,
        ticket_id: int,
        payload: HelpdeskTicketTransition,
    ) -> HelpdeskTicket:
        method_map = {
            "set_in_progress": "action_set_in_progress",
            "set_blocked": "action_set_blocked",
            "set_resolved": "action_set_resolved",
            "set_closed": "action_set_closed",
            "reopen": "action_reopen",
            "record_first_response": "action_record_first_response",
            "assign_agent": "action_assign_agent",
        }
        method = method_map[payload.action]
        kwargs: dict[str, Any] = {}
        if payload.action == "assign_agent" and payload.note:
            kwargs["note"] = payload.note
        self.client.execute_kw(TICKET_MODEL, method, [[ticket_id]], kwargs)
        return self.get_ticket(ticket_id)  # type: ignore[return-value]

    def list_comments(self, ticket_id: int, limit: int = 100) -> list[HelpdeskComment]:
        records = self.client.search_read(
            COMMENT_MODEL,
            domain=[["ticket_id", "=", ticket_id]],
            fields=["id", "ticket_id", "author_id", "comment_type", "body", "created_at"],
            limit=limit,
            offset=0,
        )
        comments: list[HelpdeskComment] = []
        for record in records:
            comments.append(
                HelpdeskComment(
                    id=record["id"],
                    ticket_id=self._many2one_id(record.get("ticket_id")),
                    author_id=self._many2one_tuple(record.get("author_id")),
                    comment_type=record.get("comment_type") or "note",
                    body=record.get("body") or "",
                    created_at=record.get("created_at") or None,
                )
            )
        return comments

    def create_comment(self, ticket_id: int, payload: HelpdeskCommentCreate) -> HelpdeskComment:
        comment_id = self.client.create(
            COMMENT_MODEL,
            {
                "ticket_id": ticket_id,
                "comment_type": payload.comment_type,
                "body": payload.body,
            },
        )
        rows = self.client.search_read(
            COMMENT_MODEL,
            domain=[["id", "=", comment_id]],
            fields=["id", "ticket_id", "author_id", "comment_type", "body", "created_at"],
            limit=1,
        )
        row = rows[0]
        return HelpdeskComment(
            id=row["id"],
            ticket_id=self._many2one_id(row.get("ticket_id")),
            author_id=self._many2one_tuple(row.get("author_id")),
            comment_type=row.get("comment_type") or "note",
            body=row.get("body") or "",
            created_at=row.get("created_at") or None,
        )

    @staticmethod
    def _ticket_fields() -> list[str]:
        return [
            "id",
            "ticket_ref",
            "name",
            "stage_id",
            "state",
            "priority",
            "requester_partner_id",
            "assignee_agent_id",
            "task_id",
            "assignment_id",
            "sla_deadline",
            "sla_breached",
            "response_time_hours",
            "resolution_time_hours",
        ]

    @staticmethod
    def _many2one_tuple(value: Any) -> tuple[int, str] | None:
        if isinstance(value, list) and len(value) == 2:
            return int(value[0]), str(value[1])
        return None

    @staticmethod
    def _many2one_id(value: Any) -> int:
        if isinstance(value, list) and value:
            return int(value[0])
        return int(value or 0)

    def _ticket_from_record(self, record: dict[str, Any]) -> HelpdeskTicket:
        return HelpdeskTicket(
            id=record["id"],
            ticket_ref=record.get("ticket_ref") or None,
            name=record["name"],
            stage=self._many2one_tuple(record.get("stage_id")),
            state=record.get("state") or None,
            priority=record.get("priority") or "1",
            requester_partner=self._many2one_tuple(record.get("requester_partner_id")),
            assignee_agent=self._many2one_tuple(record.get("assignee_agent_id")),
            task=self._many2one_tuple(record.get("task_id")),
            assignment=self._many2one_tuple(record.get("assignment_id")),
            sla_deadline=record.get("sla_deadline") or None,
            sla_breached=bool(record.get("sla_breached")),
            response_time_hours=float(record.get("response_time_hours") or 0.0),
            resolution_time_hours=float(record.get("resolution_time_hours") or 0.0),
        )


def get_helpdesk_service() -> HelpdeskService:
    credentials = OdooCredentials(
        url=settings.odoo_url,
        database=settings.odoo_db,
        username=settings.odoo_user,
        api_key=settings.odoo_api_key,
        allow_self_signed_ssl=settings.odoo_allow_self_signed_ssl,
    )
    return HelpdeskService(OdooClient(credentials))
