# Arcvo Agent Orchestration in Odoo

## Overview

Agents in Arcvo are now **entirely orchestrated within Odoo** using the `arcvo_agents` addon. Each agent is represented as an `hr.employee` record with `is_agent=True`, and all LLM decisions and actions are executed via Python directly in the addon.

This replaces the previous Hermes dashboard architecture. The flow is now:

```
Odoo (hr.employee with is_agent=True)
  ↓
  Cron Job (_cron_run_active_agents) or Manual Action
  ↓
  OllamaClient (Python in addon)
  ↓
  Ollama API (https://api.ollama.monynha.me)
  ↓
  LLM Response (gemma3:4b)
  ↓
  Parse & Log to arcvo.agent.message
  ↓
  Post to Employee's Discuss Channel
```

## Agent Registration

### Creating an Agent Employee

1. Go to **Odoo** → **Employees**
2. Create a new employee record
3. In the **Agent Configuration** tab:
   - Check **Is Agent** ✓
   - (Optional) Customize **Ollama Model** (default: `gemma3:4b`)
   - (Optional) Set **System Prompt** — instructions for this specific agent
   - Check **Active** to enable cron execution

### Example System Prompt

```
You are a project assistant in Odoo. Your role is to:
1. Monitor assigned tasks
2. Summarize progress daily
3. Alert on blockers

Respond ONLY with JSON:
{
    "summary": "Brief status",
    "status": "success or pending",
    "progress": 0-100,
    "command": "Optional action"
}
```

## Execution Modes

### 1. Automatic (Cron Job)

The cron job **"Arcvo: Run Active Agents"** runs every **5 minutes** and:
- Finds all employees with `is_agent=True` and `agent_active=True`
- Executes `_execute_agent_cycle()` for each
- Logs results to `arcvo.agent.message`
- Posts responses to the agent's Discuss channel

To **pause** an agent: Click the **⏸ Pause Agent** button on the employee form.  
To **resume**: Click **▶ Resume Agent**.

### 2. Manual Testing

On any agent employee form:
- Click **🤖 Test Agent** → Executes once immediately
- Sends a test prompt to Ollama
- Posts response to Discuss
- Logs result to Agent Messages

## Data Models

### `arcvo.agent.message` — Agent Execution Log

Stores every decision and action:

| Field | Type | Purpose |
|-------|------|---------|
| `agent_id` | M2O (hr.employee) | Which agent executed |
| `prompt` | Text | Input prompt sent to LLM |
| `raw_response` | Text | Raw text from Ollama |
| `decision` | JSON | Parsed structured decision |
| `status` | Selection | success / error / timeout / etc |
| `llm_duration_seconds` | Float | How long Ollama took |
| `create_date` | Datetime | When logged |
| `discuss_message_id` | M2O (mail.message) | If posted to Discuss |

### Extension to `hr.employee`

| Field | Type | Purpose |
|-------|------|---------|
| `is_agent` | Boolean | Enable agent mode |
| `agent_status` | Selection | idle / running / error / paused |
| `agent_active` | Boolean | Include in cron execution |
| `agent_last_execution` | Datetime | When agent last ran |
| `agent_last_error` | Text | Most recent error |
| `ollama_model` | Char | Model to use (e.g., `gemma3:4b`) |
| `ollama_system_prompt` | Text | Custom instructions |
| `agent_message_ids` | O2M (arcvo.agent.message) | Execution logs |

## Configuration

### Ollama Connection

Configuration is stored in Odoo **Settings** → **System Parameters**:

| Parameter | Example | Purpose |
|-----------|---------|---------|
| `arcvo.ollama_uri` | `https://api.ollama.monynha.me` | Ollama API base URL |
| `arcvo.ollama_timeout_seconds` | `90` | Request timeout |
| `arcvo.ollama_password` | (empty) | Auth password if needed |

### Default Values

```python
ollama_uri = "https://api.ollama.monynha.me"
ollama_timeout = 90 seconds
ollama_model per agent = "gemma3:4b"
cron interval = 5 minutes
```

## API in Addon

### Core Methods on `HrEmployeeAgent` (inherits `hr.employee`)

#### `action_test_agent()`
Manual test execution. Posts result to Discuss.

#### `action_pause_agent()`
Set `agent_active = False` (stops cron execution).

#### `action_resume_agent()`
Set `agent_active = True` (allows cron execution).

#### `_execute_agent_cycle()`
Full execution cycle:
1. Build prompt
2. Call Ollama
3. Parse decision
4. Log to arcvo.agent.message
5. Post to Discuss

