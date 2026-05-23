# Arcvo: Autonomous Agent-Based Organization

**Organização autônoma operando sobre Odoo 19 com backend Python, frontend React, e automações via MCP.**

This file helps AI agents understand the codebase structure, conventions, and how to operate autonomously in this agent-based organization.

---

## 🏗️ Architecture Overview

**Stack:**
- **ERP Core**: Odoo 19 (primary business system)
- **Backend**: FastAPI + Python 3.12+ (XML-RPC/JSON-RPC Odoo client, service layer)
- **Frontend**: React + Vite + TypeScript + TailwindCSS
- **Integrations**: Supabase, YouTube (oEmbed), Odoo MCP
- **Deployment**: Docker Compose + WSL environment

**Data Flow:**
```
Frontend (React) → Backend API (FastAPI) → Odoo RPC (XML-RPC/JSON-RPC)
                ↓
           Supabase (archive source)
                ↓
           YouTube (metadata via oEmbed)
```

---

## 📂 Repository Structure

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI application, Odoo integration, service layer |
| `backend/app/` | Main application code |
| `backend/app/api/routes/` | HTTP endpoints (auth, archive, odoo, health) |
| `backend/app/core/` | Settings, security, configuration |
| `backend/app/integrations/` | Odoo client, Supabase, YouTube metadata |
| `backend/app/services/` | Business logic (archive, Odoo operations) |
| `backend/app/schemas/` | Pydantic models for API requests/responses |
| `backend/scripts/` | Standalone utilities (Odoo health checks, imports) |
| `backend/tests/` | Unit and integration tests |
| `frontend/` | React + Vite application |
| `frontend/src/` | TypeScript + TSX source code |
| `frontend/src/features/` | Feature-based route/page organization |
| `frontend/src/lib/` | API client, utilities |
| `frontend/src/store/` | Zustand state (auth, UI) |
| `odoo/addons/` | Local Odoo addon development (mounted into Docker) |
| `docs/` | Technical documentation |

---

## 🚀 Quick Start (WSL Environment)

### Prerequisites
```bash
# Ensure .local/bin is in PATH
export PATH="$HOME/.local/bin:$PATH"

# Install system tools (requires sudo)
make install-system-tools

# Install Python tools (uv, ruff, pytest)
make tools-check
```

### First Time Setup
```bash
# Install dependencies
make install

# Copy and configure .env
cp .env.example .env
# Edit .env with real Odoo credentials and secrets
```

### Development
```bash
# Start all services (frontend + backend in parallel)
make dev

# Or run separately:
make backend   # FastAPI on http://localhost:8000
make frontend  # React Vite on http://localhost:5173
```

### Validation
```bash
make odoo-health      # Validate Odoo connectivity
make lint             # Check code style (ruff + eslint)
make test             # Run pytest + TypeScript checks + build

make docker-up        # Start local Odoo + PostgreSQL (if needed)
make docker-down      # Stop containers
```

---

## 🔐 Environment Configuration (`.env`)

**Required Odoo Integration:**
```bash
ODOO_URL=https://marcelo-m7.com
ODOO_DB=odoo19
ODOO_USER=<username>
ODOO_API_KEY=<api_key>
ODOO_INTEGRATION_MODE=xmlrpc        # Primary mode
ODOO_YOLO=read                       # MCP read-only for now
ODOO_ALLOW_SELF_SIGNED_SSL=true      # Temporary; disable after HTTPS fix
```

**Required App Secrets:**
```bash
APP_SECRET_KEY=<32+ char random key>
APP_ADMIN_PASSWORD=<strong password>
APP_JWT_EXPIRES_MINUTES=720
```

**Optional Integrations:**
```bash
SUPABASE_PROJECT_ID=wvkjainfwsyiyfcmbtid
SUPABASE_URL=https://wvkjainfwsyiyfcmbtid.supabase.co
SUPABASE_PUBLISHABLE_KEY=<public key>
```

**Do not commit `.env`** — it contains secrets. Use `.env.example` for template.

---

## 🛠️ Common Agent Tasks

### Backend Development

**Add a new API route:**
1. Create handler in `backend/app/api/routes/<feature>.py`
2. Define Pydantic schemas in `backend/app/schemas/<feature>.py`
3. Add service logic in `backend/app/services/<feature>_service.py`
4. Register router in `backend/app/main.py`
5. Add tests in `backend/tests/test_<feature>.py`

**Example:** [Archive routes](backend/app/api/routes/archive.py) → [Archive schemas](backend/app/schemas/archive.py) → [Archive service](backend/app/services/archive_service.py)

**Call Odoo models:**
```python
from app.integrations.odoo.client import OdooClient, OdooCredentials
from app.core.config import get_settings

settings = get_settings()
credentials = OdooCredentials(
    url=settings.odoo_url,
    database=settings.odoo_db,
    username=settings.odoo_user,
    api_key=settings.odoo_api_key,
    allow_self_signed_ssl=settings.odoo_allow_self_signed_ssl,
)
client = OdooClient(credentials)
client.authenticate()

# Search
records = client.search("slide.channel", [["name", "=", "My Course"]])

# Search + read
data = client.search_read("slide.channel", fields=["id", "name", "nbr_video"])

# Create
course_id = client.create("slide.channel", {"name": "New Course", "channel_type": "training"})

# Update
client.write("slide.channel", course_id, {"is_published": True})

# Count
count = client.search_count("slide.slide")
```

