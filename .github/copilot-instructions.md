# Arcvo Coding Instructions

Arcvo is a remote-Odoo production line for:

- YouTube/Supabase content imported into Odoo eLearning.
- Arcvo agents tracked in Odoo projects through `arcvo_agents`.

## Canonical Contracts

- Odoo target: `https://marcelo-m7.com`, DB `odoo19`.
- Odoo agent addon: `odoo/addons/arcvo_agents`.
- Agent models: `arcvo.agent`, `arcvo.agent.capability`, `arcvo.agent.assignment`, `arcvo.agent.audit.log`.
- Archive models: native Odoo eLearning `slide.channel` and `slide.slide`.

Do not reintroduce `agent_registry`, `autonomous_agents`, `agent.*`, Hermes runtime, or local Odoo Docker as primary architecture.

## Backend

- Use FastAPI routes as thin adapters.
- Put business logic in `backend/app/services`.
- Put API contracts in `backend/app/schemas`.
- Use `backend/app/integrations/odoo/client.py` for XML-RPC/JSON-RPC.
- Protect admin routes with `require_admin`.
- Never log `.env` secrets, API keys, JWTs, or passwords.

## Frontend

- Use React + Vite + TypeScript.
- Use TanStack Query for server state and Zustand for local session/UI state.
- Keep `/acervo`, `/agentes`, and `/odoo` operational screens, not marketing pages.
- Use clear dashboard/admin controls with lucide icons.

## Odoo

- Active custom addons live in `odoo/addons`.
- Frozen/vendor addons live in `odoo/frozen_addons` and are outside canonical deploy.
- Use `arcvo.*` model names for project-specific records.
- Keep Odoo views, security, models, and manifests valid for Odoo 19.

## Validation

Run:

```bash
make lint
make test
make validate-arcvo-agents
```
