# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Corporate portal backend (Python 3.12 / FastAPI) providing employee directory, news feed, org structure management, and file handling. Uses PostgreSQL, Elasticsearch, and Keycloak for auth.

## Development Commands

```bash
# Full startup (resets volumes, runs migrations, seeds Keycloak)
make start-dev

# Quick startup (preserves existing data)
make start-quick

# Stop all services
make down

# Remove all containers and volumes
make clean

# Create a new Alembic migration
make new-migr name="description_here"

# Apply pending migrations
make update-db-dev

# Restart API container with fresh env vars
make reload-api

# Stream API logs
make see-api-dev time=5m

# Connect to PostgreSQL CLI
make see-db-dev

# Show Keycloak admin credentials
make keycloak-info
```

The API runs via Docker: `python -m uvicorn core.app:app --host 0.0.0.0 --port 8000`

## Architecture

Layered architecture: **Controllers → Services → Repositories → Models → PostgreSQL**

```
core/
├── api/v1/          # FastAPI routers (controllers). deps.py has auth dependency injection
├── services/        # Business logic. access.py handles authorization checks
├── repositories/    # Data access (async SQLAlchemy). common_repo.py is the base CRUD class
├── models/          # SQLAlchemy ORM models. enums.py defines shared enums
├── schemas/         # Pydantic request/response DTOs
├── common/          # token_service.py (JWT/Keycloak), common_repo.py, common_exc.py
├── config/          # settings.py loads env vars via pydantic_settings
├── utils/           # db_util.py (async session), elastic_search_util.py (ES singleton)
├── security/        # API key auth
├── middleware.py    # JWTBearer middleware (RS256 token validation)
└── app.py           # FastAPI app entry point with lifespan (ES sync on startup)
```

Router aggregation happens in `core/api/v1/v1.py` — all controllers mount under `/api/v1`.

## Key Patterns

- **Auth**: Keycloak issues JWT tokens validated via RS256 public key. Roles: `employee`, `hr`, `admin`, `news_editor`. Use `require_roles()` from `deps.py` for endpoint protection.
- **Async everywhere**: SQLAlchemy async sessions via `asyncpg`, async Elasticsearch client.
- **Elasticsearch**: Used for employee full-text search and autocomplete. Index syncs on app startup via `elastic_sync_service.py`.
- **Audit trail**: Change log models (`ProfileChangeLogOrm`, `NewsChangeLogOrm`, `OrgChangeLogOrm`) track field-level changes with old/new values.
- **Org structure**: Hierarchical tree via `parent_id` self-referential FK on `OrgUnitOrm`.
- **File handling**: Upload/download through `static_service.py` with type validation (image, video, audio, document).

## Infrastructure (docker-compose)

| Service         | Port  | Purpose                    |
|-----------------|-------|----------------------------|
| database        | 5432  | PostgreSQL 16 (app data)   |
| elasticsearch   | 9200  | ES 8.11.0 (search)         |
| api             | 8000  | FastAPI application         |
| keycloak        | 8080  | Auth server                 |
| keycloak-db     | —     | PostgreSQL for Keycloak     |
| keycloak-setup  | —     | Realm/user provisioning     |

## Database Migrations

Managed by Alembic. Migration files in `alembic/versions/`. Always create migrations via `make new-migr` and apply via `make update-db-dev`.

## Test Users (from Keycloak seed)

- `petrov.av` / `password3`
- `ivanov.ii` / `password`

## Notes

- Comments and some field names are in Russian.
- The employee primary key (`eid`) is the Keycloak user ID (string).
- `.env.example` documents all required environment variables.
