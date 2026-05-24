from typing import Any

from app.schemas.knowledge import KnowledgeArticleCreate, KnowledgeArticleTransition
from app.services.knowledge_service import KnowledgeService


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
        if model == "arcvo.knowledge.article":
            return [
                {
                    "id": 21,
                    "article_ref": "KBA-00021",
                    "name": "How to recover deploy",
                    "state": "draft",
                    "category_id": [3, "Operations"],
                    "owner_agent_id": [7, "Backend Operator"],
                    "task_id": [55, "Fix prod"],
                    "version": 1,
                    "published_at": False,
                }
            ]
        if model == "arcvo.knowledge.category":
            return [
                {
                    "id": 3,
                    "name": "Operations",
                    "complete_name": "Operations",
                    "active": True,
                    "article_count": 1,
                }
            ]
        return []

    def create(self, model: str, values: dict[str, Any]) -> int:
        self.created.append((model, values))
        return 21

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


def test_create_article_creates_arcvo_knowledge_record() -> None:
    client = FakeOdooClient()
    service = KnowledgeService(client)  # type: ignore[arg-type]

    article = service.create_article(KnowledgeArticleCreate(name="How to recover deploy"))

    assert article.id == 21
    assert client.created[0][0] == "arcvo.knowledge.article"
    assert client.created[0][1]["name"] == "How to recover deploy"


def test_transition_article_calls_domain_method() -> None:
    client = FakeOdooClient()
    service = KnowledgeService(client)  # type: ignore[arg-type]

    service.transition_article(21, KnowledgeArticleTransition(action="publish"))

    assert client.exec_calls
    model, method, args, _kwargs = client.exec_calls[0]
    assert model == "arcvo.knowledge.article"
    assert method == "action_publish"
    assert args == [[21]]
