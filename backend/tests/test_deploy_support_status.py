from typing import Any

from app.services import deploy_service as deploy_module


class FakeOdooClient:
    def __init__(self, credentials: Any) -> None:
        self.credentials = credentials

    def authenticate(self) -> int:
        return 1

    def search_count(self, model: str, domain: list[Any] | None = None) -> int:
        domain = domain or []
        if model == "arcvo.helpdesk.ticket" and domain:
            if len(domain) == 3 and domain[0][0] == "sla_deadline":
                return 2
            if len(domain) == 1 and domain[0][0] == "state":
                return 5
        if model == "arcvo.helpdesk.ticket":
            return 12
        if model == "arcvo.knowledge.article" and domain:
            return 9
        if model == "arcvo.knowledge.article":
            return 20
        return 0


class FailingOdooClient:
    def __init__(self, credentials: Any) -> None:
        self.credentials = credentials

    def authenticate(self) -> int:
        raise RuntimeError("odoo unavailable")


def test_support_status_reports_metrics(monkeypatch) -> None:
    monkeypatch.setattr(deploy_module, "OdooClient", FakeOdooClient)

    support = deploy_module.DeployService._support_status()

    assert support["available"] is True
    assert support["helpdesk_total"] == 12
    assert support["helpdesk_open"] == 5
    assert support["helpdesk_sla_breached"] == 2
    assert support["knowledge_total"] == 20
    assert support["knowledge_published"] == 9
    assert support["error"] is None


def test_support_status_reports_error(monkeypatch) -> None:
    monkeypatch.setattr(deploy_module, "OdooClient", FailingOdooClient)

    support = deploy_module.DeployService._support_status()

    assert support["available"] is False
    assert support["error"] is not None
