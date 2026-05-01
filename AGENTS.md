# AGENTS.md

## Stack
- **Backend**: Python 3.12+ / FastAPI / SQLAlchemy / Alembic / PostgreSQL (prod) / SQLite (dev/test)
- **Frontend**: Next.js 14 App Router / Tailwind CSS / TypeScript / lucide-react / framer-motion / recharts
- **Fiscal**: erpbrasil.assinatura, erpbrasil.edoc, nfelib, brazilfiscalreport, reportlab

## Commands
```sh
# Backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001            # dev server
python -m pytest tests/integration/test_auth_register.py -x -v   # focused tests

# Frontend (frontend/ directory)
npm run dev           # next dev server (port 3000)
npx next build        # typecheck + build (no ESLint configured)
```

## Architecture
- **Backend entry**: `app/main.py` — mounts routers at `/api/v1/{setup,auth,empresa,produtos,clientes,vendas,notas}`
- **Frontend entry**: `frontend/src/app/layout.tsx` — wraps all pages with Sidebar + AuthGuard
- **Auth**: JWT in `Authorization: Bearer` header. Roles: `GERENTE`, `GARCOM`. See `app/api/v1/deps.py`
- **DB migrations**: `alembic upgrade head` (auto-run on startup via entrypoint.sh)
- **Models** in `app/models/`, **schemas** in `app/schemas/`, **services** in `app/services/`

## Auth & Security Rules
- Public routes only: `GET /`, `GET /setup/status`, `POST /setup/setup-admin`
- Login rate-limited: 10/min per IP (slowapi)
- Product create/update/delete → GERENTE only
- Client create/edit → any authenticated user; delete → GERENTE only
- Cancel sale → GERENTE only
- Cancel NFe → GERENTE only (justificativa mín. 15 caracteres)
- Print routes (`/notas/{id}/imprimir`, `/imprimir-a4`) accept token via `?token=` query param for new-tab opening
- All other routes: header `Authorization: Bearer` only
- NFe already authorized cannot be re-emitted (protected in backend + frontend)

## Key Conventions
- **DB fallback**: SQLite (`test.db`) if no `DATABASE_URL` env set; Postgres in prod/homolog
- **SECRET_KEY** must be ≥16 chars or server crashes on startup
- **Upload limits**: images 5MB (MIME-validated), XML 10MB, PFX 1MB (only latest kept)
- **CNPJ card import**: extracts data from PDF via `pdftotext` (requires `poppler-utils` in Docker)
- **Dark mode**: most pages support `dark:` classes; wizard-fiscal and notas were recently fixed

## Testing Quirks
- `test_cliente_persistencia` is known-broken (pre-existing auth issue)
- Tests use SQLite at `test.db` — force with `APP_ENV=test`
- Fixtures in `tests/conftest.py` recreate tables per module

## Docker
```sh
docker-compose up --build -d   # full stack (db:5433, backend:8001, frontend:3001)
```
- Backend Dockerfile at repo root; frontend at `frontend/Dockerfile`
- Prod: Railway deployment with `poppler-utils` in Dockerfile for pdftotext
