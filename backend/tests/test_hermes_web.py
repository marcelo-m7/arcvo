from pathlib import Path

from fastapi.testclient import TestClient

from app.hermes.web import (
    LOCALHOST_API_BASE,
    LOCATION_API_BASE,
    create_hermes_app,
    prepare_static_assets,
)


class FakeAgent:
    async def execute(self, input_data: str, chat_history: list) -> dict[str, object]:
        return {"response": f"ok: {input_data}", "chat_history": chat_history}


def _read_static(static_dir: Path) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in static_dir.rglob("*")
        if path.is_file() and path.suffix in {".html", ".js", ".css"}
    )


def test_prepare_static_assets_rewrites_localhost_api_base() -> None:
    static_dir = prepare_static_assets()
    text = _read_static(static_dir)

    assert LOCALHOST_API_BASE not in text
    assert LOCATION_API_BASE in text


def test_prepare_static_assets_removes_legacy_font_preloads() -> None:
    static_dir = prepare_static_assets()
    index = (static_dir / "index.html").read_text(encoding="utf-8")

    assert "font/eot" not in index
    assert "font/ttf" not in index
    assert "font/woff" not in index


def test_prepare_static_assets_can_use_public_base_url() -> None:
    static_dir = prepare_static_assets(public_base_url="https://hermes.example.com/")
    text = _read_static(static_dir)

    assert LOCALHOST_API_BASE not in text
    assert 'baseURL:"https://hermes.example.com"' in text


def test_hermes_chat_route_uses_agent() -> None:
    app = create_hermes_app(FakeAgent())
    client = TestClient(app)

    response = client.post("/chat", json={"message": "ping", "chat_history": []})

    assert response.status_code == 200
    assert response.json()["response"] == "ok: ping"
