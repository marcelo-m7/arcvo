# Quick Validation Checklist - Agent Registry Deployment

Complete these steps in order to validate Phase 3A implementation.

## 📋 Pre-Deployment Checklist

### 1. Code Validation ✅ (Already Done)
- [x] `agents.py` module compiles without errors
- [x] FastAPI app initializes with 8 agent endpoints
- [x] Backend tests still pass (12/12)
- [x] No import errors

### 2. Docker Deployment (DO THIS NEXT)

```bash
# Start Docker stack
make docker-up

# Wait for Odoo to start (check http://localhost:8069)
# Default credentials: admin / admin

# Check Odoo logs for addon errors
docker-compose logs -f odoo
```

**Expected output:**
```
odoo  | 2026-05-23 XX:XX:XX,XXX INFO odoo.modules.loading: Loaded modules
odoo  | 2026-05-23 XX:XX:XX,XXX INFO odoo.modules.loading: Modules to load: ['agent_registry']
```

### 3. Odoo UI Verification

1. Login to Odoo at http://localhost:8069
2. Go to **Agents** menu (sidebar → should see new menu item)
3. Verify you can see:
   - **Capabilities** submenu - 10 capabilities listed
   - **Agents** submenu - 7 demo agents
   - **Assignments** submenu - empty (no tasks yet)
   - **Audit Logs** submenu - empty initially

### 4. Backend API Testing

```bash
# In another terminal, start backend
cd backend
make dev
# Or: .venv/Scripts/python.exe -m uvicorn app.main:app --reload

# In browser, go to http://localhost:8000/docs
# You should see:
#   - GET /api/v1/agents/agents
#   - GET /api/v1/agents/agents/{agent_id}
#   - etc. (8 endpoints total)
```

### 5. API Smoke Test

```bash
# Test agent list endpoint
curl -X GET "http://localhost:8000/api/v1/agents/agents" \
  -H "accept: application/json"

# Expected response (if agents created in Odoo):
# [
#   {
#     "id": 1,
#     "name": "CEO Agent",
#     "agent_type": "orchestrator",
#     "status": "available",
#     ...
#   }
# ]
```

### 6. Heartbeat Test

```bash
# Agent sends heartbeat
curl -X POST "http://localhost:8000/api/v1/agents/agents/heartbeat" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": 1, "status": "available"}'

# Expected: {"status": "ok", "message": "Heartbeat recorded"}

# Verify in Odoo that last_heartbeat was updated
```

### 7. Audit Trail Check

```bash
# Query audit logs
curl -X GET "http://localhost:8000/api/v1/agents/audit/1" \
  -H "accept: application/json"

# Expected: List of audit entries with heartbeat + other actions
```

## ✅ Success Criteria

All tests pass if:

- [ ] Docker Odoo starts without errors
- [ ] agent_registry addon installed successfully
- [ ] 7 demo agents appear in Odoo UI
- [ ] 10 capabilities visible in Capabilities list
- [ ] FastAPI server starts with 8 agent endpoints
- [ ] Swagger UI shows all agent endpoints
- [ ] GET /agents returns list of agents (non-empty)
- [ ] POST /agents/heartbeat succeeds (status 200)
- [ ] Audit logs show heartbeat action

## 🔧 Troubleshooting

### Addon doesn't appear in Odoo

**Check:**
1. Volume mount: `docker-compose ps` shows `-v` for odoo/addons
2. Addon path: `docker exec arcvo_odoo ls /mnt/extra-addons/agent_registry/`
3. Odoo logs: Look for "agent_registry" in load messages

**Fix:**
```bash
# Reinstall addon
# Go to Apps → search "agent_registry" → Install
```

### FastAPI shows 502 errors

**Check:**
1. Odoo running: `curl http://localhost:8069` should respond
2. Credentials: Check .env has ODOO_URL, ODOO_USER, ODOO_API_KEY
3. Auth: `make odoo-health` should pass

**Fix:**
```bash
make odoo-health  # Tests XML-RPC connectivity
```

### Agent endpoints not showing in Swagger

**Check:**
```bash
cd backend
.venv\Scripts\python.exe -c "from app.main import app; print([r.path for r in app.routes if 'agents' in r.path])"
```

Should print 8 agent endpoints.

**Fix:** Restart backend server

## 📊 Expected File Structure After Deployment

```
odoo/addons/agent_registry/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── agent.py (4 models defined)
├── views/
│   ├── agent_*.xml (4 view files)
├── security/
│   └── ir.model.access.csv
└── data/
    ├── agent_capabilities_demo.xml
    └── agent_demo.xml

backend/app/api/routes/
├── agents.py (NEW - 400+ lines)
└── [other existing routes]

backend/app/main.py (UPDATED)
```

---

## 🚀 Next Steps After Validation

1. ✅ Phase 3B-1: Task Router implementation
2. ✅ Phase 3B-2: Extend project.task with agent fields
3. ✅ Phase 3C: First production agent (BackendAgent)

**Estimated time:** 2-4 hours for full validation + next phase
