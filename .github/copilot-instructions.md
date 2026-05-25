# Arcvo Coding Instructions

Arcvo is a remote-Odoo production line for YouTube/Supabase content (eLearning) and Odoo-tracked digital agents (`arcvo_agents` addon).

**Production target:** Odoo at `https://marcelo-m7.com`, DB `odoo19`.

---

## Quick Start

```bash
make install              # Setup .venv and dependencies (uv sync)
make backend              # Start FastAPI on http://localhost:8000
make lint test            # Validate code quality
make odoo-health          # Check Odoo connectivity
make ollama-health        # Check Ollama API
make validate-arcvo-agents # Validate Odoo addon
```

See [QUICK_START.md](../QUICK_START.md) for 5-min deployment validation or [technical-setup.md](../docs/technical-setup.md) for environment details.

---

## Canonical Contracts

**Do not reintroduce:** `agent_registry`, `autonomous_agents`, `agent.*`, Hermes runtime, or local Odoo Docker.

**Agent models:** Use `arcvo.*` prefixes only:
- `arcvo.agent` — Employee (hr.employee extended) that acts as an agent
- `arcvo.agent.capability` — Skills/permissions
- `arcvo.agent.assignment` — Task routing
- `arcvo.agent.audit.log` — Execution history

**Archive models:** Native Odoo eLearning (`slide.channel`, `slide.slide`).

---

## Architecture Zones

### Backend (`backend/app`)

- **Routes** (`api/routes/`): Thin HTTP adapters; routes are read-only or trigger services
- **Services** (`services/`): Business logic; handle archive, Odoo sync, deploy, agents
- **Schemas** (`schemas/`): Pydantic contracts for API requests/responses
- **Integrations** (`integrations/`): External clients (Odoo XML-RPC, Supabase, Ollama)
- **Core** (`core/`): Config, security, auth, internal access checks

**Rules:**
- Use `backend/app/integrations/odoo/client.py` for all Odoo communication (XML-RPC/JSON-RPC)
- Put business logic in services, not routes
- Protect admin routes with `require_admin` decorator
- **Never log secrets**: No `.env` values, API keys, JWTs, or passwords in output

### Odoo Addon (`odoo/addons/arcvo_agents`)

- **Models** (`models/`): Database structure (Python classes)
  - `agent.py`, `assignment.py`, `capability.py` — Core entities
  - `agent_orchestration.py` — Cron job execution logic
  - `ollama_client.py` — LLM integration
  - `agent_message.py`, `discuss_response_engine.py` — Discuss integration
- **Views** (`views/`): XML form/tree/kanban definitions
- **Data** (`data/`): XML fixtures, cron job config
- **Security** (`security/`): ACL rules, record rules

**Rules:**
- Extend `hr.employee` (use `_inherit`), not replace
- Use `arcvo.*` model names for custom records
- Keep XML valid for Odoo 19 Community
- Test views in Odoo UI after changes

### Frontend

Located in `frontend/src` (if created). Use React + Vite + TypeScript.
- **State:** TanStack Query (server), Zustand (local/UI)
- **Screens:** `/acervo`, `/agentes`, `/odoo` are operational dashboards, not marketing pages
- **Design:** lucide-react icons, clear controls, minimal frills

---

## Common Tasks

### Adding an Agent Capability

1. Create in Odoo: `arcvo.agent.capability` record (data file or UI)
2. Backend: Update `backend/app/schemas/agents.py` if API schema changes
3. Test: Run agent with capability enabled, check `arcvo.agent.message` log

### Modifying Agent Execution Logic

1. Edit `odoo/addons/arcvo_agents/models/agent_orchestration.py`
2. Cron runs every 5 min → check `arcvo.agent.audit.log` for history
3. Or trigger manual test via Odoo UI (agent form → "Test Agent" button)
4. Run `make validate-arcvo-agents` to check for syntax errors

### Extending Odoo Models

Use `_inherit` (never `_name`). Example:
```python
class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    is_agent = fields.Boolean(...)
```

### Adding API Endpoints

1. Create route file: `backend/app/api/routes/myroute.py`
2. Add to `backend/app/main.py`: `app.include_router(myroute.router)`
3. Put logic in `backend/app/services/` (not in route)
4. Test: `curl http://localhost:8000/api/v1/...`

### Testing

**Run all:** `make test` (pytest + Odoo addon validation)

**Test locations:**
- Backend: `backend/tests/test_*.py`
- Addon: `odoo/addons/arcvo_agents/tests/` (if needed, create per Odoo pattern)

**Coverage:** Aim for >70% on critical paths (services, models). Routes and schema validation are lighter.

---

## Common Pitfalls

### Secret Leakage

❌ **Bad:**
```python
print(f"API Key: {os.getenv('ODOO_API_KEY')}")  # LOGGED
import json; json.dumps({"password": env.APP_ADMIN_PASSWORD})  # EXPOSED
```

✅ **Good:**
```python
logger.debug("Odoo XML-RPC call initiated")  # No values
if error:
    logger.error("Auth failed")  # Message only, no credentials
```

### Odoo XML-RPC Connection Issues

**If `execute_kw` fails:**
1. Check `.env`: `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_API_KEY`
2. Verify `ODOO_INTEGRATION_MODE=xmlrpc` in `.env`
3. Test: `make odoo-health`
4. Odoo may require re-auth after deploy: reload UI and retry

### Agent Not Executing

1. Check employee has `is_agent=True` and `user_id` set
2. Check Ollama is reachable: `make ollama-health`
3. Review cron logs: **Settings** → **Automation** → **Scheduled Actions** → "Arcvo: Run Active Agents"
4. Or test manually: Odoo UI → Employee form → "Test Agent" button → check `arcvo.agent.message` log

### Model Migration or Data Consistency

After modifying `arcvo_agents` models:
1. Uninstall addon from Odoo UI
2. Clear Python cache: `find odoo/addons/arcvo_agents -type d -name __pycache__ -exec rm -rf {} +`
3. Re-install addon (Odoo will auto-run `__init__.py` migrations)

---

## Environment & Dependencies

- **Python:** 3.11+
- **Dependency manager:** `uv` (in Makefile)
- **Backend framework:** FastAPI
- **Odoo:** 19 Community (remote)
- **LLM:** Ollama (`gemma3:4b` recommended)

Install system tools once: `make install-system-tools`

---

## Validation & Deployment

**Before commit:**
```bash
make lint          # Ruff check
make format        # Auto-format (optional, recommended)
make test          # Pytest
make validate-arcvo-agents  # Addon validation
```

**Deploy:**
1. Push to `main` → Coolify auto-builds Odoo Docker image
2. Manual trigger: `POST /api/v1/deploy/coolify` (admin only)
3. See [DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md) for validation steps

**Rollback:**
- Uninstall addon from Odoo UI, or revert git commit

---

## Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) — System diagram, data flow, cron/webhook logic
- [technical-setup.md](../docs/technical-setup.md) — Environment variables, dev tools, integrations
- [odoo-agent-orchestration.md](../docs/odoo-agent-orchestration.md) — Agent execution deep dive
- [QUICK_START.md](../QUICK_START.md) — 5-min deployment test
- [DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md) — Production validation checklist
