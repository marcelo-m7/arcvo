from __future__ import annotations

import shutil
import tempfile
from collections.abc import Awaitable, Callable
from importlib import resources
from pathlib import Path
from typing import Any

import hermes.web_interface
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

DEFAULT_HERMES_PUBLIC_ORIGINS = [
    "https://hermes.marcelo-m7.com",
    "http://localhost:8010",
    "http://127.0.0.1:8010",
]
LOCALHOST_API_BASE = 'baseURL:"http://localhost:8000"'
LOCATION_API_BASE = "baseURL:window.location.origin"


def _origin_list(origins: str | None = None) -> list[str]:
    raw = origins or ",".join(DEFAULT_HERMES_PUBLIC_ORIGINS)
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


def _patch_static_assets(static_dir: Path, public_base_url: str = "") -> None:
    api_base = f'baseURL:"{public_base_url.rstrip("/")}"' if public_base_url else LOCATION_API_BASE
    for path in static_dir.rglob("*.js"):
        text = path.read_text(encoding="utf-8")
        if LOCALHOST_API_BASE in text:
            path.write_text(text.replace(LOCALHOST_API_BASE, api_base), encoding="utf-8")

    index = static_dir / "index.html"
    if index.exists():
        lines = index.read_text(encoding="utf-8").splitlines()
        filtered = [
            line
            for line in lines
            if not (
                'rel="preload"' in line
                and 'as="font"' in line
                and any(font_type in line for font_type in ("font/eot", "font/ttf", "font/woff"))
            )
        ]
        index.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def prepare_static_assets(public_base_url: str = "") -> Path:
    temp_dir = Path(tempfile.mkdtemp())
    dist_path = resources.files(hermes.web_interface) / "dist"
    for item in dist_path.iterdir():
        destination = temp_dir / item.name
        if item.is_dir():
            shutil.copytree(item, destination)
        else:
            shutil.copy2(item, destination)
    _patch_static_assets(temp_dir, public_base_url=public_base_url)
    return temp_dir


def create_hermes_app(
    agent: Any,
    *,
    public_base_url: str = "",
    cors_origins: str | None = None,
) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origin_list(cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.post("/chat")
    async def chat(request: Request):
        data = await request.json()
        message = data.get("message", "")
        chat_history = data.get("chat_history", [])

        if not message:
            return JSONResponse({"error": "Empty message"}, status_code=400)
        if agent is None:
            return JSONResponse({"error": "Agent not available"}, status_code=500)

        execute: Callable[..., Awaitable[Any]] = agent.execute
        return await execute(input_data=message, chat_history=chat_history)

    static_dir = prepare_static_assets(public_base_url=public_base_url)
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    return app


async def run_hermes_web(
    *,
    port: int,
    agent: Any,
    public_base_url: str = "",
    cors_origins: str | None = None,
) -> None:
    app = create_hermes_app(
        agent,
        public_base_url=public_base_url,
        cors_origins=cors_origins,
    )
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


__all__ = [
    "LOCALHOST_API_BASE",
    "LOCATION_API_BASE",
    "create_hermes_app",
    "prepare_static_assets",
    "run_hermes_web",
]
