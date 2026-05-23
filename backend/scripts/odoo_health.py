from app.services.odoo_service import get_odoo_service


def main() -> None:
    health = get_odoo_service().health()
    print(health.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
