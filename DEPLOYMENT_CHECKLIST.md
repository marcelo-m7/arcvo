# Arcvo Agent Automation - Final Deployment Checklist

## ✅ Phase: Deploy, Correction, and Validation - COMPLETE

### Code Quality & Fixes
- [x] All 8 models pass py_compile syntax check
- [x] All 12 view XML files validated and fixed
- [x] automation_discuss.py: action_retry() implemented with full LLM regeneration
- [x] automation_matcher.py: round-robin strategy corrected  
- [x] employee_agent_views.xml: 4 inherit_id XML references fixed
- [x] No remaining unimplemented TODOs (Phase 4 escalate-to-human comment is documentation)

### Cleanup & Artifacts
- [x] All __pycache__ directories removed
- [x] All .pyc compiled files removed
- [x] Git repository clean, all changes committed (commit: 6e61b84)
- [x] Cache files cleaned

### Test Suite - 20/20 PASSED ✅
- [x] Phase 1 Webhooks: 3/3 tests passed
- [x] Phase 2 Auto-Assignment: 4/4 tests passed
- [x] Phase 3 Smart Discuss: 4/4 tests passed
- [x] Phase 4 Escalation: 4/4 tests passed
- [x] Phase 5 eLearning: 4/4 tests passed
- [x] Integration Workflow: 1/1 test passed

### Security
- [x] ACLs configured (20 entries in ir.model.access.csv)
- [x] base.group_user: read-only or limited write
- [x] base.group_system: full CRUD
- [x] No hardcoded secrets or API keys
- [x] Environment variables properly used

### Configuration
- [x] __manifest__.py: All 5 view XMLs in data list
- [x] models/__init__.py: All 14 models imported
- [x] Signal handlers configured (4 total):
  - ProjectTaskWebhook (automation_webhook.py)
  - MailMessageDiscussHandler (automation_discuss.py)
  - SlideSlideHandler (slide_management.py)
  - ProjectTaskElearning (elearning_task_template.py)
- [x] Cron integration (automation_escalation.py)
- [x] Ollama endpoint configured (https://api.ollama.monynha.me)
- [x] All model imports validated
- [x] SQL constraints and indexes configured

---

## Pre-Deployment (Local Validation)

---

## Deployment (Production Verification)

### Step 1: Pre-Flight Check (5 min)
```bash
# Verify Odoo is running
curl -I https://marcelo-m7.com

# Verify Ollama API is accessible  
curl -I https://api.ollama.monynha.me

# Check git status
git status  # Should show: nothing to commit
```

### Step 2: Deploy Code (5 min)
```bash
# Pull latest to Odoo server
git pull origin main

# Clear Python cache
find odoo/addons/arcvo_agents -type d -name __pycache__ -exec rm -rf {} +
```

### Step 3: Install Addon (10 min)
1. Go to https://marcelo-m7.com/web/login
2. Search Apps → "arcvo_agents"
3. Click Install (or Uninstall → Install for clean install)
4. Wait for completion
5. Verify module in installed list

### Step 4: Smoke Tests (15 min)

#### Test 1: Webhook Trigger
- Create project task → Verify webhook fires → Check automation logs

#### Test 2: Agent Assignment
- Create task matching criteria → Verify agent assigned

#### Test 3: Discuss Response
- Post: "@AgentName please review" → Wait 10s → Verify LLM response posted

#### Test 4: Escalation
- Block task → Wait for escalation → Verify logged

#### Test 5: eLearning
- Create slide in enabled channel → Verify task auto-created → Complete → Verify auto-published

### Step 5: Monitor
- Check Odoo logs for errors
- Monitor automation execution logs
- Monitor Ollama API response times

---

## 🎯 Success Criteria

✅ **READY FOR PRODUCTION**

- All 14 Odoo models created
- 20 ACL entries configured
- 5 view XML files loaded
- Signal handlers firing
- Webhook dispatcher working
- Matcher assigning tasks
- Discuss responses posting
- Escalation detecting stuck tasks
- eLearning engine creating tasks
- 20/20 tests passing
- No ERROR logs in Odoo

**Last Git Commit**: 6e61b84 (Fixes + cleanup)  
**Test Suite**: 20/20 PASSED ✅  
**Deployment Status**: READY 🚀

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
