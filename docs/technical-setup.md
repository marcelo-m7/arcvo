# Arcvo Technical Setup

## Environment

Copy `.env.example` to `.env` and fill in real secrets locally. Do not commit `.env`.

Required Odoo variables:

- `ODOO_URL`
- `ODOO_DB`
- `ODOO_USER`
- `ODOO_API_KEY`
- `ODOO_INTEGRATION_MODE=xmlrpc`
- `ODOO_YOLO=read`

`ODOO_ALLOW_SELF_SIGNED_SSL=true` is a temporary workaround for the current Traefik default certificate on the remote Odoo endpoint. Disable it after HTTPS is fixed.

## Development

```bash
export PATH="$HOME/.local/bin:$PATH"
make install
make dev
```

On this WSL workspace under `/mnt/c`, `pnpm install` may fail with `EACCES` during package renames. If that happens, run `npm install --prefix frontend` as a local fallback, or move the repository to the Linux filesystem, for example under `~/projects`, and rerun `pnpm install`.

Run services separately:

```bash
make backend
make frontend
```

## Backend

The FastAPI app lives in `backend/app`.

- `app/api/routes`: HTTP routes.
- `app/core`: settings and security helpers.
- `app/integrations/odoo`: XML-RPC/JSON-RPC client.
- `app/services`: application service layer.
- `app/schemas`: API response/request schemas.

Primary endpoints:

- `GET /health`
- `GET /api/v1/odoo/health`
- `GET /api/v1/odoo/models/{model}/records`
- `POST /api/v1/odoo/models/{model}/records`
- `PATCH /api/v1/odoo/models/{model}/records/{id}`

## Frontend

The React app lives in `frontend`.

- Vite + TypeScript.
- TailwindCSS v4.
- React Router for pages.
- TanStack Query for server state.
- Zustand for local UI state.

Set `VITE_API_BASE_URL=http://localhost:8000` for local development.

## Odoo and MCP

The backend uses XML-RPC as the primary integration path. JSON-RPC is available in the client for diagnostics.

The MCP server is configured in Codex with:

- `mcp-server-odoo 0.6.0`
- `ODOO_YOLO=read`
- `ODOO_DB=odoo19`

The Odoo-side MCP routes currently return `404`, so full MCP controlled mode requires installing the Odoo MCP module in the Odoo instance.

The Codex MCP connector may continue to show `Reauthentication required` until the MCP process is restarted and the app connection is reauthenticated. XML-RPC and JSON-RPC healthchecks are currently the reliable validation path.

## System Tools

Install tools with:

```bash
make install-system-tools
```

This command needs `sudo` for apt and Docker installation.
