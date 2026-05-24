import json

from app.core.config import settings
from app.integrations.odoo.client import OdooClient, OdooClientError, OdooCredentials
from app.services.odoo_service import get_odoo_service


def main() -> None:
    try:
        health = get_odoo_service().health()
    except OdooClientError as exc:
        client = OdooClient(
            OdooCredentials(
                url=settings.odoo_url,
                database=settings.odoo_db,
                username=settings.odoo_user,
                api_key=settings.odoo_api_key,
                allow_self_signed_ssl=settings.odoo_allow_self_signed_ssl,
            )
        )
        try:
            version = client.version()
        except OdooClientError:
            version = {}
        print(
            json.dumps(
                {
                    "status": "error",
                    "url": settings.odoo_url,
                    "database": settings.odoo_db,
                    "server_version": version.get("server_version"),
                    "authenticated": False,
                    "error": str(exc),
                },
                indent=2,
            )
        )
        raise SystemExit(1) from exc

    print(health.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
