# Database Management — MailOps AI

This directory contains database migration scripts (Alembic), schema configurations, local development environment specifications, and database documentation for MailOps AI.

---

## Technical Stack
- **Database Engine**: PostgreSQL 16
- **Vector Extension**: `pgvector` (`pgvector/pgvector:pg16` Docker image)
- **ORM / Data Access**: SQLAlchemy 2.0 (`DeclarativeBase`, `Mapped`, `mapped_column`)
- **Driver**: `psycopg` (v3) (`psycopg[binary]>=3.1.18`)
- **Migrations**: Alembic (`alembic>=1.13.1`)

---

## Local PostgreSQL Setup (Docker)

To launch the reproducible local PostgreSQL environment:

### Start PostgreSQL
```bash
docker compose up -d
```

### Stop PostgreSQL
```bash
docker compose down
```

### Required Environment Variables
Configured in `.env` (derived from `.env.example`):
```env
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=mailops_db
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/mailops_db
```

---

## Alembic Migration Workflow

Alembic configuration is specified in root `alembic.ini` and points to migration scripts in `database/migrations/`.

### Apply Migrations (Upgrade to Latest)
```bash
alembic upgrade head
```

### Revert Migrations (Downgrade to Base)
```bash
alembic downgrade base
```

### Create New Migration Revision
```bash
alembic revision --autogenerate -m "describe_migration_changes"
```

---

## Domain Models (Milestone 2 Schema)

### 1. `User` (`users` table)
- `id` (UUID, Primary Key)
- `email` (String 255, Unique, Indexed, Non-nullable)
- `full_name` (String 255, Nullable)
- `avatar_url` (String 512, Nullable)
- `is_active` (Boolean, Default True)
- `is_superuser` (Boolean, Default False)
- `created_at` (DateTime UTC)
- `updated_at` (DateTime UTC)
- `oauth_accounts` (Relationship to `OAuthAccount`, Cascade Delete)

### 2. `OAuthAccount` (`oauth_accounts` table)
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key -> `users.id` ON DELETE CASCADE, Indexed, Non-nullable)
- `provider` (String 50, Non-nullable, e.g. "google")
- `provider_account_id` (String 255, Non-nullable, provider user ID / sub)
- `email` (String 255, Nullable)
- `encrypted_access_token` (Text, Nullable — Secure Storage Boundary)
- `encrypted_refresh_token` (Text, Nullable — Secure Storage Boundary)
- `token_expires_at` (DateTime UTC, Nullable)
- `scopes` (Text, Nullable)
- `created_at` (DateTime UTC)
- `updated_at` (DateTime UTC)
- `UniqueConstraint("provider", "provider_account_id", name="uq_oauth_provider_account")`

---

## Token Storage Security Boundary

`encrypted_access_token` and `encrypted_refresh_token` establish the storage schema for OAuth tokens. Plaintext credentials MUST NEVER be stored in these columns. In Milestone 3, application-level symmetric encryption keys will encrypt access and refresh tokens prior to database persistence.

---

## Running Database Tests

Execute full unit and integration test suite:
```bash
$env:PYTHONPATH="."
.\.venv\Scripts\python -m pytest backend/tests
```

Execute standalone Alembic migration lifecycle verification (Upgrade -> Verify -> Downgrade -> Verify -> Re-upgrade):
```bash
$env:PYTHONPATH="."
.\.venv\Scripts\python scripts/verify_migrations.py
```
