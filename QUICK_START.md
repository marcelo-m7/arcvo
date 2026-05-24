# Quick Start: Deploy and Test First Agent

Complete este guia em **5-10 minutos** para validar que agentes funcionam em produção.

## Prerequisites

- ✅ Arcvo deployed (via Coolify, commit `945c318` or later)
- ✅ Odoo instance healthy (`https://marcelo-m7.com`)
- ✅ Ollama healthy (`https://api.ollama.monynha.me/api/health` → 200)

## Step 1: Install Addon (1 min)

1. Access Odoo: `https://marcelo-m7.com`
2. **Settings** → **Apps & Modules**
3. Search: `arcvo_agents`
4. Click **Install** (if not already installed)
5. Wait for installation (should be quick)

## Step 2: Create Test Agent (2 min)

1. **HR** → **Employees**
2. Click **Create**
3. Fill in:
   - **Name**: "Test Agent"
   - **Email**: `agent@example.com`
4. Scroll down → **Agent Configuration** tab
5. Check ✓ **Is Agent**
6. Verify:
   - **Ollama Model**: `gemma3:4b` (default)
   - **Active**: ✓ (checked)
7. **Save**

### Issue: "Agent Configuration" tab missing?

The addon may not be installed yet:
- Go back to Settings → Apps → Search "arcvo_agents" → Install
- Refresh employee form (Ctrl+R)

## Step 3: Assign User to Agent (1 min)

**Important:** Agents must have a User to execute and post to Discuss.

1. Still on agent employee form
2. Scroll to **User** field
3. Either:
   - **Option A**: Click **Create User** (if not exists)
     - Set username: `agent.test`
     - Password: auto-generated
   - **Option B**: Select existing user from dropdown
4. **Save**

### Issue: User not appearing in dropdown?

Create a new user first:
- Settings → Users & Companies → Users → Create
- Set username + password
- Come back to employee and select it

## Step 4: Test Manual Execution (3 min)

1. On agent employee form, locate the **header buttons**
2. Click **🤖 Test Agent** (green button)
3. Wait 5-30 seconds (Ollama processing)

### Expected Outcome

- Notification: **"Agent Test Successful"** ✓
- **Agent Execution Logs** tab shows new entry with status **Success** ✓
- Agent's chatter (Discuss) shows message: **"🤖 Agent Execution - Test Agent"** ✓

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Agent is not configured as agent" | Ensure `Is Agent` is checked ✓ |
| "Timeout after 90s" | Ollama slow; wait 2 min, try again |
| "Ollama API error" | Check `https://api.ollama.monynha.me/api/health` |
| "No user/partner" | Assign a User to the employee |
| Button doesn't appear | Refresh form (Ctrl+R) after addon install |

## Step 5: Verify Cron Execution (5 min)

Cron job runs every **5 minutes** automatically.

1. Remain on agent employee form
2. Ensure **Active** is checked ✓ (for cron inclusion)
3. **Save**
4. **Wait 5 minutes**
5. Refresh form (Ctrl+R)
6. Check **Agent Execution Logs** tab
7. A **new entry** should appear (auto-executed by cron)

### Expected Outcome

- Status: **Success** ✓
- Time: Recent (within last 5 min) ✓
- Response visible ✓

### Disable Cron (optional)

If you want to test only manual execution:
- Uncheck **Active** ✓ (turns off cron)
- Agent won't run automatically but manual Test still works

## Step 6: Monitor Logs (1 min)

All agent executions are logged to a dedicated menu.

1. **Arcvo** → **Agent Messages** (new menu item)
2. See all executions (test + auto)
3. Click any entry to see:
   - **Prompt** sent to LLM
   - **Raw Response** from Ollama
   - **Parsed Decision** (JSON)
   - **Status** (success/error/timeout)
   - **Duration** (how long LLM took)
4. Messages are **immutable** (for audit trail)

## Success Checklist ✅

- [ ] Addon installed
- [ ] Test agent created + active
- [ ] User assigned to agent
- [ ] **🤖 Test Agent** button executed successfully
- [ ] Notification: "Agent Test Successful"
- [ ] Agent Execution Logs show success entry
- [ ] Discuss/chatter has agent response message
- [ ] Waited 5 min + cron ran automatically
- [ ] Second log entry from auto-execution visible

**If all checkboxes pass**: 🎉 **Agents working!**

---

## Next Steps

### Create Multiple Agents
Repeat Steps 2-3 for different agents (different roles, models, system prompts).

### Customize Agent Behavior
Edit agent employee form → **Agent Configuration** tab:
- **System Prompt**: Custom instructions for this agent
- **Ollama Model**: Switch to different model if available
  - Check available: `https://api.ollama.monynha.me/api/tags`

### Pause/Resume Agent
Use buttons on agent form:
- **⏸ Pause Agent**: Stop auto-execution (manual Test still works)
- **▶ Resume Agent**: Re-enable auto-execution

### View Full Documentation
See [docs/odoo-agent-orchestration.md](../docs/odoo-agent-orchestration.md) for:
- Architecture deep dive
- Advanced configuration
- Troubleshooting guide
- Performance tuning

### Deployment Validation
Use [DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md) for comprehensive production validation.

---

## Common Questions

**Q: Where do agent responses go?**
A: Two places:
1. Agent's **Discuss/chatter** channel (in employee form)
2. **Arcvo** → **Agent Messages** menu (immutable audit log)

**Q: How do I stop an agent permanently?**
A: Delete the employee record (or uncheck `Is Agent` flag).

**Q: How do I change which LLM model an agent uses?**
A: Edit agent employee → **Agent Configuration** → **Ollama Model** field.

**Q: Can agents talk to other systems?**
A: Currently Ollama only. Integration with tools is on roadmap.

**Q: What if Ollama is down?**
A: Cron continues but logs show error. Manual Test shows timeout. Fix Ollama → retry.

---

## Performance Notes

- **Cron interval**: 5 minutes (can change in `data/cron_jobs.xml`)
- **Ollama timeout**: 90 seconds (configurable in System Parameters)
- **Recommended model**: `gemma3:4b` (fast, 4B parameters)
- **First run slower**: Models load on first use (~10-30s)

---

**Still stuck?** Check [docs/odoo-agent-orchestration.md](../docs/odoo-agent-orchestration.md#troubleshooting) for detailed troubleshooting.
