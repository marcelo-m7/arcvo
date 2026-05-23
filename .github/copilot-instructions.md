# Copilot Instructions for Arcvo Codebase

## Code Style & Conventions

### Python Backend

**Tool:** Ruff (linter + formatter)

```python
# Line length: 100 chars
# Target: Python 3.12+
# Lint rules: E, F, I (imports), UP, B

# Imports: sorted, organized
from typing import Any
import httpx
from app.core.config import settings
from app.integrations.odoo.client import OdooClient
```

**Naming & Structure:**
- Models: `SnakeCase` file + `PascalCase` class (e.g., `user_service.py` → `UserService`)
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`
- Dataclasses: Use `@dataclass(frozen=True)` for immutable configs

**Docstrings & Types:**
- Use type hints on all functions: `def create(self, model: str, values: dict[str, Any]) -> int:`
- Class docstrings for public classes
- No inline comments for obvious code; prefer clear names

**Error Handling:**
```python
class ServiceError(RuntimeError):
    """Custom exception for this service."""

try:
    result = risky_operation()
except ValueError as exc:
    raise ServiceError(f"Operation failed: {exc}") from exc
```

**Pydantic Schemas:**
- Use `BaseModel` for API request/response contracts
- Use `Field` for validation/constraints: `Field(min_length=1, max_length=255)`
- Place in `app/schemas/` organized by feature

**FastAPI Routes:**
- Slim, use service layer for logic
- Include HTTP status codes: `@router.post(..., status_code=201)`
- Use dependency injection for settings/credentials
- Document endpoints with docstrings

### TypeScript/React Frontend

**Tool:** ESLint + Prettier

```typescript
// Line length: 80 chars (frontend convention)
// Target: TypeScript 5.9+, React 19+

// Imports: organized, alphabetical
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";
```

**Naming & Structure:**
- Components: `PascalCase`, file matches component name (e.g., `ArchivePage.tsx`)
- Hooks/functions: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Feature folders: one feature per folder under `src/features/`

**Component Patterns:**
```typescript
// Functional components only, with hooks
import { FC, ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

interface Props {
  id: string;
  onUpdate?: (data: any) => void;
  children?: ReactNode;
}

export const MyComponent: FC<Props> = ({ id, onUpdate, children }) => {
  const { data, isLoading } = useQuery({
    queryKey: ["resource", id],
    queryFn: () => api.get(`/resource/${id}`),
  });

  return <div>{children}</div>;
};
```

**State Management:**
- UI state: Zustand stores in `src/store/`
- Server state: TanStack Query in components
- Form state: Local component state or React Hook Form if complex

**Styling:**
- TailwindCSS v4 classes (no inline styles)
- Dark mode with `dark:` prefix
- Responsive: `sm:`, `md:`, `lg:` prefixes

### Odoo Addons

**File Naming:**
- Models: `models/models.py`
- Controllers: `controllers/controllers.py`
- Views: `views/views.xml`
- Data: `data/<feature>.xml` (loaded from manifest)
- Security: `security/ir.model.access.csv`

**Manifest Convention:**
```python
{
    'name': "Feature Name",
    'version': "0.1",
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/demo.xml',
    ],
    'demo': ['data/demo.xml'],
    'external_dependencies': {'python': ['requests']},
}
```

**Model Naming:**
- Model names: `lowercase.name` (e.g., `my_addon.contract`)
- Fields: `snake_case`
- Methods: `snake_case`, prefix private with `_`

---

## API & Integration Patterns

### Odoo Integration
```python
from app.integrations.odoo.client import OdooClient, OdooCredentials

# Initialize in service or route dependency
credentials = OdooCredentials(
    url=settings.odoo_url,
    database=settings.odoo_db,
    username=settings.odoo_user,
    api_key=settings.odoo_api_key,
    allow_self_signed_ssl=settings.odoo_allow_self_signed_ssl,
)
client = OdooClient(credentials)
client.authenticate()

# Always catch OdooClientError
try:
    records = client.search_read("res.partner", fields=["name", "email"])
except OdooClientError as exc:
    logger.error(f"Odoo search failed: {exc}")
    raise  # Or handle gracefully
```

### API Responses
```python
from fastapi import FastAPI, HTTPException
from app.schemas.archive import ArchiveCourse

@router.get("/courses", response_model=list[ArchiveCourse])
async def list_courses():
    """Fetch all archive courses from Odoo."""
    try:
        courses = archive_service.list_courses()
        return courses
    except OdooClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
```

### Frontend API Client
```typescript
// frontend/src/lib/api.ts
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  },
});

export { api };

