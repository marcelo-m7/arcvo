from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HelpdeskComment(BaseModel):
    id: int
    ticket_id: int
    author_id: tuple[int, str] | None = None
    comment_type: str
    body: str
    created_at: datetime | None = None


class HelpdeskCommentCreate(BaseModel):
    body: str = Field(min_length=1)
    comment_type: Literal["note", "public", "internal", "system"] = "note"


class HelpdeskTicket(BaseModel):
    id: int
    ticket_ref: str | None = None
    name: str
    stage: tuple[int, str] | None = None
    state: str | None = None
    priority: str
    requester_partner: tuple[int, str] | None = None
    assignee_agent: tuple[int, str] | None = None
    task: tuple[int, str] | None = None
    assignment: tuple[int, str] | None = None
    sla_deadline: datetime | None = None
    sla_breached: bool = False
    response_time_hours: float = 0.0
    resolution_time_hours: float = 0.0


class HelpdeskTicketCreate(BaseModel):
    name: str = Field(min_length=2, max_length=220)
    description: str | None = None
    priority: Literal["0", "1", "2", "3"] = "1"
    requester_partner_id: int | None = None
    assignee_agent_id: int | None = None
    task_id: int | None = None
    assignment_id: int | None = None
    sla_deadline: datetime | None = None
    knowledge_article_ids: list[int] = Field(default_factory=list)


class HelpdeskTicketUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=220)
    description: str | None = None
    priority: Literal["0", "1", "2", "3"] | None = None
    requester_partner_id: int | None = None
    assignee_agent_id: int | None = None
    task_id: int | None = None
    assignment_id: int | None = None
    stage_id: int | None = None
    sla_deadline: datetime | None = None
    knowledge_article_ids: list[int] | None = None


class HelpdeskTicketTransition(BaseModel):
    action: Literal[
        "set_in_progress",
        "set_blocked",
        "set_resolved",
        "set_closed",
        "reopen",
        "record_first_response",
        "assign_agent",
    ]
    note: str | None = None
