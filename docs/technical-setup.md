# Arcvo Technical Setup

## Ambiente

Copie `.env.example` para `.env` e preencha os segredos reais localmente.

Odoo remoto:

- `ODOO_URL=https://marcelo-m7.com`
- `ODOO_DB=odoo19`
- `ODOO_USER`
- `ODOO_API_KEY`
- `ODOO_INTEGRATION_MODE=xmlrpc`
- `ODOO_ALLOW_SELF_SIGNED_SSL=false`

Admin local:

- `APP_SECRET_KEY`
- `APP_ADMIN_PASSWORD`
- `APP_JWT_EXPIRES_MINUTES`
- `CORS_ORIGINS=http://localhost:8010,http://127.0.0.1:8010`

Supabase:

- `SUPABASE_PROJECT_ID=wvkjainfwsyiyfcmbtid`
- `SUPABASE_URL=https://wvkjainfwsyiyfcmbtid.supabase.co`
- `SUPABASE_PUBLISHABLE_KEY`

Ollama:

- `OLLAMA_URI`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`

Endpoint validado:

- `OLLAMA_URI=https://api.ollama.monynha.me`
- `OLLAMA_MODEL=gemma3:4b`

Hermes:

- `HERMES_PROVIDER`
- `HERMES_MODEL`
- `HERMES_DASHBOARD_PORT=8010`
- `HERMES_PUBLIC_BASE_URL` vazio por padrao; quando vazio a UI usa `window.location.origin`.
- `HERMES_CORS_ORIGINS=https://hermes.marcelo-m7.com,http://localhost:8010,http://127.0.0.1:8010`

Coolify:

- `COOLIFY_HOST`
- `COOLIFY_API_KEY`
- `COOLIFY_ARCVO_WEBHOOK`

Agentes:

- `AGENT_COMMAND_ALLOWLIST`

## Desenvolvimento

```bash
make install
make dev
```

Servicos separados:

```bash
make backend
make hermes
```

## Backend

O backend fica em `backend/app`.

- `api/routes`: endpoints HTTP internos.
- `core`: configuracao e seguranca.
- `integrations/odoo`: cliente XML-RPC/JSON-RPC.
- `hermes`: agente e ferramentas para a UI padrao do Hermes.
- `services`: regras de acervo, Odoo, Supabase, agentes e deploy.
- `schemas`: contratos Pydantic.

Rotas mantidas:

- `GET /health`
- `POST /api/v1/auth/login`
- `GET /api/v1/odoo/health`
- `GET|POST|PATCH /api/v1/archive/*`
- `GET|POST /api/v1/agents/*`
- `GET|POST /api/v1/deploy/*`

## Acervo YouTube

O acervo usa modelos nativos do Odoo eLearning:

- Curso/categoria: `slide.channel`.
- Video: `slide.slide`.
- Metadados YouTube: oEmbed publico.
- Importacao Supabase: categorias viram cursos; playlists Supabase sao ignoradas.

Comandos:

```bash
make odoo-health
make import-supabase-youtube
```

## Agentes Arcvo

O addon canonico e `odoo/addons/arcvo_agents`.

Modelos:

- `arcvo.agent`
- `arcvo.agent.capability`
- `arcvo.agent.assignment`
- `arcvo.agent.audit.log`

O addon tambem estende `project.task` com:

- `arcvo_agent_id`
- `arcvo_requires_agent`
- `arcvo_assignment_ids`

Discuss e chatter:

- cada agente possui `discuss_channel_id`;
- mensagens operacionais sao postadas no Discuss do agente;
- progresso de assignments tambem aparece no chatter do assignment e da tarefa;
- auditoria fica em `arcvo.agent.audit.log`.

Use `make validate-arcvo-agents` para validar a estrutura local do addon.

## Hermes

Hermes e a mesa operacional. O codigo em `backend/app/hermes` cria um agente `ArcvoOdooOps` com ferramentas Odoo-backed.

Comando local:

```bash
make hermes
```

Ferramentas expostas:

- listar agentes;
- listar auditoria;
- atribuir tarefa;
- enviar mensagem ao Discuss de um agente;
- ler mensagens recentes do agente;
- executar agente com Ollama;
- executar pendencias;
- consultar Odoo/Coolify/Ollama.

## Coolify Odoo

A instancia Odoo no Coolify usa Docker Compose buildpack. Por isso `docker-compose.yaml` deve permanecer na raiz do repositorio. O servico Odoo usa `odoo/Dockerfile` para copiar `./odoo/addons` para `/mnt/extra-addons` dentro da imagem.

## Validacao

```bash
make validate-arcvo-agents
make lint
make test
make ollama-health
make odoo-health
```

Checks esperados:

- Ruff no backend.
- Pytest no backend.
- Validador local do addon `arcvo_agents`.
- Healthcheck Odoo remoto autenticado.

## Seguranca

- Nunca commitar `.env`, `.env.local`, `.venv`, caches, logs ou build artifacts.
- Nao registrar `ODOO_API_KEY`, `APP_ADMIN_PASSWORD`, JWTs ou chaves Supabase em logs.
- Segredos nao entram em prompts, respostas Hermes, mensagens Discuss ou auditoria.
- `SUDO_PASSWORD`, quando existir localmente, e usado apenas para manutencao do WSL e nunca deve entrar em logs, prompts ou commits.
