from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def test_login_valid_password() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/auth/login", json={"password": settings.app_admin_password})
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_invalid_password() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/auth/login", json={"password": "wrong-password"})
    assert response.status_code == 401
