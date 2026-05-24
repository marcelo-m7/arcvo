# Integração Odoo ↔ Ollama para Agentes Arcvo

## Visão Geral
Os agentes Arcvo (modelos `arcvo.agent.*` no Odoo) executam tarefas usando Ollama como backend de LLM para raciocínio e decisão.

## Fluxo de Execução

```
Odoo (arcvo_agents addon)
  ↓
Backend FastAPI (agent_runner.py)
  ↓
OllamaClient (integrations/ollama.py)
  ↓
Ollama API (https://api.ollama.monynha.me)
  ↓
Resposta LLM (gemma3:4b por padrão)
```

## Componentes

### 1. Odoo Side (arcvo_agents addon)
- **Modelos**: `arcvo.agent`, `arcvo.agent.assignment`, `arcvo.agent.audit.log`
- **Métodos RPC**:
  - `action_heartbeat()` — registra heartbeat do agente
  - `action_apply_progress()` — atualiza status/progresso da atribuição
  - `action_post_discuss_message()` — grava mensagens em Discuss do agente

### 2. Backend Services
- **agent_runner.py**: orquestra execução de agentes via Ollama
  - `run_pending()` — processa atribuições pendentes
  - `run_agent(agent_id)` — executa agente específico
  - `chat(agent_id, message)` — chat síncrono com agente via Ollama

- **agent_service.py**: leitura de agentes e auditoria do Odoo

### 3. Ollama Integration
- **OllamaClient** (integrations/ollama.py): cliente HTTP para Ollama
  - `health()` — verifica disponibilidade
  - `generate(prompt)` — solicita geração de texto

### 4. Hermes Dashboard
- Web UI para gerenciamento de agentes
- Expõe ArcvoHermesTools para acesso a agent_runner via Hermes SDK
- Roda no serviço `hermes` do docker-compose (porta 8010)

## Variáveis de Ambiente Necessárias

### Odoo Connection
```bash
ODOO_URL=https://marcelo-m7.com
ODOO_DB=odoo19
ODOO_USER=mail@marcelo-m7.com
ODOO_API_KEY=<seu-chave-api>
ODOO_ALLOW_SELF_SIGNED_SSL=true
```

### Ollama Configuration
```bash
OLLAMA_URI=https://api.ollama.monynha.me
OLLAMA_MODEL=gemma3:4b
OLLAMA_TIMEOUT_SECONDS=90
OLLAMA_UI_SENHA=monynha.com  # Password if Ollama requires auth
```

### Hermes Dashboard
```bash
HERMES_DASHBOARD_ENABLED=true
HERMES_DASHBOARD_PORT=8010
HERMES_PUBLIC_BASE_URL=https://hermes.marcelo-m7.com  # Empty uses window.location.origin
HERMES_CORS_ORIGINS=https://hermes.marcelo-m7.com,http://localhost:8010,http://127.0.0.1:8010
HERMES_PROVIDER=gemini
HERMES_MODEL=gemini-2.0-flash
GEMINI_API_KEY=<seu-chave-gemini>
```

## Docker Compose Configuration

O serviço `hermes` deve receber todas as variáveis acima no bloco `environment`:

```yaml
  hermes:
    build:
      context: .
      dockerfile: backend/Dockerfile.hermes
    environment:
      - ODOO_URL
      - ODOO_DB
      - ODOO_USER
      - ODOO_API_KEY
      - ODOO_ALLOW_SELF_SIGNED_SSL=true
      - OLLAMA_URI
      - OLLAMA_MODEL
      - OLLAMA_TIMEOUT_SECONDS=${OLLAMA_TIMEOUT_SECONDS:-90}
      - OLLAMA_UI_SENHA=${OLLAMA_UI_SENHA:-}
      - HERMES_DASHBOARD_ENABLED=true
      - HERMES_DASHBOARD_PORT=8010
      - HERMES_PUBLIC_BASE_URL=${HERMES_PUBLIC_BASE_URL:-}
      - HERMES_CORS_ORIGINS=...
      - HERMES_PROVIDER=gemini
      - HERMES_MODEL=gemini-2.0-flash
      - GEMINI_API_KEY
```

## Validação Local

```bash
# 1. Verificar conectividade Odoo
make odoo-health

# 2. Verificar conectividade Ollama
make ollama-health

# 3. Testar chat de agente (executa Ollama + grava em Discuss no Odoo)
cd backend && uv run python -c "import asyncio; from app.services.agent_runner import get_agent_runner; print(asyncio.run(get_agent_runner().chat(agent_id=4, message='test')))"

# 4. Validar que addon Odoo tem modelos esperados
make validate-arcvo-agents
```

## Troubleshooting

### Agente não encontrado
- Confirmar que agente existe em Odoo (modelo `arcvo.agent`)
- Verificar permissões de usuário em `ODOO_USER`

### Timeout durante geração Ollama
- Pode acontecer em primeiro uso (modelo carregando)
- Aumentar `OLLAMA_TIMEOUT_SECONDS` se necessário
- Verificar conectividade em `OLLAMA_URI`

### Mensagens não aparecem em Discuss
- Confirmar que agente tem `discuss_channel_id` preenchido
- Verificar ACL de `mail.message` no Odoo
- Confirmar método RPC `action_post_discuss_message` está disponível

### Docker Compose falha ao iniciar Hermes
- Garantir todas as variáveis de env estão no `.env`
- Verificar logs: `docker logs <container_id>`
- Validar sintaxe YAML do docker-compose
