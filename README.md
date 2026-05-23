# Arcvo

Fullstack workspace for a digital archive backed by Odoo 19.

## Stack

- Frontend: React, Vite, TypeScript, TailwindCSS, TanStack Query, Zustand.
- Backend: FastAPI, Pydantic Settings, Uvicorn, XML-RPC/JSON-RPC Odoo client.
- Odoo: Odoo 19 remote integration plus local addon workspace under `odoo/addons`.
- MCP: `mcp-server-odoo` configured for read-only YOLO mode while the Odoo-side MCP module is unavailable.

## Quick Start

```bash
export PATH="$HOME/.local/bin:$PATH"
make install
make dev
```

Frontend: http://localhost:5173

Backend: http://localhost:8000

API docs: http://localhost:8000/docs

## Useful Commands

```bash
make tools-check
make odoo-health
make lint
make test
make docker-up
make docker-down
```

See [docs/technical-setup.md](docs/technical-setup.md) for setup and integration details.
