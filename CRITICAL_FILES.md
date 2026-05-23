# Critical Files Guide

**Quick reference for Arcvo's autonomous agent system**

## 📚 Essential Documentation

### Start Here
1. **[README.md](README.md)** - Project overview + quick start
2. **[AGENTS.md](AGENTS.md)** - Agent organization structure (210+ lines)

### Architecture & Design
3. **[PHASE3_COMPLETION_REPORT.md](PHASE3_COMPLETION_REPORT.md)** - What was built this session
4. **[PHASE3_ROADMAP.md](PHASE3_ROADMAP.md)** - 5-phase evolution plan
5. **`.github/copilot-instructions.md`** - Code conventions & standards
6. **`docs/technical-setup.md`** - Low-level setup details

### Deployment & Validation
7. **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Step-by-step validation

## 💾 Core Implementation Files

### Odoo Agent Registry Addon
```
odoo/addons/agent_registry/
├── __manifest__.py                  - Addon metadata
├── __init__.py                      - Module loader
├── models/agent.py                  - 4 ORM models (agent, capability, assignment, audit_log)
├── views/
│   ├── agent_capability_views.xml   - Capability UI
│   ├── agent_views.xml              - Agent UI (Kanban-ready)
│   ├── agent_assignment_views.xml   - Task assignment UI
│   └── agent_audit_log_views.xml    - Audit log viewer
├── security/ir.model.access.csv     - ACL permissions
├── data/
│   ├── agent_capabilities_demo.xml  - 10 predefined capabilities
│   └── agent_demo.xml               - 7 demo agents
```

**Key Model Fields:**
- `agent.agent`: id, name, agent_type, status, api_key, current_workload, max_concurrent_tasks, last_heartbeat, is_available (computed)
- `agent.capability`: id, name, description, category
- `agent.assignment`: id, agent_id, task_id, status (assigned→claimed→in_progress→completed), progress_percentage, timestamps
- `agent.audit_log`: id, agent_id, task_id, action_type, action_details (JSON), status_code, timestamp, error_msg (all readonly)

### Backend Agent APIs
```
backend/app/api/routes/agents.py        - 8 FastAPI endpoints (400+ lines)
```

**Endpoints:**
- `GET /api/v1/agents/agents` - List all agents
- `GET /api/v1/agents/agents/{id}` - Get agent details
- `POST /api/v1/agents/agents/heartbeat` - Heartbeat (keep-alive)
- `GET /api/v1/agents/tasks/me/pending` - Discover tasks
- `POST /api/v1/agents/tasks/{id}/claim` - Claim task
- `POST /api/v1/agents/tasks/{id}/report` - Report progress
- `POST /api/v1/agents/tasks/{id}/complete` - Complete task
- `GET /api/v1/agents/audit/{id}` - Audit logs

### Backend Integration
```
backend/app/main.py                 - FastAPI app (UPDATED - agents router registered)
```

## 🔑 Key Patterns

### Agent Registration
1. Agent creates record in `agent.agent` with capabilities
2. Stores `api_key` (auto-generated via `secrets.token_urlsafe(32)`)
3. Sets `max_concurrent_tasks` (default 3-5)
4. Initial status: "available"

### Heartbeat Loop
```
Agent → POST /agents/heartbeat
     ← updates last_heartbeat
     ← sets status
     ← creates audit log entry
```

### Task Lifecycle
```
Task Created
  → Task Router queries agent capabilities
  → Finds best-fit agent (exact match → workload → success rate)
  → Auto-creates assignment record
  → Agent polling finds pending tasks
  → Agent claims: POST /tasks/{id}/claim
    → workload += 1
    → assignment.status = "claimed"
    → audit logged
  → Agent works...
    → reports progress: POST /tasks/{id}/report
  → Task complete: POST /tasks/{id}/complete
    → workload -= 1
    → assignment.status = "completed"
    → result stored
    → audit logged
```

### Workload Management
```python
# Check if agent can take work
is_available = (
    agent.status == "available" AND
    agent.current_workload < agent.max_concurrent_tasks
)

# Increment on claim
agent.current_workload += 1

# Decrement on complete
agent.current_workload = max(0, agent.current_workload - 1)
```

## 📊 Demo Data

### 7 Demo Agents
1. CEO Agent (orchestrator) - Delegating, decision-making
2. Project Manager (executor) - Status reports, planning
3. Backend Dev (executor) - Backend development
4. Frontend Dev (executor) - Frontend development
5. DevOps Agent (executor) - Infrastructure
6. QA Agent (executor) - Testing
7. Docs Agent (executor) - Documentation

