# Arcvo

Arcvo e uma operacao Odoo-first para acervo YouTube/eLearning e funcionarios digitais rastreaveis.

O alvo oficial e o Odoo remoto `https://marcelo-m7.com`, banco `odoo19`.

## Stack

- Odoo 19 Community: SSOT para projetos, tarefas, agentes, Discuss, chatter e auditoria.
- Hermes: interface operacional padrao para conversar com agentes e acionar ferramentas.
- Backend: FastAPI, Pydantic, Uvicorn, XML-RPC/JSON-RPC para Odoo.
- Ollama: motor auxiliar de raciocinio dos agentes.
- Coolify: deploy automatico por push na `main` e webhook manual quando necessario.
- Acervo: Supabase Open2, YouTube/oEmbed e Odoo eLearning (`slide.channel`, `slide.slide`).

## Linha De Producao

```text
Supabase / YouTube
  -> backend FastAPI
  -> normalizacao e enriquecimento
  -> Odoo eLearning
```

```text
Odoo project.task
  -> arcvo.agent.assignment
  -> Hermes tools
  -> Ollama
  -> Discuss + chatter + arcvo.agent.audit.log
```

## Comandos

```bash
make install
make dev
make backend
make hermes
make lint
make test
make odoo-health
make import-supabase-youtube
make validate-arcvo-agents
```

Backend local: `http://localhost:8000`

Hermes local: `http://localhost:8010`

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
- `OLLAMA_URI`
- `OLLAMA_MODEL`

## Odoo

Addons ativos ficam em `odoo/addons`.

- `arcvo_agents`: addon canonico para agentes, atribuicoes, Discuss e auditoria em `project.task`.

O arquivo `docker-compose.yaml` permanece na raiz porque a instancia Coolify usa Docker Compose buildpack. O servico Odoo e construido por `odoo/Dockerfile`, que copia `./odoo/addons` para `/mnt/extra-addons` dentro da imagem.

## APIs Principais

- `GET /health`
- `POST /api/v1/auth/login`
- `GET /api/v1/odoo/health`
- `GET|POST|PATCH /api/v1/archive/*`
- `GET /api/v1/agents`
- `GET /api/v1/agents/{id}`
- `POST /api/v1/agents/{id}/heartbeat`
- `POST /api/v1/agents/{id}/message`
- `GET /api/v1/agents/{id}/messages`
- `POST /api/v1/agents/{id}/run`
- `POST /api/v1/agents/run-pending`
- `GET /api/v1/agents/executions`
- `GET /api/v1/agents/audit`
- `POST /api/v1/agents/tasks/{task_id}/assign`
- `GET /api/v1/deploy/coolify/status`
- `POST /api/v1/deploy/coolify`

## Documentacao

Veja [docs/technical-setup.md](docs/technical-setup.md) para detalhes de ambiente, estrutura e validacao.
