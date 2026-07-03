import json

from app.integrations.odoo.client import OdooClientError
from app.services.odoo_service import get_odoo_service


def main() -> None:
    try:
        health = get_odoo_service().health()
    except OdooClientError as exc:
        print(
            json.dumps(
                {
                    "status": "error",
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
