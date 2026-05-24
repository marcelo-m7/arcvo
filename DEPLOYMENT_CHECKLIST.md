# Deployment Checklist for Arcvo Agent Refactor

## Pre-Deployment (Local Validation)

### Code Quality
- [ ] Run `make lint` — no ruff errors
- [ ] Run `make test` — all tests passing
- [ ] Run `make validate-arcvo-agents` — addon validation passes
- [ ] Backend imports clean (no Hermes references)

### Addon Validation
- [ ] Python syntax correct in all addon files
- [ ] XML views valid for Odoo 19
- [ ] Model dependencies correct (`hr` addon required)
- [ ] ACL configured in `security/ir.model.access.csv`
- [ ] Cron job registered in `data/cron_jobs.xml`

### Backend Simplification
- [ ] Verify `backend/app/hermes/` deleted
- [ ] Verify `backend/app/services/agent_runner.py` deleted
- [ ] Verify `backend/app/api/routes/agents.py` deleted
- [ ] Verify `backend/Dockerfile.hermes` deleted
- [ ] Backend still runs: `make backend` starts without errors

### Environment Cleanup
- [ ] `.env.example` updated (no HERMES_* variables)
- [ ] `docker-compose.yaml` updated (no hermes service)
- [ ] No Hermes imports in any config files

### Documentation
- [ ] [docs/odoo-agent-orchestration.md](docs/odoo-agent-orchestration.md) created
- [ ] README.md updated (references to Hermes removed)
- [ ] Makefile updated (hermes targets removed)

---

## Deployment (Production Verification)

### Docker Compose
- [ ] `docker-compose.yaml` has only: hermes → **REMOVED** ✓
- [ ] Services: `odoo`, `postgresql` present
- [ ] Volumes correct for Odoo data
- [ ] No hanging references to Hermes service

### Coolify Deployment
- [ ] Commit `6aa1373` visible in repo history
- [ ] Coolify automatically triggered deployment on push
- [ ] Container build logs show no Dockerfile.hermes errors
- [ ] Odoo service healthy (`http://<server>:8069` responds)
- [ ] PostgreSQL service healthy

### Odoo Instance (`https://marcelo-m7.com`)

#### Addon Installation
- [ ] Navigate to **Settings** → **Apps & Modules**
- [ ] Search for `arcvo_agents`
- [ ] If not installed, click **Install**
- [ ] Check for installation errors in logs

#### Agent Model Verification
- [ ] New model `arcvo.agent.message` appears in Settings → Models
- [ ] `hr.employee` has new fields:
  - [ ] `is_agent` (Boolean)
  - [ ] `agent_status` (Selection)
  - [ ] `agent_active` (Boolean)
  - [ ] `agent_last_execution` (Datetime)
  - [ ] `ollama_model` (Char)
  - [ ] `ollama_system_prompt` (Text)
  - [ ] `agent_message_ids` (One2many)

#### Cron Job Registration
- [ ] Settings → Automation → Scheduled Actions
- [ ] **"Arcvo: Run Active Agents"** present
- [ ] Interval: 5 minutes
- [ ] Active: Yes
- [ ] No errors in last execution

#### Create Test Agent
1. **Employees** → **New**
   - [ ] Name: "Test Agent"
   - [ ] Check **Is Agent** ✓
   - [ ] Set **Ollama Model**: `gemma3:4b`
   - [ ] Save
   - [ ] A **User** must be assigned (create if needed)

2. **Test Manual Execution**
   - [ ] Click **🤖 Test Agent** button
   - [ ] Wait for execution (should take ~5-30s)
   - [ ] Notification appears: "Agent Test Successful"
   - [ ] Check **Agent Execution Logs** tab
   - [ ] Latest log shows status: **Success**
   - [ ] Response text visible in log details

3. **Verify Discuss Integration**
   - [ ] Agent employee's chatter shows recent post
   - [ ] Post title: "🤖 Agent Execution - Test Agent"
   - [ ] Post contains LLM response

#### Enable Cron Execution
- [ ] On agent employee, check **Active** ✓
- [ ] Wait 5 minutes
- [ ] Check **Agent Execution Logs** again
- [ ] New log entry should appear (automatic execution)

#### Ollama Connectivity
- [ ] Settings → System Parameters
- [ ] Verify `arcvo.ollama_uri` = `https://api.ollama.monynha.me`
- [ ] Health check: 
  ```bash
  curl -s https://api.ollama.monynha.me/api/health
  # Should return 200 OK
  ```

### Backend Health (Optional)
- [ ] `GET /health` responds 200
- [ ] `GET /api/v1/odoo/health` responds 200
- [ ] `GET /api/v1/archive/*` still works
- [ ] No 500 errors for removed agent endpoints

---

## Rollback Plan

If deployment issues occur:

1. **Revert commit:**
   ```bash
   git revert 6aa1373
   git push origin main
   ```

2. **Or restore from backup:**
   - Coolify has automatic backups
   - Restore previous Odoo database from PostgreSQL backup

3. **Check logs:**
   - Odoo logs: `/var/lib/odoo/odoo.log`
   - PostgreSQL logs: `docker logs <postgres_container>`
   - Addon errors usually visible in Odoo web UI → Settings → Logs

---

## Success Criteria

✅ All checks above pass

✅ Test agent successfully runs via manual action

✅ Test agent automatically executes via cron (5 min interval)

✅ Logs appear in Agent Messages menu

✅ Responses posted to Discuss channel

✅ No errors in Odoo logs related to addon

✅ Backend still healthy (archive, health endpoints work)

---

## Post-Deployment (Monitoring)

### Daily Monitoring
- [ ] Check **Agent Messages** menu for errors
- [ ] Monitor cron job last execution time (should be recent)
- [ ] Check agent employee **agent_status** field (should be "idle" or "running")

### Weekly Monitoring
- [ ] Review agent execution logs for patterns
- [ ] Check Ollama health: `curl https://api.ollama.monynha.me/api/health`
- [ ] Monitor Odoo database size (agent messages grow daily)

### Performance Considerations
- [ ] Agent messages clean up policy (consider archiving old >30d)
- [ ] Cron job duration (should complete in <5min)
- [ ] Ollama timeout (current: 90s, can adjust per performance)

---

## Reference Files

- **Addon Implementation**: [odoo/addons/arcvo_agents/](../odoo/addons/arcvo_agents/)
- **Agent Orchestration Guide**: [docs/odoo-agent-orchestration.md](odoo-agent-orchestration.md)
- **Commit**: `6aa1373` — full refactor details
- **Deprecated**: Hermes dashboard, backend agent_runner service

---

## Questions?

See [docs/odoo-agent-orchestration.md](odoo-agent-orchestration.md) for:
- Architecture overview
- API reference
- Troubleshooting guide
- Example agent configurations
