from typing import Any

from app.services.odoo_service import OdooService


class FakeOdooClient:
    def version(self) -> dict[str, Any]:
        return {"server_version": "19.0"}

    def authenticate(self) -> int:
        return 42


def test_odoo_health_reports_not_configured_without_credentials() -> None:
    service = OdooService(
        client=None,
        database="",
        configured=False,
        tls_workaround_enabled=False,
    )

    health = service.health()

    assert health.status == "not_configured"
    assert health.configured is False
    assert health.authenticated is False


def test_odoo_health_authenticates_when_configured() -> None:
    service = OdooService(
        client=FakeOdooClient(),
        database="template",
        configured=True,
        tls_workaround_enabled=True,
    )

    health = service.health()

    assert health.status == "ok"
    assert health.configured is True
    assert health.database == "template"
    assert health.server_version == "19.0"
    assert health.authenticated is True
    assert health.uid == 42
    assert health.tls_workaround_enabled is True