// Usage in component:
const { data } = useQuery({
  queryKey: ["courses"],
  queryFn: () => api.get("/api/v1/archive/courses").then(r => r.data),
});
```

---

## Testing

### Backend Tests
```python
# tests/test_archive_service.py
import pytest
from app.services.archive_service import ArchiveService
from app.integrations.odoo.client import OdooClient, OdooClientError

@pytest.fixture
def mock_client(monkeypatch):
    def mock_search_read(*args, **kwargs):
        return [{"id": 1, "name": "Test Course"}]
    monkeypatch.setattr(OdooClient, "search_read", mock_search_read)

def test_list_courses(mock_client):
    service = ArchiveService(OdooClient(...))
    courses = service.list_courses()
    assert len(courses) == 1
    assert courses[0].name == "Test Course"
```

**Run:**
```bash
cd backend
uv run pytest --capture=no
```

### Frontend Tests
- Use TypeScript compiler for type checking: `pnpm typecheck`
- Build test: `pnpm build`
- ESLint: `pnpm lint`

---

## Commit & PR Conventions

**Branch naming:**
```
feat/feature-name
fix/bug-description
refactor/area-of-change
docs/documentation-update
test/test-coverage
```

**Commit messages:**
```
feat: add archive course list endpoint [task-123]
fix: handle missing Odoo credentials gracefully
refactor: extract Supabase client to service layer
docs: update environment configuration section
test: add archive service unit tests
```

**Link to Odoo tasks:** Include task ID in commit/PR description for traceability

---

## File Organization Rules

**Backend Structure:**
```
backend/app/
├── api/routes/      # HTTP endpoints (feature-based)
├── core/            # Config, security, settings
├── integrations/    # External service clients (Odoo, Supabase, YouTube)
├── schemas/         # Pydantic request/response models
├── services/        # Business logic layer
└── main.py          # App factory
```

**Frontend Structure:**
```
frontend/src/
├── app/             # Root App component
├── components/      # Shared components (ProtectedRoute, Shell)
├── features/        # Feature-based pages (archive, auth, odoo)
├── lib/             # Utilities, API client
├── store/           # Zustand state (auth, ui)
└── styles/          # Global styles
```

---

## Performance & Security

### Performance Checks
- Backend: Use search/search_read with limits; avoid N+1 queries
- Frontend: Use TanStack Query caching; avoid re-renders with useMemo/useCallback
- Odoo: Prefer search_read over separate search + read calls

### Security
- Never commit `.env`
- JWT tokens stored in localStorage (frontend)
- Odoo API keys loaded from environment only
- Self-signed SSL disabled in production
- CORS configured to specific origins (not `*`)

---

## Common Tasks

### Add a Feature
1. **Backend route** → `backend/app/api/routes/<feature>.py`
2. **Service layer** → `backend/app/services/<feature>_service.py`
3. **Schemas** → `backend/app/schemas/<feature>.py`
4. **Tests** → `backend/tests/test_<feature>.py`
5. **Register router** in `backend/app/main.py`
6. **Frontend page** → `frontend/src/features/<feature>/<Feature>Page.tsx`
7. **API client** → update `frontend/src/lib/api.ts`
8. **Test** → `make test`

### Debug Odoo Connection
```bash
make odoo-health
# Output: version, auth status, model availability

# Or in Python:
from app.integrations.odoo.client import OdooClient, OdooCredentials
from app.core.config import get_settings
settings = get_settings()
client = OdooClient(OdooCredentials(...))
print(client.version())
print(client.authenticate())
```

### Format & Lint
```bash
make format
make lint
```

---

## Useful Shortcuts

| Command | Purpose |
|---------|---------|
| `make dev` | Start frontend + backend |
| `make test` | Run all tests + typecheck + build |
| `make odoo-health` | Validate Odoo connection |
| `make lint` | Check style |
| `make format` | Auto-format code |
| `make docker-up` | Start local Odoo + PostgreSQL |
| `make tools-check` | Verify system tools installed |

---

## Agent Capabilities

When working as an AI agent in this codebase:

1. **Explore before assuming** — Check existing patterns in similar files
2. **Follow tool conventions** — Ruff for Python, ESLint for TypeScript
3. **Link, don't duplicate** — Reference docs/files instead of copying
4. **Test before merge** — Run `make test` and validate Odoo health
5. **Document integration points** — If adding new Odoo models or API endpoints
6. **Handle errors explicitly** — Raise typed exceptions, catch gracefully
7. **Use dependency injection** — Services, config, credentials passed as params
8. **Keep components small** — Single responsibility, testable, reusable

---

**Last Updated:** 2026-05-23  
**Team:** Monynha Softwares  
**Organization Model:** Autonomous Agent-Based (Odoo 19)
