# Arcvo Agent Guide

## English

Arcvo agents are Odoo-tracked employees (`hr.employee` extended) that execute tasks autonomously using Ollama LLM reasoning.

**Key contracts:**
- Agent = `hr.employee` with `is_agent=True` + linked `user_id`
- Capabilities = Skills/permissions stored in `arcvo.agent.capability`
- Assignments = Task routing via `arcvo.agent.assignment`
- Audit = Execution history in `arcvo.agent.audit.log` + `arcvo.agent.message`

**Execution:**
- **Cron:** Every 5 min (Scheduled Action "Arcvo: Run Active Agents")
- **Manual:** Odoo UI → Agent form → "Test Agent" button

**Key files:**
- Orchestration: [odoo/addons/arcvo_agents/models/agent_orchestration.py](odoo/addons/arcvo_agents/models/agent_orchestration.py)
- Discuss integration: [models/discuss_response_engine.py](odoo/addons/arcvo_agents/models/discuss_response_engine.py)
- Ollama client: [models/ollama_client.py](odoo/addons/arcvo_agents/models/ollama_client.py)
- Data/cron config: [data/cron_jobs.xml](odoo/addons/arcvo_agents/data/cron_jobs.xml)

See [docs/odoo-agent-orchestration.md](docs/odoo-agent-orchestration.md) for detailed execution flow.

---

## Português

Este arquivo descreve o contrato atual para agentes no projeto Arcvo.

### Produto Canonico

Arcvo tem dois dominios:

- Acervo YouTube/eLearning no Odoo remoto.
- Agentes Arcvo rastreados no Odoo por meio do addon `arcvo_agents`.

Nao use os nomes antigos `agent_registry`, `autonomous_agents` ou modelos `agent.*`.
O contrato oficial usa modelos `arcvo.*`.

### Estrutura

- `backend/app/api/routes`: rotas FastAPI.
- `backend/app/services`: regras de aplicacao.
- `backend/app/integrations`: clientes externos.
- `frontend/src/features`: telas React (se criadas).
- `odoo/addons/arcvo_agents`: addon Odoo canonico.
- `odoo/frozen_addons`: addons preservados, fora do deploy ativo.

### Regras De Trabalho

- Odoo remoto `https://marcelo-m7.com`, DB `odoo19`, e o alvo oficial.
- Nao imprimir segredos de `.env` ou `.env.local`.
- Nao criar docs de fase ou promessas de autonomia sem implementacao real.
- Quando alterar agentes:
  1. Atualize models em `odoo/addons/arcvo_agents/models/`
  2. Atualize views XML em `odoo/addons/arcvo_agents/views/`
  3. Se houver integração backend: atualize `backend/app/services/agent_service.py`
  4. Execute: `make validate-arcvo-agents` e `make test`
  5. Uninstale/reinstale addon no Odoo UI

### Dados de Agente

Um agente no Arcvo é um `hr.employee` com:
- `is_agent=True`
- `user_id` (obrigatorio para Discuss)
- `ollama_model` (padrão: `gemma3:4b`)
- Capabilities associadas

Ver: [odoo/addons/arcvo_agents/models/agent.py](odoo/addons/arcvo_agents/models/agent.py)

### Execução

**Cron (automático):**
- Cron job a cada 5 min
- Busca agentes com `active=True`
- Chama `agent_orchestration.run_active_agents()`
- Registra em `arcvo.agent.audit.log` + Discuss

**Manual (teste):**
- Odoo UI → HR → Employees → Agent form
- Botão "Test Agent"
- Resultado em `arcvo.agent.message` + notificação

Ver: [docs/odoo-agent-orchestration.md](docs/odoo-agent-orchestration.md)
