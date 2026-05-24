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
- `CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`

Supabase:

- `SUPABASE_PROJECT_ID=wvkjainfwsyiyfcmbtid`
- `SUPABASE_URL=https://wvkjainfwsyiyfcmbtid.supabase.co`
- `SUPABASE_PUBLISHABLE_KEY`

Ollama:

- `OLLAMA_URI`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`

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
make frontend
```

## Backend

O backend fica em `backend/app`.

- `api/routes`: endpoints HTTP.
- `core`: configuracao e seguranca.
- `integrations/odoo`: cliente XML-RPC/JSON-RPC.
- `services`: regras de acervo, Odoo, Supabase e agentes.
- `schemas`: contratos Pydantic.

Rotas mantidas:

- `GET /health`
- `POST /api/v1/auth/login`
- `GET /api/v1/odoo/health`
- `GET|POST|PATCH /api/v1/archive/*`
- `GET|POST|PATCH /api/v1/odoo/models/*`
- `GET|POST /api/v1/agents/*`

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

Use `make validate-arcvo-agents` para validar a estrutura local do addon.

O backend executa agentes por `arcvo.agent.assignment`: busca a tarefa, chama Ollama,
executa apenas comandos presentes em `AGENT_COMMAND_ALLOWLIST` e registra tudo em
`arcvo.agent.audit.log`. Odoo permanece como fonte de verdade.

## Frontend

O frontend fica em `frontend`.

- `/acervo`: dashboard e envio de videos.
- `/agentes`: agentes, heartbeat, vinculo de tarefa e auditoria.
- `/producao`: status do repositorio, Ollama, Coolify e webhook manual de deploy.
- `/odoo`: healthcheck e diagnostico Odoo.

Configure `VITE_API_BASE_URL=http://localhost:8000` em desenvolvimento.

## Validacao

```bash
make lint
make test
```

Checks esperados:

- Ruff no backend.
- Pytest no backend.
- ESLint, TypeScript e build no frontend.

## Seguranca

- Nunca commitar `.env`, `.env.local`, `.venv`, caches, logs ou build artifacts.
- Nao registrar `ODOO_API_KEY`, `APP_ADMIN_PASSWORD`, JWTs ou chaves Supabase em logs.
- `sc_react_theme` esta congelado em `odoo/frozen_addons` e fora do fluxo canonico.
- `SUDO_PASSWORD`, quando existir localmente, e usado apenas para manutencao do WSL e nunca deve entrar em logs, prompts ou commits.
