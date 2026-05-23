from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import archive, auth, health, odoo
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(archive.router, prefix="/api/v1/archive", tags=["archive"])
    app.include_router(odoo.router, prefix="/api/v1/odoo", tags=["odoo"])
    return app


app = create_app()
