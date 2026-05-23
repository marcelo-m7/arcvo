from app.core.config import settings
from app.integrations.odoo.client import OdooClient, OdooCredentials
from app.schemas.odoo import OdooHealth, OdooRecordList


class OdooService:
    def __init__(self, client: OdooClient) -> None:
        self.client = client

    def health(self) -> OdooHealth:
        version = self.client.version()
        uid = self.client.authenticate()
        partner_count = self.client.search_count("res.partner")
        return OdooHealth(
            status="ok",
            integration_mode=settings.odoo_integration_mode,
            url=settings.odoo_url,
            database=settings.odoo_db,
            server_version=version.get("server_version"),
            authenticated=True,
            uid=uid,
            partner_count=partner_count,
            mcp_mode=settings.odoo_yolo,
            tls_workaround_enabled=settings.odoo_allow_self_signed_ssl,
        )

    def list_records(self, model: str, limit: int, offset: int) -> OdooRecordList:
        records = self.client.search_read(model=model, limit=limit, offset=offset)
        count = self.client.search_count(model)
        return OdooRecordList(
            model=model,
            limit=limit,
            offset=offset,
            count=count,
            records=records,
        )

    def create_record(self, model: str, values: dict) -> int:
        return self.client.create(model, values)

    def update_record(self, model: str, record_id: int, values: dict) -> bool:
        return self.client.write(model, record_id, values)


def get_odoo_service() -> OdooService:
    credentials = OdooCredentials(
        url=settings.odoo_url,
        database=settings.odoo_db,
        username=settings.odoo_user,
        api_key=settings.odoo_api_key,
        allow_self_signed_ssl=settings.odoo_allow_self_signed_ssl,
    )
    return OdooService(OdooClient(credentials))