#### `_run_ollama_generation(prompt: str) → str`
HTTP call to Ollama. Handles health check, timeout, auth.

#### `_post_to_discuss(subject: str, body: str)`
Post message to agent's Discuss channel (chatter).

#### `_build_agent_prompt() → str`
Construct LLM prompt. Uses `ollama_system_prompt` if set, else generic template.

### Cron Job

#### `_cron_run_active_agents()`
Scheduled every 5 minutes. Finds active agents and runs cycles.

```python
# Finds employees where:
#   is_agent = True
#   agent_active = True
#   user_id != None
# Calls _execute_agent_cycle() for each
```

### OllamaClient (in `models/ollama_client.py`)

Standalone HTTP client for Ollama:

```python
from models.ollama_client import OllamaClient

client = OllamaClient(
    base_url="https://api.ollama.monynha.me",
    model="gemma3:4b",
    timeout=90,
)

# Health check
healthy = client.health()  # Returns bool

# List models
models = client.list_models()  # Returns list[str]

# Generate text
response = client.generate(prompt="Hello")  # Returns str

# Extract JSON from response
decision = client.extract_json_from_text(response)  # Returns dict or None
```

## Discuss Integration

### Automatic Posting

Each time an agent runs successfully, it posts to its **employee's Discuss channel**:

```
[Agent Name] - Agent Execution
============================
Decision: [Brief summary of LLM decision]

Full Response:
[Raw LLM output]
```

### Prerequisites

- Employee must have a **User** account (`user_id` set)
- User must have an active **Partner** record
- Discuss/Mail module must be installed

## Troubleshooting

### Agent won't run

**Check:**
1. `is_agent` = True on employee
2. `agent_active` = True on employee
3. Employee has a **User** assigned
4. Cron job "Arcvo: Run Active Agents" is **Active**

**View logs:**
- Go to employee form → **Agent Execution Logs** tab
- Click on recent message log entry → view **Parsed Decision** and error details

### Ollama timeout

**Symptom:** `arcvo.agent.message` with status=`timeout`

**Fix:**
1. Check Ollama health: Visit `https://api.ollama.monynha.me/api/health`
2. Increase timeout: Settings → System Parameters → `arcvo.ollama_timeout_seconds` = `180`
3. Check model size: `gemma3:4b` is recommended; larger models may timeout

### Messages not posting to Discuss

**Symptom:** Agent runs successfully but no message appears in employee chatter

**Check:**
1. Employee has a **User** with an active **Partner**
2. Check Odoo logs for mail module errors
3. Manually post to discuss: Test the employee's discuss integration separately

## Examples

### Simple Status Reporter Agent

```yaml
System Prompt:
"Report the current task status. Respond with JSON:
{
    'summary': 'Brief status',
    'status': 'success',
    'progress': 50,
    'command': 'continue'
}"
```

### Project Daily Summary Agent

```yaml
System Prompt:
"Summarize today's project activity (tasks completed, blockers, next steps).
Respond with JSON:
{
    'summary': 'Daily report',
    'status': 'success',
    'progress': 100,
    'command': 'email-report'
}"
```

## Migration from Hermes

**Changes from previous architecture:**

| Previous | Now |
|----------|-----|
| Hermes web dashboard | Odoo employee form |
| Separate `arcvo.agent` model | `hr.employee` with `is_agent=True` |
| Backend FastAPI orchestration | Addon Python orchestration |
| Manual API calls from frontend | Cron job + manual actions in Odoo |
| CORS setup for frontend → backend | Direct addon → Ollama calls |

**No more:**
- Hermes service in docker-compose
- Backend agent_runner service
- Environment variables `HERMES_*`
- Separate agent registry outside Odoo

## Environment Variables (Still Used)

None specific to agents now. Ollama config is in Odoo **Settings** → **System Parameters**.

To set defaults during module install, use `data/` XML files or initialization hooks.

## Performance Considerations

- **Cron interval:** 5 minutes (adjustable in `data/cron_jobs.xml`)
- **Timeout:** 90 seconds (configurable in System Parameters)
- **Model:** `gemma3:4b` recommended (4B parameters, fast)
- **Concurrency:** Cron runs sequentially per agent; no parallel execution
- **Logging:** Each run creates 1 `arcvo.agent.message` record

## Next Steps

1. ✅ Create an employee and mark `is_agent=True`
2. ✅ Click **🤖 Test Agent** to verify Ollama connectivity
3. ✅ Check **Agent Execution Logs** tab for results
4. ✅ Set `agent_active=True` to enable cron
5. ✅ Monitor **Agent Messages** menu for all execution logs
