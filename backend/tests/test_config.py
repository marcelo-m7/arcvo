from app.core.config import Settings


def test_cors_origin_list_splits_values() -> None:
    settings = Settings(cors_origins="http://localhost:8000, https://example.com, ")

    assert settings.cors_origin_list == ["http://localhost:8000", "https://example.com"]


def test_cors_origin_list_accepts_wildcard() -> None:
    settings = Settings(cors_origins="*")

    assert settings.cors_origin_list == ["*"]


def test_odoo_credentials_are_optional() -> None:
    settings = Settings(odoo_db="", odoo_user="", odoo_api_key="")

    assert settings.has_odoo_credentials is False
