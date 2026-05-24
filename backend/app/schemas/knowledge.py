from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class KnowledgeCategory(BaseModel):
    id: int
    name: str
    complete_name: str | None = None
    active: bool = True
    article_count: int = 0


class KnowledgeCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    parent_id: int | None = None
    sequence: int = 10
    active: bool = True


class KnowledgeArticle(BaseModel):
    id: int
    article_ref: str | None = None
    name: str
    state: str
    category: tuple[int, str] | None = None
    owner_agent: tuple[int, str] | None = None
    task: tuple[int, str] | None = None
    version: int = 1
    published_at: datetime | None = None


class KnowledgeArticleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=220)
    summary: str | None = None
    content_html: str | None = None
    category_id: int | None = None
    owner_agent_id: int | None = None
    task_id: int | None = None
    tags: str | None = None
    related_ticket_ids: list[int] = Field(default_factory=list)


class KnowledgeArticleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=220)
    summary: str | None = None
    content_html: str | None = None
    category_id: int | None = None
    owner_agent_id: int | None = None
    task_id: int | None = None
    tags: str | None = None
    related_ticket_ids: list[int] | None = None


class KnowledgeArticleTransition(BaseModel):
    action: Literal["submit_review", "publish", "archive", "reset_draft"]