### 10 Demo Capabilities
1. backend_dev - Backend development
2. frontend_dev - Frontend development
3. odoo_dev - Odoo extension development
4. devops - Infrastructure & deployment
5. database_admin - Database administration
6. project_management - Project coordination
7. product_management - Product strategy
8. qa_testing - Quality assurance
9. code_review - Code review & standards
10. documentation - Technical documentation

## 🚀 Quick Commands

```bash
# Validate
make tools-check        # System dependencies
make odoo-health        # Odoo connectivity
make test               # Backend tests
make lint               # Code style

# Develop
make dev                # Frontend + Backend
make backend            # Backend only
make frontend           # Frontend only

# Deploy
make docker-up          # Start Odoo + PostgreSQL
make docker-down        # Stop containers

# Format
make format             # Auto-format code
```

## 🔍 API Test Examples

### List agents
```bash
curl http://localhost:8000/api/v1/agents/agents
```

### Agent heartbeat
```bash
curl -X POST http://localhost:8000/api/v1/agents/agents/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"agent_id": 1, "status": "available"}'
```

### Query audit logs
```bash
curl http://localhost:8000/api/v1/agents/audit/1?limit=10
```

## 🎯 Success Criteria Checklist

- [ ] Odoo addon installs without errors
- [ ] 7 demo agents appear in Odoo UI
- [ ] FastAPI shows 8 agent endpoints in Swagger
- [ ] Agent heartbeat API succeeds (200)
- [ ] Workload tracked on task claim/complete
- [ ] Audit logs show all actions with timestamps
- [ ] Task Router auto-assigns to suitable agent
- [ ] Agent can claim task and report progress

## 📖 File Organization

```
Arcvo/
├── README.md                        ← Start here
├── AGENTS.md                        ← Agent organization
├── PHASE3_COMPLETION_REPORT.md      ← What was built
├── PHASE3_ROADMAP.md                ← Next phases
├── DEPLOYMENT_CHECKLIST.md          ← Validation steps
├── CRITICAL_FILES.md                ← This file
│
├── backend/
│   ├── app/
│   │   ├── main.py                  ← FastAPI app
│   │   ├── api/routes/
│   │   │   ├── agents.py            ← NEW: Agent APIs
│   │   │   ├── archive.py           ← Archive
│   │   │   ├── auth.py              ← Authentication
│   │   │   ├── health.py            ← Health check
│   │   │   └── odoo.py              ← Odoo integration
│   │   ├── integrations/
│   │   │   └── odoo/client.py       ← XML-RPC client
│   │   └── services/
│   │       ├── archive_service.py
│   │       └── odoo_service.py
│   └── tests/                       ← Unit tests (12/12 passing)
│
├── frontend/
│   ├── src/
│   │   ├── features/
│   │   │   ├── archive/
│   │   │   ├── auth/
│   │   │   └── odoo/
│   │   ├── store/                   ← Zustand state
│   │   ├── lib/api.ts               ← API client
│   │   └── app/App.tsx              ← Root component
│
├── odoo/
│   ├── addons/
│   │   ├── agent_registry/          ← NEW: Agent system
│   │   │   ├── models/
│   │   │   ├── views/
│   │   │   ├── security/
│   │   │   └── data/
│   │   ├── my_addom/                ← Legacy addon
│   │   └── sc_react_theme/          ← Theme
│
├── .github/
│   └── copilot-instructions.md      ← Code standards
│
├── docs/
│   └── technical-setup.md           ← Setup details
│
├── docker-compose.yaml              ← Odoo + PostgreSQL
├── Makefile                         ← Build automation
└── .env                             ← Configuration (not tracked)
```

## 🔗 Next Phase Checklist

**Before Phase 3B:**
- [ ] Review AGENTS.md
- [ ] Review PHASE3_COMPLETION_REPORT.md
- [ ] Read DEPLOYMENT_CHECKLIST.md
- [ ] Understand agent API patterns
- [ ] Understand Task Router algorithm

**Phase 3B First Steps:**
- [ ] `make docker-up` → start Odoo
- [ ] Verify addon installed
- [ ] Run API smoke tests
- [ ] Begin project.task extension

---

**Last Updated:** 2026-05-23  
**Context:** Phase 3A Complete, Phase 3B Ready
