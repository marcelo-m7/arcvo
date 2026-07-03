from typing import Any, Protocol

from app.core.config import settings
from app.integrations.odoo.client import OdooClient, OdooCredentials
from app.schemas.odoo import OdooHealth


class OdooHealthClient(Protocol):
    def version(self) -> dict[str, Any]:
        ...

    def authenticate(self) -> int:
        ...


class OdooService:
    def __init__(
        self,
        client: OdooHealthClient | None,
        database: str,
        configured: bool,
        tls_workaround_enabled: bool = False,
    ) -> None:
        self.client = client
        self.database = database
        self.configured = configured
        self.tls_workaround_enabled = tls_workaround_enabled

    def health(self) -> OdooHealth:
        if self.client is None or not self.configured:
            return OdooHealth(
                status="not_configured",
                configured=False,
                database=self.database or None,
                tls_workaround_enabled=self.tls_workaround_enabled,
            )

        version = self.client.version()
        uid = self.client.authenticate()
        return OdooHealth(
            status="ok",
            configured=True,
            database=self.database,
            server_version=version.get("server_version"),
            authenticated=True,
            uid=uid,
            tls_workaround_enabled=self.tls_workaround_enabled,
        )


def get_odoo_service() -> OdooService:
    if not settings.has_odoo_credentials:
        return OdooService(
            client=None,
            database=settings.odoo_db,
            configured=False,
            tls_workaround_enabled=settings.odoo_allow_self_signed_ssl,
        )

    credentials = OdooCredentials(
        url=settings.odoo_url,
        database=settings.odoo_db,
        username=settings.odoo_user,
        api_key=settings.odoo_api_key,
        allow_self_signed_ssl=settings.odoo_allow_self_signed_ssl,
    )
    return OdooService(
        client=OdooClient(credentials),
        database=settings.odoo_db,
        configured=True,
        tls_workaround_enabled=settings.odoo_allow_self_signed_ssl,
    )
