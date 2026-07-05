# Development Notes

## Backend

Install dependencies:

```bash
make install
```

Run the API locally:

```bash
make backend
```

Available endpoints:

- `GET /health`
- `GET /api/v1/odoo/health`

The Odoo health endpoint is intentionally read-only. It reports
`not_configured` until `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, and `ODOO_API_KEY`
are set.

## Odoo

The starter addon is `odoo/addons/custom_base`.

Use it as a shape reference for new addons:

- manifest
- model package
- access CSV
- XML views
- addon README

Validate addon structure with:

```bash
make validate-addons
```

## Docker Compose

The root compose file is the deployment entrypoint for Coolify-compatible
builds. It builds Odoo from `odoo/Dockerfile`, starts PostgreSQL, and preserves
Odoo and database data in named volumes.

## Supabase (tube-o2)

Use docs/supabase-tube-o2-migration.md as the standard runbook for:

- schema convergence with `mcp_supabase_apply_migration`
- edge function deployment
- post-migration validation and advisors

Do not replay all historical SQL files blindly. Prefer a convergence migration
that matches the stable baseline defined in the playbook.
