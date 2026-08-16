# System Architecture Overview

MailOps AI uses a **Modular Monolith** architecture pattern for Version 1.

```
                   +--------------------------------+
                   | React + TypeScript + Vite UI   |
                   +--------------------------------+
                                   | (HTTP REST)
                                   v
                   +--------------------------------+
                   |      FastAPI Backend App       |
                   +--------------------------------+
                     |            |               |
                     v            v               v
           +-------------+  +------------+  +------------+
           | PostgreSQL  |  | Background |  | External   |
           | + pgvector  |  | Workers    |  | APIs       |
           +-------------+  +------------+  +------------+
                                              (Gmail/Gemini)
```

## Database Layer Architecture (Milestone 2)

MailOps AI uses **PostgreSQL 16** with **SQLAlchemy 2.0** ORM and **Alembic** schema migrations.

### Core Architecture Components:
- **Engine & Driver**: `psycopg` (v3) driver connecting via `postgresql+psycopg://` URI.
- **Session Management**: Request-scoped sessions yielded by `get_db()` dependency generator with `SessionLocal` factory (`autocommit=False, autoflush=False`).
- **Base Infrastructure**: Modern SQLAlchemy 2.0 `DeclarativeBase` (`backend/app/db/base_class.py`) with automatic table naming conventions, default UUID primary keys (`uuid.uuid4`), and timezone-aware UTC timestamps (`created_at`, `updated_at`).
- **Domain Models**:
  - `User`: Application user entity (`users` table) with unique indexed `email`.
  - `OAuthAccount`: Identity provider account link (`oauth_accounts` table) with `UniqueConstraint("provider", "provider_account_id")` and cascade deletion from `User`.
- **Token Security Boundary**: Nullable text columns (`encrypted_access_token`, `encrypted_refresh_token`) establishing schema boundaries for encrypted token persistence without raw credential exposure.
- **Schema Migration Control**: Controlled exclusively through versioned scripts in `database/migrations/` managed by Alembic.
