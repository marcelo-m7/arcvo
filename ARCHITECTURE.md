# Architecture Overview

## Current State (After Refactor)

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Arcvo System                                │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐         ┌──────────────────────────┐
│   Odoo 19 (Primary)      │         │  Ollama (LLM Engine)     │
│  marcelo-m7.com:8069     │◄────────┤ api.ollama.monynha.me    │
│                          │         │                          │
│  ┌────────────────────┐  │         └──────────────────────────┘
│  │  hr.employee       │  │  
│  │  is_agent=True     │  │  ┌──────────────────────────┐
│  │  ┌──────────────┐  │  │  │ PostgreSQL (Data)        │
│  │  │  Cron Job    │──┼──┼──│  port 5432               │
│  │  │  (5 min)     │  │  │  └──────────────────────────┘
│  │  └──────────────┘  │  │
│  │                    │  │  ┌──────────────────────────┐
│  │  ┌──────────────┐  │  │  │ Supabase (Archive)       │
│  │  │ Manual Test  │◄─┼──┼──│ wvkjainfwsyiyfcmbtid     │
│  │  │ Button       │  │  │  └──────────────────────────┘
│  │  └──────────────┘  │  │
│  │                    │  │
│  │  arcvo_agents      │  │
│  │  addon:            │  │
│  │  • agent_*         │  │
│  │  • message logs    │  │
│  │  • Discuss posts   │  │
│  │  • Cron schedule   │  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ Backend APIs       │  │
│  │ • /health          │  │
│  │ • /archive/*       │  │
│  │ • /odoo/health     │  │
│  │ • /deploy/*        │  │
│  │ (NO agent logic)   │  │
│  └────────────────────┘  │
└──────────────────────────┘
         ↓
   ┌─────────────┐
   │   Coolify   │
   │ (CD/deploy) │
   └─────────────┘
```

## What Changed?

### Removed
❌ **Hermes** (web dashboard + Agent SDK)
- ❌ `backend/app/hermes/` directory
- ❌ `backend/Dockerfile.hermes` container
- ❌ `docker-compose` hermes service
- ❌ Environment variables: `HERMES_*`

❌ **Backend Agent Logic**
- ❌ `backend/app/services/agent_runner.py`
- ❌ `backend/app/api/routes/agents.py`
- ❌ Agent endpoints (`POST /agents/run`, etc)

### Added
✅ **Odoo Addon** (`arcvo_agents`)
- ✅ `ollama_client.py` — HTTP client for Ollama
- ✅ `agent_orchestration.py` — hr.employee extension + cron job
- ✅ `agent_message.py` — Audit log model
- ✅ Views (XML) for UI

### Kept
✅ **Backend Support APIs** (simplified)
- Archive service
- Health checks
- Deploy integration

---

## Agent Execution Flow

### Scenario: Cron-Triggered Execution

```
[Every 5 minutes]
     ↓
    Odoo Cron Job: _cron_run_active_agents()
     ↓
    Find active agents: hr.employee where is_agent=True, agent_active=True
     ↓
    For each agent:
     ├─ Build prompt (custom or generic)
     ├─ Call OllamaClient.generate(prompt)
     ├─ Ollama processes LLM → response
     ├─ Parse JSON from response
     ├─ Create arcvo.agent.message log (immutable)
     ├─ Post to employee's Discuss channel
     └─ Update agent_status, agent_last_execution
```

### Scenario: Manual Test Execution

```
[User clicks "🤖 Test Agent" button]
     ↓
    action_test_agent() called
     ↓
    Set agent_status = "running"
     ↓
    Build test prompt
     ↓
    Call OllamaClient.generate(test_prompt)
     ↓
    Ollama processes → response
     ↓
    Create arcvo.agent.message log
     ├─ status = "success" or "error"
     └─ error_message if failed
     ↓
    Post to Discuss
     ↓
    Show notification: "Agent Test Successful" or error
     ↓
    Set agent_status = "idle"
```

---

## Configuration Locations

### Odoo System Parameters (Settings → System Parameters)

| Parameter | Example | Purpose |
|-----------|---------|---------|
| `arcvo.ollama_uri` | `https://api.ollama.monynha.me` | Ollama API endpoint |
| `arcvo.ollama_timeout_seconds` | `90` | Request timeout (s) |
| `arcvo.ollama_password` | (empty) | Auth if needed |

### Cron Job Configuration (data/cron_jobs.xml)

```xml
<record id="cron_run_active_agents" model="ir.cron">
    <field name="interval_number">5</field>
    <field name="interval_type">minutes</field>
    <field name="active" eval="True"/>
</record>
```

### Agent Configuration (hr.employee form)

Per-agent customization:
- **is_agent**: Flag to enable agent mode
- **ollama_model**: Which LLM model to use
- **ollama_system_prompt**: Custom instructions for agent
- **agent_active**: Include in cron execution
- **agent_status**: Current state (idle/running/error)

---

## Data Model

### arcvo.agent.message (Immutable Audit Log)

```
┌─────────────────────────────────┐
│  arcvo.agent.message            │
├─────────────────────────────────┤
│ agent_id → hr.employee          │
│ prompt → Text (input)           │
│ raw_response → Text (output)    │
│ decision → JSON (parsed)        │
│ status → Selection (success)    │
│ llm_duration_seconds → Float    │
│ create_date → Datetime          │
│ discuss_message_id → Optional   │
└─────────────────────────────────┘
```

**Purpose**: Complete audit trail of all agent decisions. Can never be modified/deleted.

### hr.employee (Extended)

New fields added:
- `is_agent` → Boolean (enable agent mode)
- `agent_status` → Selection (idle/running/paused/error)
- `agent_active` → Boolean (include in cron)
- `agent_last_execution` → Datetime
- `agent_last_error` → Text
- `ollama_model` → Char
- `ollama_system_prompt` → Text
- `agent_message_ids` → One2many (to arcvo.agent.message)

**OllamaClient** (Utility, not a model)
- Python requests-based HTTP client
- No database persistence
- Used by agent_orchestration.py to call Ollama API

---

## Key Differences from Previous Architecture

| Aspect | Before (Hermes) | After (Odoo) |
|--------|---|---|
| **Registry** | Separate `arcvo.agent` model | `hr.employee` with `is_agent=True` |
| **Execution** | FastAPI backend service | Odoo addon (Python, in-process) |
| **Orchestration** | Hermes SDK + dashboard | Odoo cron job + manual actions |
| **LLM Calls** | Backend HTTP client | Addon OllamaClient |
| **UI** | Hermes web dashboard | Odoo employee form |
| **Logs** | `arcvo.agent.audit.log` | `arcvo.agent.message` |
| **Discuss Integration** | Backend posts messages | Addon posts directly |
| **Manual Trigger** | Hermes web button | Odoo form button |
| **Cron Schedule** | N/A (N/A) | Every 5 minutes |
| **Configuration** | Env vars, Hermes UI | Odoo System Parameters + form |
| **Test Method** | Hermes chat UI | Form button "Test Agent" |

---

## Deployment Model

### Docker Compose (Production)

Services:
- `odoo` — Main application + addon code
- `postgresql` — Data persistence
- `hermes` — **REMOVED** ✓

Environment Variables:
- `ODOO_*` — Odoo connection (still used)
- `OLLAMA_*` — **Removed from .env** (now in System Parameters)
- `HERMES_*` — **Removed** ✓
- `SUPABASE_*` — Archive integration (unchanged)

### Coolify Deployment

- Automatic on push to `main`
- Builds `Dockerfile` (Odoo instance)
- Copies `odoo/addons` to `/mnt/extra-addons`
- No Hermes service to build

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Cron frequency | 5 min | Configurable |
| Ollama timeout | 90s | Configurable per agent |
| Model | gemma3:4b | 4B params, fast |
| Message log growth | ~1 per execution | Immutable, no cleanup |
| Concurrent agents | 1 per cycle | Cron processes sequentially |
| First run | ~20-30s | Model loading |
| Subsequent runs | ~5-10s | Model cached |

---

## File Reference

### New Files (Added)
- `odoo/addons/arcvo_agents/models/ollama_client.py`
- `odoo/addons/arcvo_agents/models/agent_orchestration.py`
- `odoo/addons/arcvo_agents/models/agent_message.py`
- `odoo/addons/arcvo_agents/views/agent_message_views.xml`
- `odoo/addons/arcvo_agents/views/employee_agent_views.xml`
- `odoo/addons/arcvo_agents/data/cron_jobs.xml`
- `docs/odoo-agent-orchestration.md` (detailed reference)
- `DEPLOYMENT_CHECKLIST.md` (validation steps)
- `QUICK_START.md` (5-min test guide)

### Removed Files
- `backend/app/hermes/` (entire directory)
- `backend/app/services/agent_runner.py`
- `backend/app/api/routes/agents.py`
- `backend/Dockerfile.hermes`
- `backend/tests/test_agent_runner.py`
- `backend/tests/test_hermes_web.py`

### Modified Files
- `backend/app/main.py` (removed hermes imports)
- `backend/app/core/config.py` (hermes fields deprecated)
- `docker-compose.yaml` (removed hermes service)
- `.env.example` (removed HERMES_* and OLLAMA_*)
- `README.md` (updated for new architecture)
- `Makefile` (removed hermes targets)
- `odoo/addons/arcvo_agents/__manifest__.py` (added dependencies, new data files)

---

## Next Evolution

**Potential future improvements** (not in scope for this refactor):

- [ ] Tool calling (agents can invoke commands beyond LLM reasoning)
- [ ] Multi-agent collaboration (agents delegating to other agents)
- [ ] Longer memory (beyond last execution logs)
- [ ] Scheduled tasks (vs. fixed 5-min cron)
- [ ] Integration with project.task workflow
- [ ] Agent market/templates (pre-built agent configurations)