### Frontend Development

**Add a new page:**
1. Create component in `frontend/src/features/<feature>/<Feature>Page.tsx`
2. Add route in `frontend/src/App.tsx`
3. Add API client method in `frontend/src/lib/api.ts`
4. Use TanStack Query for async state in component

**Example:** [ArchivePage.tsx](frontend/src/features/archive/ArchivePage.tsx) uses [archive.ts API client](frontend/src/lib/archive.ts)

**Use API client:**
```typescript
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Query (read)
const { data: courses, isLoading } = useQuery({
  queryKey: ["archive", "courses"],
  queryFn: () => api.get("/api/v1/archive/courses"),
});

// Mutation (write)
const createCourseMutation = useMutation({
  mutationFn: (name: string) => api.post("/api/v1/archive/courses", { name }),
  onSuccess: () => {
    // Refetch, toast, etc.
  },
});
```

### Odoo Addon Development

**Create addon scaffold:**
```bash
cd odoo/addons
odoo-bin scaffold my_addon .
```

**Key files:**
- `__manifest__.py` — metadata, dependencies, data files
- `models/models.py` — Model definitions (ORM)
- `views/views.xml` — Form/tree/search views
- `security/ir.model.access.csv` — Record rules

See [Odoo 19 skill](file:///c:\Users\marce\.agents\skills\odoo-19\SKILL.md) for advanced patterns.

### Supabase Archive Import

**Preview import (dry-run):**
```bash
make dry-run-supabase-youtube
# Outputs: .data/supabase_youtube.json (preview of what will be imported)
```

**Execute import:**
```bash
make import-supabase-youtube
# Maps Supabase videos → Odoo slide.slide
# Maps categories → Odoo slide.channel (creates if missing)
```

See [backend/scripts/import_supabase_youtube.py](backend/scripts/import_supabase_youtube.py) for details.

---

## 📊 Primary API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/odoo/health` | Odoo connectivity validation |
| `POST` | `/api/v1/auth/login` | Admin login (returns JWT) |
| `GET` | `/api/v1/archive/dashboard` | Course/video counts |
| `GET` | `/api/v1/archive/courses` | List Odoo slide.channel records |
| `POST` | `/api/v1/archive/courses` | Create course (auto-creates if missing) |
| `GET` | `/api/v1/archive/youtube/videos` | List published videos |
| `POST` | `/api/v1/archive/youtube/videos` | Create video from YouTube URL |
| `PATCH` | `/api/v1/archive/youtube/videos/{id}` | Update video metadata/publish status |
| `POST` | `/api/v1/archive/youtube/preview` | Preview YouTube metadata before creation |
| `GET` | `/api/v1/odoo/models/{model}/records` | Generic Odoo search_read |
| `POST` | `/api/v1/odoo/models/{model}/records` | Generic Odoo create |
| `PATCH` | `/api/v1/odoo/models/{model}/records/{id}` | Generic Odoo write |

**API Docs:** http://localhost:8000/docs (Swagger UI, dev only)

---

## 🔌 Integration Points

### Odoo XML-RPC Client
**File:** [backend/app/integrations/odoo/client.py](backend/app/integrations/odoo/client.py)

- Handles authentication, search, CRUD operations
- Wraps XML-RPC with error handling
- Supports both XML-RPC (primary) and JSON-RPC (diagnostics)

**Health check:**
```bash
make odoo-health
# Outputs version, auth status, common models available
```

### Supabase Archive Integration
**File:** [backend/app/integrations/supabase.py](backend/app/integrations/supabase.py)

- Fetches public YouTube archive (videos + categories)
- Uses public oEmbed (no YouTube API key needed)
- Maps to Odoo eLearning models (slide.channel, slide.slide)

### MCP (Model Context Protocol)
- Configured in VS Code Copilot with `mcp-server-odoo`
- Currently in read-only YOLO mode (no MCP control until module installed in Odoo)
- XML-RPC and JSON-RPC remain primary integration paths

---

## 🧪 Testing & Quality

**Run all tests:**
```bash
make test
# Runs: pytest (backend) + TypeScript typecheck + Vite build (frontend)
```

**Backend tests:**
```bash
cd backend
uv run pytest --capture=no
# Test files: tests/test_*.py
```

**Linting:**
```bash
make lint
# Backend: ruff check .
# Frontend: eslint .
```

**Formatting:**
```bash
make format
# Backend: ruff format .
# Frontend: prettier --write .
```

---

## 🐳 Docker Deployment

**Start local Odoo + PostgreSQL:**
```bash
make docker-up
# Odoo: http://localhost:8069
# PostgreSQL: localhost:5432
# (Credentials in docker-compose.yaml)
```

**Stop:**
```bash
make docker-down
```

**Addons:** Local files in `odoo/addons/` are mounted and copied into the container on startup.

---

## 📋 Agent Collaboration Patterns

### Task Assignment via Odoo
1. **ProjectManager Agent** creates project/task in Odoo (`project.task`)
2. **DeveloperAgent** claims task, links to PR/branch
3. **DevOpsAgent** handles deployment/infrastructure
4. **QAAgent** validates deliverables
5. **DocumentationAgent** updates docs

### Recommended Workflow
- All work tracked in Odoo (`project.task`, `ir.attachment` for deliverables)
- Code changes in feature branches
- PRs linked to Odoo tasks
- Commits reference task IDs: `feat: add dashboard [task-id]`
- All scripts logged to `backend/scripts/` (reusable across agents)

### MCP for Agent Automation
- Use `mcp-server-odoo` to:
  - Query tasks, projects, models
  - Update task status/progress
  - Fetch model records for processing
  - Post logs/attachments

---

## ⚠️ Important Notes

### WSL Path Issues
- If `pnpm install` fails with `EACCES` on `/mnt/c`, move repo to Linux filesystem: `~/projects/arcvo`
- Alternatively, use `npm install --prefix frontend` as fallback

### Odoo Self-Signed SSL
- `ODOO_ALLOW_SELF_SIGNED_SSL=true` is temporary
- Must disable after Traefik HTTPS is properly configured
- Remove MCP SSL patch when cert is fixed

### Odoo Authentication
- `authenticate()` is the reliable health check (not just HTTP status)
- `ODOO_API_KEY` is the authentication token (not password)
- XML-RPC and JSON-RPC may return different error formats

### Missing Credentials
- Backend gracefully skips Odoo routes if `has_odoo_credentials` is False
- Frontend still renders, but Odoo-dependent pages show errors
- Import scripts fail loudly if `.env` is incomplete

---

## 🔄 Common Agent Workflows

### Developer Agent: Add Feature to Archive
```bash
# 1. Branch
git checkout -b feat/archive-tags

# 2. Backend: Create route + service
# Edit: backend/app/api/routes/archive.py
#       backend/app/services/archive_service.py
#       backend/app/schemas/archive.py

# 3. Frontend: Add page + API client
# Edit: frontend/src/features/archive/TagsPage.tsx
#       frontend/src/lib/api.ts

# 4. Test
make test

# 5. Commit + link to Odoo task
git commit -am "feat: add archive tags [task-123]"
git push origin feat/archive-tags

# 6. Create PR (link to Odoo task in PR description)
```

### DevOps Agent: Deploy to Production
```bash
# 1. Pull latest main
git checkout main && git pull

# 2. Build Docker image
docker build -f backend/Dockerfile -t arcvo-backend:latest .
docker build -f frontend/Dockerfile -t arcvo-frontend:latest .

# 3. Push to registry

# 4. Deploy (Kubernetes / Docker Swarm / Ansible)

# 5. Validate health
make odoo-health
curl -s http://production-api/health | jq .
```

### QA Agent: Validate Deliverable
```bash
# 1. Fetch feature branch
git checkout feat/archive-tags

# 2. Run tests
make test

# 3. Manual testing (dev server)
make dev
# Test: http://localhost:5173, http://localhost:8000/docs

# 4. Validate Odoo integration
make odoo-health

# 5. Approve in PR / Update Odoo task status
```

---

## 📚 Documentation Links

- [Technical Setup](docs/technical-setup.md) — Environment, backend structure, integrations
- [README](README.md) — Project overview, quick start, useful commands
- [Makefile](Makefile) — All available commands
- [Backend Config](backend/app/core/config.py) — Settings, environment variables
- [Odoo Client](backend/app/integrations/odoo/client.py) — XML-RPC/JSON-RPC interface
- [Archive Service](backend/app/services/archive_service.py) — Business logic examples

---

## 🎯 Next Steps for Organization Growth

1. **Autonomous Task Router**: MCP-based system to automatically assign Odoo tasks to specialized agents
2. **Agent Registry**: Odoo module to define agent roles, capabilities, and availability
3. **Audit Trail**: Structured logging of all agent actions (decisions, API calls, errors)
4. **Multi-Agent Orchestration**: Workflow engine for complex, multi-step tasks across agents
5. **Performance Monitoring**: Dashboard for agent productivity, error rates, task completion times
6. **Knowledge Base**: Shared MCP-backed documentation for agent learning

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Odoo connection fails | Run `make odoo-health`, check `ODOO_URL`, `ODOO_API_KEY`, SSL certificate |
| `pnpm install` fails on WSL | Move repo to `~/projects`, or use `npm install --prefix frontend` |
| Tests fail with import errors | Run `cd backend && uv sync` to refresh lockfile |
| Frontend won't connect to backend | Check `VITE_API_BASE_URL` in `.env`, ensure backend is running |
| MCP shows "Reauthentication required" | Restart MCP process, re-authenticate XML-RPC connection |

---

**Last Updated:** 2026-05-23  
**Organization Model:** Autonomous Agent-Based (Odoo 19 + Python + React)  
**Primary Integration:** Odoo XML-RPC + Supabase + YouTube oEmbed
