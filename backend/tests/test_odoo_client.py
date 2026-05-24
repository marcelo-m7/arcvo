from app.integrations.odoo.client import OdooCredentials, _is_transient


def test_odoo_credentials_model() -> None:
    credentials = OdooCredentials(
        url="https://example.com",
        database="odoo19",
        username="user@example.com",
        api_key="secret",
    )
    assert credentials.database == "odoo19"


def test_is_transient_eof() -> None:
    exc = Exception("EOF occurred in violation of protocol")
    assert _is_transient(exc) is True


def test_is_transient_normal_error() -> None:
    exc = Exception("Access Denied")
    assert _is_transient(exc) is False


def test_is_transient_connection_reset() -> None:
    assert _is_transient(ConnectionResetError()) is True
