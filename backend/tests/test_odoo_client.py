from app.integrations.odoo.client import OdooCredentials


def test_odoo_credentials_model() -> None:
    credentials = OdooCredentials(
        url="https://example.com",
        database="odoo19",
        username="user@example.com",
        api_key="secret",
    )
    assert credentials.database == "odoo19"
