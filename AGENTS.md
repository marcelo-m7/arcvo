# Contributor Guide

This repository is a clean template for Odoo 19 Community plus a Python FastAPI
backend. Keep it generic and reusable.

## Contracts

- Odoo addons live in `odoo/addons`.
- External addon sources live in `odoo/external-addons`.
- The Odoo image is built from `odoo/Dockerfile` and must remain based on
  `odoo:19`.
- Addons must be copied to `/mnt/extra-addons`.
- The root `docker-compose.yaml` is the Coolify deploy entrypoint.
- The backend app is created in `backend/app/main.py`.
- Backend settings live in `backend/app/core/config.py`.

## Working Rules

- Do not commit real `.env` files or secrets.
- Do not add project-specific business rules to the template.
- Keep examples small and easy to delete.
- Prefer generic names such as `custom_base` for starter addons.
- Keep Makefile targets aligned with files that actually exist.
- After backend or addon changes, run:

```bash
make lint
make test
make validate-addons
docker compose config
```

## Backend Shape

- `backend/app/api/routes`: HTTP route modules.
- `backend/app/core`: settings and app configuration.
- `backend/app/integrations`: external clients.
- `backend/app/services`: application services.
- `backend/app/schemas`: Pydantic models.
- `backend/tests`: pytest tests.

The template should expose only generic endpoints by default:

- `GET /health`
- `GET /api/v1/odoo/health`

## Odoo Addon Shape

A starter addon should include:

- `__manifest__.py`
- `__init__.py`
- `models/__init__.py`
- optional small demo model
- `security/ir.model.access.csv` when a model exists
- `views/` only for generic starter screens

Keep dependencies minimal. Use `base` unless the addon genuinely needs more.
