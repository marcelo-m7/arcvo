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
