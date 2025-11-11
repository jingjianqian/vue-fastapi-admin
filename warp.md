# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Overview

A full-stack admin platform combining FastAPI (Python 3.11) and Vue 3 + Vite + Naive UI with RBAC, dynamic routing, and JWT authentication.

## Stack
- Backend: FastAPI, Tortoise ORM (MySQL by default), Aerich (migrations), Uvicorn
- Frontend: Vue 3, Vite, Pinia, Vue Router, Naive UI, UnoCSS, Axios
- Package managers: pnpm (recommended) or npm
- Docker: Multi-stage build producing Nginx + Python image on port 80

## Repository layout
- Backend (Python): project root
  - Entrypoint: `run.py` (Uvicorn, port 9999, reload on dev)
  - App module: `app/` (routers, models, schemas, settings, init)
  - Config: `app/settings/config.py` (**MySQL default**; SQLite available commented out)
  - Tooling: `pyproject.toml`, `requirements.txt`, `Makefile`
- Frontend (Vue): `web/`
  - Entry: `web/src/main.js`
  - Router: `web/src/router/index.js`
  - Store: `web/src/store/index.js`
  - API calls: `web/src/api/index.js`
  - Vite config: `web/vite.config.js`
  - Env files: `web/.env`, `.env.development`, `.env.production`

## Prerequisites
- Python 3.11+
- Node.js 18.8.0+
- pnpm (recommended): `npm i -g pnpm`
- MySQL (or edit `app/settings/config.py` to use SQLite for local dev)

## Quick start
### Backend (dev)
**Option A: uv (recommended)**
```powershell
pip install uv
uv venv
.\.venv\Scripts\activate  # Windows; use source .venv/bin/activate on Linux/Mac
uv add pyproject.toml
python run.py  # serves http://localhost:9999, OpenAPI at /docs
```

**Option B: pip**
```powershell
python -m venv venv
.\venv\Scripts\activate  # Windows; use source venv/bin/activate on Linux/Mac
pip install -r requirements.txt
python run.py
```

**Notes**
- First run initializes DB, seeds superuser `admin`/`123456`, menus, roles, and APIs.
- **Default DB: MySQL** (connection settings in `app/settings/config.py`)
- To use SQLite locally: uncomment SQLite block and change `default_connection` to "sqlite" in `app/settings/config.py`

### Frontend (dev)
1) `cd web`
2) `pnpm i` (or `npm i`)
3) `pnpm dev`

Defaults
- Dev server port: from `web/.env` (`VITE_PORT=3100`)
- API base: `VITE_BASE_API=/api/v1`
- Proxy: enabled in development (`VITE_USE_PROXY=true`) to backend

## Build
### Frontend
- From `web/`: `pnpm build` (outputs to `web/dist`, controlled by `OUTPUT_DIR` in build/constant)

### Docker (full stack)
- Build: `docker build --no-cache . -t vue-fastapi-admin`
- Run: `docker run -d --restart=always --name=vue-fastapi-admin -p 9999:80 vue-fastapi-admin`
- Access: http://localhost:9999 (Nginx serves frontend; backend proxied)

## Lint, format, test
### Backend (Makefile targets)
- Install deps: `make install` (uv)
- Start: `make start` (equiv. `python run.py`)
- Check: `make check` (black/isort check + ruff)
- Format: `make format` (black + isort)
- Lint: `make lint` (ruff)
- Test: `make test` (pytest)
- DB utils: `make clean-db`, `make migrate`, `make upgrade`

### Frontend
- Lint: `pnpm lint`
- Fix: `pnpm run lint:fix`
- Prettier: `pnpm run prettier`

## Configuration
### Frontend env (web/.env*)
- `.env`:
  - `VITE_TITLE` — app title
  - `VITE_PORT` — dev server port (default 3100)
- `.env.development`:
  - `VITE_PUBLIC_PATH=/`
  - `VITE_USE_PROXY=true`
  - `VITE_BASE_API=/api/v1`
- `.env.production`:
  - `VITE_PUBLIC_PATH=/`
  - `VITE_BASE_API=/api/v1`
  - `VITE_USE_COMPRESS=true`
  - `VITE_COMPRESS_TYPE=gzip`

### Backend settings (app/settings/config.py)
- CORS: allow all by default (change for production)
- JWT: HS256; default token lifetime 7 days
- **DB: MySQL by default**; SQLite config is commented out (uncomment and switch for local dev)
- **Never hardcode secrets** — use environment variables for production

## Routing and auth
- Backend mounts routers under `/api` and versioned as `/api/v1`
- Frontend API module calls endpoints under `/base`, `/user`, `/role`, `/menu`, `/api`, `/dept`, `/auditlog`, `/wechat` with base `/api/v1`
- **Auth**: JWT via `POST /api/v1/base/access_token`
- **Token header**: Frontend sends token in header **"token"** (not "Authorization")
- Permission checking: `DependPermission` validates user's role-bound APIs against method+path

## High-level architecture

### Backend (app/)
- **App startup**: `app/__init__.py` creates FastAPI with middleware (CORS, background task, HTTP audit log) and lifespan that calls `init_data()`
- **init_data()** sequence:
  1. Runs DB migrations (Aerich)
  2. Seeds admin user (admin/123456)
  3. Seeds menus including wechat management
  4. Collects API registry via `ApiController.refresh_api()`
  5. Seeds roles and permissions
- **Routing**:
  - `/api/v1/base` — login, user info (no permission check)
  - `/api/v1/user`, `/role`, `/menu`, `/api`, `/dept`, `/auditlog`, `/wechat` — require `DependPermission`
- **Permission system**: `PermissionControl.has_permission()` validates JWT user's method+path against role-bound APIs
- **API registry**: `ApiController.refresh_api()` scans FastAPI routes with dependencies, inserts/updates Api table, removes stale entries
- **Models**: Tortoise ORM with User, Role, Menu, Api, Dept, AuditLog; many-to-many: roles ↔ menus, roles ↔ apis

### Frontend (web/)
- **HTTP client** (`web/src/utils/http/`):
  - Axios wrapper with `baseURL` from `VITE_BASE_API`
  - Attaches token in header **"token"** (except when `noNeedToken=true`)
  - Interceptors: show errors, logout on 401
- **Router**: Dynamic routes loaded after login; fetches user info, menus, accessible APIs; guards enforce auth
- **Proxy**: Dev server proxies `/api/v1` to backend when `VITE_USE_PROXY=true`

## Common tasks
- Change dev server port: edit `web/.env` → `VITE_PORT`
- Change API base path: edit `web/.env.*` → `VITE_BASE_API`
- Switch DB to SQLite: edit `app/settings/config.py`, uncomment SQLite block, set `default_connection` to "sqlite"
- Reset local DB: `make clean-db` (removes migrations and db files), then rerun
- Add tests: Install pytest separately (not in requirements.txt), then use `make test`

## Important notes
- **Database**: MySQL is the configured default (not SQLite); provide credentials or switch to SQLite for local dev
- **Tests**: Makefile references pytest but it's not in `requirements.txt`; install separately if needed
- **Token header**: Frontend uses header name "token" (not standard "Authorization")
- **Default credentials**: admin/123456 (created on first run; **change for production**)
- **Windows**: Commands shown use PowerShell syntax; Makefile may need adjustment for native Windows

## Quick reference
- **Backend**: `python run.py` → http://localhost:9999/docs
- **Frontend**: `cd web && pnpm dev` → http://localhost:3100
- **Docker**: `docker build --no-cache . -t vue-fastapi-admin && docker run -d -p 9999:80 vue-fastapi-admin`
