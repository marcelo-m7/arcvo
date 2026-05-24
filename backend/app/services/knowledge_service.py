from typing import Any

from app.core.config import settings
from app.integrations.odoo.client import OdooClient, OdooCredentials
from app.schemas.knowledge import (
    KnowledgeArticle,
    KnowledgeArticleCreate,
    KnowledgeArticleTransition,
    KnowledgeArticleUpdate,
    KnowledgeCategory,
    KnowledgeCategoryCreate,
)

ARTICLE_MODEL = "arcvo.knowledge.article"
CATEGORY_MODEL = "arcvo.knowledge.category"


class KnowledgeService:
    def __init__(self, client: OdooClient) -> None:
        self.client = client

    def list_categories(self, limit: int = 100) -> list[KnowledgeCategory]:
        rows = self.client.search_read(
            CATEGORY_MODEL,
            fields=["id", "name", "complete_name", "active", "article_count"],
            limit=limit,
            offset=0,
        )
        return [
            KnowledgeCategory(
                id=row["id"],
                name=row["name"],
                complete_name=row.get("complete_name") or None,
                active=bool(row.get("active", True)),
                article_count=int(row.get("article_count") or 0),
            )
            for row in rows
        ]

    def create_category(self, payload: KnowledgeCategoryCreate) -> KnowledgeCategory:
        category_id = self.client.create(
            CATEGORY_MODEL,
            {
                "name": payload.name,
                "description": payload.description or "",
                "parent_id": payload.parent_id or False,
                "sequence": payload.sequence,
                "active": payload.active,
            },
        )
        row = self.client.search_read(
            CATEGORY_MODEL,
            domain=[["id", "=", category_id]],
            fields=["id", "name", "complete_name", "active", "article_count"],
            limit=1,
        )[0]
        return KnowledgeCategory(
            id=row["id"],
            name=row["name"],
            complete_name=row.get("complete_name") or None,
            active=bool(row.get("active", True)),
            article_count=int(row.get("article_count") or 0),
        )

    def list_articles(self, state: str | None = None, limit: int = 100) -> list[KnowledgeArticle]:
        domain = [["state", "=", state]] if state else []
        rows = self.client.search_read(
            ARTICLE_MODEL,
            domain=domain,
            fields=self._article_fields(),
            limit=limit,
            offset=0,
        )
        return [self._article_from_record(row) for row in rows]

    def get_article(self, article_id: int) -> KnowledgeArticle | None:
        rows = self.client.search_read(
            ARTICLE_MODEL,
            domain=[["id", "=", article_id]],
            fields=self._article_fields(),
            limit=1,
        )
        return self._article_from_record(rows[0]) if rows else None

    def create_article(self, payload: KnowledgeArticleCreate) -> KnowledgeArticle:
        values: dict[str, Any] = {
            "name": payload.name,
            "summary": payload.summary or "",
            "content_html": payload.content_html or "",
            "tags": payload.tags or "",
        }
        if payload.category_id:
            values["category_id"] = payload.category_id
        if payload.owner_agent_id:
            values["owner_agent_id"] = payload.owner_agent_id
        if payload.task_id:
            values["task_id"] = payload.task_id
        if payload.related_ticket_ids:
            values["related_ticket_ids"] = [(6, 0, payload.related_ticket_ids)]

        article_id = self.client.create(ARTICLE_MODEL, values)
        return self.get_article(article_id)  # type: ignore[return-value]

    def update_article(self, article_id: int, payload: KnowledgeArticleUpdate) -> KnowledgeArticle:
        values: dict[str, Any] = {}
        for field in (
            "name",
            "summary",
            "content_html",
            "category_id",
            "owner_agent_id",
            "task_id",
            "tags",
        ):
            value = getattr(payload, field)
            if value is not None:
                values[field] = value
        if payload.related_ticket_ids is not None:
            values["related_ticket_ids"] = [(6, 0, payload.related_ticket_ids)]
        if values:
            self.client.write(ARTICLE_MODEL, article_id, values)
        return self.get_article(article_id)  # type: ignore[return-value]

    def transition_article(
        self,
        article_id: int,
        payload: KnowledgeArticleTransition,
    ) -> KnowledgeArticle:
        method_map = {
            "submit_review": "action_submit_review",
            "publish": "action_publish",
            "archive": "action_archive",
            "reset_draft": "action_reset_draft",
        }
        self.client.execute_kw(ARTICLE_MODEL, method_map[payload.action], [[article_id]], {})
        return self.get_article(article_id)  # type: ignore[return-value]

    @staticmethod
    def _article_fields() -> list[str]:
        return [
            "id",
            "article_ref",
            "name",
            "state",
            "category_id",
            "owner_agent_id",
            "task_id",
            "version",
            "published_at",
        ]

    @staticmethod
    def _many2one_tuple(value: Any) -> tuple[int, str] | None:
        if isinstance(value, list) and len(value) == 2:
            return int(value[0]), str(value[1])
        return None

    def _article_from_record(self, row: dict[str, Any]) -> KnowledgeArticle:
        return KnowledgeArticle(
            id=row["id"],
            article_ref=row.get("article_ref") or None,
            name=row["name"],
            state=row.get("state") or "draft",
            category=self._many2one_tuple(row.get("category_id")),
            owner_agent=self._many2one_tuple(row.get("owner_agent_id")),
            task=self._many2one_tuple(row.get("task_id")),
            version=int(row.get("version") or 1),
            published_at=row.get("published_at") or None,
        )


def get_knowledge_service() -> KnowledgeService:
    credentials = OdooCredentials(
        url=settings.odoo_url,
        database=settings.odoo_db,
        username=settings.odoo_user,
        api_key=settings.odoo_api_key,
        allow_self_signed_ssl=settings.odoo_allow_self_signed_ssl,
    )
    return KnowledgeService(OdooClient(credentials))
