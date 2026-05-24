from typing import Any

from app.services import deploy_service as deploy_module


class FakeOdooClient:
    def __init__(self, credentials: Any) -> None:
        self.credentials = credentials

    def authenticate(self) -> int:
        return 1

    def search_count(self, model: str, domain: list[Any] | None = None) -> int:
        domain = domain or []
        if model == "arcvo.agent" and domain:
            return 4
        if model == "arcvo.agent":
            return 6
        if model == "arcvo.agent.assignment" and domain[0][2] == "blocked":
            return 1
        if model == "arcvo.agent.assignment":
            return 3
        if model == "project.task":
            return 8
        if model == "arcvo.agent.audit.log":
            return 21
        return 0


class FailingOdooClient:
    def __init__(self, credentials: Any) -> None:
        self.credentials = credentials

    def authenticate(self) -> int:
        raise RuntimeError("odoo unavailable")


def test_operations_status_reports_metrics(monkeypatch) -> None:
    monkeypatch.setattr(deploy_module, "OdooClient", FakeOdooClient)

    operations = deploy_module.DeployService._operations_status()

    assert operations["available"] is True
    assert operations["agents_total"] == 6
    assert operations["agents_available"] == 4
    assert operations["assignments_open"] == 3
    assert operations["assignments_blocked"] == 1
    assert operations["tasks_requiring_agent"] == 8
    assert operations["audit_total"] == 21
    assert operations["error"] is None


def test_operations_status_reports_error(monkeypatch) -> None:
    monkeypatch.setattr(deploy_module, "OdooClient", FailingOdooClient)

    operations = deploy_module.DeployService._operations_status()

    assert operations["available"] is False
    assert operations["error"] is not None
