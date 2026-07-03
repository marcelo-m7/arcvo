# Odoo FastAPI Template

Reusable development template for projects that combine:

- Odoo 19 Community with custom addons
- Python backend with FastAPI
- PostgreSQL for Odoo
- Docker Compose deploys compatible with Coolify

The repository is intentionally small. It contains no product-specific rules,
sample production data, third-party import flows, or project-specific workflows.

## Structure

```text
backend/
  app/
    api/routes/       FastAPI route modules
    core/             settings and application configuration
    integrations/     external clients
    schemas/          Pydantic response models
    services/         application services
  scripts/            small local validation helpers
  tests/              pytest suite
odoo/
  Dockerfile          Odoo image based on odoo:19
  addons/custom_base  minimal addon template
docs/                 development notes
docker-compose.yaml   Coolify-compatible Odoo + PostgreSQL stack
```

## Local Commands

```bash
make install          # install backend dependencies with uv
make backend          # run FastAPI on http://localhost:8000
make lint             # run ruff
make format           # format backend Python files
make test             # run pytest
make odoo-health      # check configured Odoo connectivity
make validate-addons  # validate addon manifests and XML
make all              # lint, tests, and addon validation
```

FastAPI exposes:

- `GET /health`
- `GET /api/v1/odoo/health`

## Environment

Copy `.env.example` to `.env` for local development and fill in real values
there. Do not commit `.env`.

Important variables:

- `APP_ENV`
- `APP_NAME`
- `CORS_ORIGINS`
- `ODOO_URL`
- `ODOO_DB`
- `ODOO_USER`
- `ODOO_API_KEY`
- `ODOO_ALLOW_SELF_SIGNED_SSL`
- `SERVICE_FQDN_ODOO_8069`
- `SERVICE_USER_POSTGRES`
- `SERVICE_PASSWORD_POSTGRES`

`GET /api/v1/odoo/health` returns `not_configured` until the Odoo variables are
set.

## Odoo Addons

Custom addons live under `odoo/addons`. The Dockerfile copies this directory to
`/mnt/extra-addons`, which keeps the image compatible with Odoo's standard addon
loading pattern.

To create a new addon:

1. Copy `odoo/addons/custom_base` to a new addon directory.
2. Update `__manifest__.py` with the addon name, summary, and dependencies.
3. Replace the demo model, access rules, and views with your project model.
4. Run `make validate-addons`.
5. Install or upgrade the addon in the Odoo UI.

## Coolify Deploy

The root `docker-compose.yaml` is the deploy entrypoint. It keeps:

- `odoo` service built from `odoo/Dockerfile`
- `postgresql` service based on `postgres:16-alpine`
- persistent volumes for Odoo and PostgreSQL
- Odoo healthcheck
- Coolify-compatible environment variables for the Odoo public FQDN and
  PostgreSQL credentials

The Odoo image remains based on `odoo:19` and copies addons to
`/mnt/extra-addons`.

On a new PostgreSQL volume, Odoo opens the database manager first. Create the
initial database there, then install `custom_base` from the Apps menu.

## Validation

Before handing off changes, run:

```bash
make install
make lint
make test
make all
docker compose config
```

When Docker is available, also run:

```bash
docker compose build
```
