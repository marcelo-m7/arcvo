# Coding Instructions

This repository is an Odoo 19 Community and FastAPI template. Keep the codebase
generic, deployable, and easy to fork for a new project.

## Backend

- Create the FastAPI app in `backend/app/main.py`.
- Put settings in `backend/app/core/config.py`.
- Keep routes thin and generic.
- Keep reusable client code under `backend/app/integrations`.
- Do not log secrets or environment variable values.

## Odoo

- Put custom addons under `odoo/addons`.
- Keep `odoo/Dockerfile` based on `odoo:19`.
- Keep addon copying to `/mnt/extra-addons`.
- Keep starter addon dependencies minimal, usually only `base`.
- Validate manifests and XML with `make validate-addons`.

## Validation

Run this before handing off changes:

```bash
make lint
make test
make validate-addons
docker compose config
```

## Supabase

- For tube-o2 Supabase work, use `docs/supabase-tube-o2-migration.md` as the
	source of truth.
- Apply schema convergence with `mcp_supabase_apply_migration`.
- Validate public tables, RLS, key RPCs, and advisor findings after migration.
- Deploy edge functions from `frontend/tube-o2/supabase/functions`.
