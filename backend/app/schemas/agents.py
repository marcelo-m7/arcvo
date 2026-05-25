from typing import Any

from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    id: int
    name: str
    role: str
    state: str
    description: str | None = None
    is_agent: bool = True
    agent_active: bool = True
    capability_ids: list[int] = Field(default_factory=list)
    max_concurrent_tasks: int
    open_assignment_count: int
    completed_assignment_count: int
    success_rate: float
    is_available: bool
    last_heartbeat: str | None = None
    discuss_channel_id: list[Any] | int | bool | None = None


class AgentHeartbeat(BaseModel):
    state: str | None = Field(default=None, pattern="^(idle|busy|blocked|offline|disabled)$")
    message: str | None = None


class AgentHeartbeatResponse(BaseModel):
    agent_id: int
    status: str
    message: str


class AgentAssignmentCreate(BaseModel):
    agent_id: int
    notes: str | None = None


class AgentAssignmentResponse(BaseModel):
    assignment_id: int
    task_id: int
    agent_id: int
    status: str
    created: bool


class AgentAuditLog(BaseModel):
    id: int
    agent_id: list[Any] | int | bool | None = None
    task_id: list[Any] | int | bool | None = None
    assignment_id: list[Any] | int | bool | None = None
    action: str
    message: str | None = None
    payload: dict[str, Any] | None = None
    created_at: str | None = None


class AgentRunRequest(BaseModel):
    limit: int = Field(default=1, ge=1, le=10)


class AgentChatMessage(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class AgentChatResponse(BaseModel):
    agent_id: int
    agent_name: str
    role: str
    reply: str


class AgentMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    task_id: int | None = None
    assignment_id: int | None = None


class AgentMessageResponse(BaseModel):
    agent_id: int
    status: str
    message: str


class AgentDiscussMessage(BaseModel):
    id: int
    body: str | None = None
    date: str | None = None
    author_id: list[Any] | int | bool | None = None


class AgentExecution(BaseModel):
    assignment_id: int
    agent_id: int
    task_id: int
    status: str
    progress: int
    summary: str
    command: str | None = None
    command_allowed: bool | None = None
