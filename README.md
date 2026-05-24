# Arcvo

Arcvo e uma linha de producao para publicar acervo YouTube no Odoo eLearning e administrar agentes rastreaveis em projetos Odoo.

O alvo oficial deste repositorio e o Odoo remoto `https://marcelo-m7.com`, banco `odoo19`.

## Stack

- Frontend: React, Vite, TypeScript, TailwindCSS, TanStack Query, Zustand.
- Backend: FastAPI, Pydantic, Uvicorn, XML-RPC/JSON-RPC para Odoo.
- Odoo: Odoo 19 remoto com eLearning (`slide.channel`, `slide.slide`) e addon `arcvo_agents`.
- Agentes: funcionarios digitais em `project.task`, assistidos por Ollama e auditados no Odoo.
- Deploy: webhook Coolify manual pelo painel de Producao.
- Fontes: Supabase Open2, URLs YouTube e oEmbed publico para metadados.

## Linha De Producao

```text
Supabase / YouTube
  -> backend FastAPI
  -> normalizacao e enriquecimento
  -> Odoo eLearning
  -> admin React
```

Agentes seguem outro fluxo rastreavel:

```text
Projetos Odoo
  -> project.task
  -> arcvo_agents
  -> /api/v1/agents
  -> admin React
```

Execucao autonoma:

```text
arcvo.agent.assignment
  -> backend runner
  -> Ollama
  -> allowlist de comandos
  -> arcvo.agent.audit.log
```

## Comandos

```bash
make install
make dev
make backend
make frontend
make lint
make test
make odoo-health
make import-supabase-youtube
make validate-arcvo-agents
```

Frontend: `http://localhost:5173`

Backend: `http://localhost:8000`

API docs em desenvolvimento: `http://localhost:8000/docs`

## Variaveis

Copie `.env.example` para `.env` e preencha segredos reais localmente. Nao commite `.env`.

Obrigatorias:

- `APP_SECRET_KEY`
- `APP_ADMIN_PASSWORD`
- `ODOO_URL`
- `ODOO_DB`
- `ODOO_USER`
- `ODOO_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`

## Odoo

Addons ativos ficam em `odoo/addons`.

- `arcvo_agents`: addon canonico para agentes e atribuicoes em `project.task`.

Addons congelados ficam em `odoo/frozen_addons` e nao fazem parte do deploy canonico.

## APIs Principais

- `GET /health`
- `POST /api/v1/auth/login`
- `GET /api/v1/odoo/health`
- `GET /api/v1/archive/dashboard`
- `GET /api/v1/archive/courses`
- `GET /api/v1/archive/youtube/videos`
- `POST /api/v1/archive/youtube/videos`
- `GET /api/v1/agents`
- `GET /api/v1/agents/{id}`
- `POST /api/v1/agents/{id}/heartbeat`
- `POST /api/v1/agents/{id}/run`
- `POST /api/v1/agents/run-pending`
- `GET /api/v1/agents/executions`
- `GET /api/v1/agents/audit`
- `POST /api/v1/agents/tasks/{task_id}/assign`
- `GET /api/v1/deploy/coolify/status`
- `POST /api/v1/deploy/coolify`

## Documentacao

Veja [docs/technical-setup.md](docs/technical-setup.md) para detalhes de ambiente, estrutura e validacao.
