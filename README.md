# Arcvo

Arcvo é uma operação Odoo-first para acervo YouTube/eLearning e funcionários digitais rastreáveis.

O alvo oficial é o Odoo remoto `https://marcelo-m7.com`, banco `odoo19`.

## Stack

- **Odoo 19 Community**: SSOT para projetos, tarefas, agentes (hr.employee), Discuss, chatter e auditoria.
- **Backend FastAPI**: Serviço de suporte (health, archive, deploy), sem lógica de agentes.
- **Ollama**: Motor de raciocínio LLM para agentes (`gemma3:4b` recomendado).
- **Arcvo Addon** (`arcvo_agents`): Orquestração de agentes, logs estruturados, integração Discuss.
- **Coolify**: Deploy automático por push na `main` e webhook manual quando necessário.
- **Acervo**: Supabase Open2, YouTube/oEmbed e Odoo eLearning (`slide.channel`, `slide.slide`).

## Linha De Produção

### Acervo (YouTube → Odoo eLearning)
```text
Supabase / YouTube
  → backend FastAPI (import/enrich)
  → Odoo eLearning (slide.channel, slide.slide)
```

### Agentes (Odoo Native Orchestration)
```text
Odoo hr.employee (is_agent=True)
  ↓ Cron (5 min) ou Ação Manual
  ↓ OllamaClient (Python addon)
  ↓ Ollama API
  ↓ arcvo.agent.message (auditoria) + Discuss
```

## Comandos

```bash
make install           # Instala dependências (uv sync)
make lint              # Validação ruff
make format            # Auto-format código
make test              # Executa pytest
make backend           # Inicia FastAPI local (porta 8000)
make odoo-health       # Verifica conectividade Odoo
make ollama-health     # Verifica conectividade Ollama
make validate-arcvo-agents  # Valida addon Python/XML
make import-supabase-youtube  # Importa acervo de Supabase
```

**Backend Local:** `http://localhost:8000` (API docs: `/docs`)

**Agentes:** Executados via Odoo cron (5 min) + ações manuais (botão Test Agent)

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

O endpoint Ollama validado e `https://api.ollama.monynha.me`.
Modelo recomendado para runtime mais rapido: `gemma3:4b`.

## Odoo

Addons ativos ficam em `odoo/addons`.

- `arcvo_agents`: addon canonico para agentes, atribuicoes, Discuss e auditoria em `project.task`.

O arquivo `docker-compose.yaml` permanece na raiz porque a instancia Coolify usa Docker Compose buildpack. O servico Odoo e construido por `odoo/Dockerfile`, que copia `./odoo/addons` para `/mnt/extra-addons` dentro da imagem.

## APIs Principais (Backend)

- `GET /health` — health check geral
- `POST /api/v1/auth/login` — autenticação
- `GET /api/v1/odoo/health` — status Odoo
- `GET|POST|PATCH /api/v1/archive/*` — gerenciamento acervo
- `GET /api/v1/deploy/coolify/status` — status deploy
- `POST /api/v1/deploy/coolify` — trigger deploy

**Nota:** Lógica de agentes foi movida para Odoo addon. Veja [docs/odoo-agent-orchestration.md](docs/odoo-agent-orchestration.md) para orquestração de agentes.

## Documentacao

Veja [docs/technical-setup.md](docs/technical-setup.md) para detalhes de ambiente, estrutura e validacao.
