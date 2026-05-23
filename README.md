# Arcvo

Autonomous multi-agent organization for digital archive coordination, backed by Odoo 19.

## Architecture

**Arcvo** is built as a self-governing organization where agents autonomously claim and execute work tracked in Odoo.

- **Agent Registry** (Odoo addon): Central nervous system for agent profiles, capabilities, assignments, and audit trails
- **Agent APIs** (FastAPI): HTTP endpoints for agent coordination (heartbeat, task claiming, progress reporting)
- **Demo Agents**: Pre-configured CEO, PM, developers, QA, and support agents ready to collaborate
- **Audit Trail**: Immutable action logging for compliance and debugging

See [AGENTS.md](AGENTS.md) for organization structure and workflows.

## Stack

- Frontend: React, Vite, TypeScript, TailwindCSS, TanStack Query, Zustand
- Backend: FastAPI, Pydantic, Uvicorn, XML-RPC/JSON-RPC Odoo client
- Odoo: Odoo 19 with **agent_registry** addon for multi-agent orchestration
- MCP: `mcp-server-odoo` configured for read-only YOLO mode (pending module install)
- Integration: YouTube URLs, Supabase import, multi-provider archive

## Quick Start

```bash
# Prerequisites
make tools-check

# Setup environment
make install

# Start services
make dev          # Frontend + Backend locally
make docker-up    # Odoo + PostgreSQL + addons

# Access
Frontend: http://localhost:5173
Backend:  http://localhost:8000
API Docs: http://localhost:8000/docs
Odoo:     http://localhost:8069
```

## Agents & Autonomy

The system is designed for autonomous operation:

```bash
# Validate Odoo connectivity and agent setup
make odoo-health

# View agent registration in Odoo
# → Go to http://localhost:8069 → Agents menu

# Agents coordinate via REST API
# → See http://localhost:8000/docs → /api/v1/agents/*
```

New agents register, discover tasks, and report progress autonomously. See [AGENTS.md](AGENTS.md) and [PHASE3_COMPLETION_REPORT.md](PHASE3_COMPLETION_REPORT.md) for implementation details.

## Documentation

- **[AGENTS.md](AGENTS.md)** — Agent-based organization structure, workflows, troubleshooting
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** — Code conventions and standards
- **[PHASE3_COMPLETION_REPORT.md](PHASE3_COMPLETION_REPORT.md)** — Multi-agent architecture implementation
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** — Validation steps for agent registry
- **[docs/technical-setup.md](docs/technical-setup.md)** — Low-level setup details

## Useful Commands

```bash
# Validation
make tools-check      # Verify system dependencies
make odoo-health      # Test Odoo XML-RPC connectivity

# Development
make dev              # Frontend + Backend with auto-reload
make backend          # Backend only
make frontend         # Frontend only

# Quality
make lint             # Check code style (Ruff + ESLint)
make test             # Run all tests (pytest + typecheck)
make format           # Auto-format code

# Infrastructure
make docker-up        # Start Odoo + PostgreSQL
make docker-down      # Stop containers
```

## Architecture Overview

```
Autonomous Multi-Agent Organization
    ↓
Odoo 19 (Central ERP)
├── agent_registry addon
│   ├── agent.agent (agent profiles + status)
│   ├── agent.capability (skills catalog)
│   ├── agent.assignment (task bindings)
│   └── agent.audit_log (immutable actions)
└── project module (extended)
    └── project.task (with agent assignments)
    ↑
FastAPI Backend
├── /api/v1/agents/* (agent CRUD + heartbeat)
├── /api/v1/tasks/* (task coordination)
└── /api/v1/audit/* (audit log queries)
    ↑
Autonomous Agents
├── CEO (orchestration)
├── PM (project management)
├── Backend Dev (development)
├── Frontend Dev (UI/UX)
├── DevOps (infrastructure)
├── QA (quality assurance)
└── Docs (documentation)
```

## Key Features

✅ Agent registration & discovery  
✅ Capability-based task routing  
✅ Real-time workload tracking  
✅ Heartbeat health monitoring  
✅ Immutable audit trail  
✅ Automatic status indicators  
✅ Task assignment workflows  
✅ Progress reporting & completion tracking

## Default Admin Login

Uses `APP_ADMIN_PASSWORD` from `.env`.
