import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.ai import router as ai_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.gmail import router as gmail_router
from backend.app.api.v1.graph import router as graph_router
from backend.app.api.v1.reply_drafts import router as reply_drafts_router
from backend.app.api.v1.search import router as search_router
from backend.app.core.config import settings

log = logging.getLogger("mailops.startup")


def _ensure_migrations_applied() -> None:
    """Check Alembic migration state and apply pending migrations when behind HEAD.

    Behavior by environment:
    - Non-production (APP_ENV != 'production'):  Automatically runs
      ``alembic upgrade head`` when the DB revision is behind or absent.
      A migration failure raises RuntimeError, which stops the server.
    - Production: Skips auto-migration entirely. Migrations MUST be applied
      as an explicit pre-deployment step (e.g., ``alembic upgrade head`` in
      the CI/CD pipeline). The backend logs a warning if the schema is behind.

    This is a safety net for local development and fresh Docker Compose
    environments, not a replacement for a proper deployment migration step.
    """
    try:
        from alembic.config import Config
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory

        from backend.app.db.session import engine

        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn)
            current_rev = ctx.get_current_revision()

        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()

        if current_rev == head_rev:
            log.info("Database schema is current at revision %s.", current_rev)
            return

        if settings.APP_ENV == "production":
            # In production, never auto-migrate. Log loudly and continue.
            log.critical(
                "PRODUCTION: Database at revision %s but HEAD is %s. "
                "Run 'alembic upgrade head' in your deployment pipeline immediately.",
                current_rev,
                head_rev,
            )
            return

        # Development / staging: auto-migrate.
        if current_rev is None:
            log.warning(
                "No Alembic revision found in database. Running 'alembic upgrade head'..."
            )
        else:
            log.warning(
                "Database at revision %s, HEAD is %s. Running 'alembic upgrade head'...",
                current_rev,
                head_rev,
            )

        from alembic import command

        command.upgrade(alembic_cfg, "head")
        log.info("Alembic upgrade head completed successfully.")

    except RuntimeError:
        raise  # Re-raise migration failure to stop server startup.
    except Exception as exc:
        log.critical("Database migration check failed at startup: %s", exc, exc_info=True)
        raise RuntimeError(f"Database migration failed at startup: {exc}") from exc


def _reset_stale_syncing_states() -> None:
    """Reset any gmail_sync_states rows stuck at SYNCING due to a prior server crash.

    A crash during an active sync leaves the row at sync_status='SYNCING'
    indefinitely. On restart we mark them FAILED with a safe diagnostic message
    so users can re-trigger a fresh sync rather than seeing a permanently
    stuck status.

    This function is intentionally non-fatal: if the DB is unavailable or the
    table does not yet exist, it logs a warning and continues.
    """
    try:
        from sqlalchemy import update

        from backend.app.db.session import SessionLocal
        from backend.app.models.gmail_sync_state import GmailSyncState

        db = SessionLocal()
        try:
            result = db.execute(
                update(GmailSyncState)
                .where(GmailSyncState.sync_status == "SYNCING")
                .values(
                    sync_status="FAILED",
                    error_message="Sync interrupted by server restart.",
                )
            )
            affected = result.rowcount
            db.commit()
            if affected:
                log.warning(
                    "FIX-SYNC-1: Reset %d stale SYNCING state(s) to FAILED at startup.",
                    affected,
                )
        finally:
            db.close()

    except Exception as exc:
        # Non-fatal: log and continue. Migrations may not have been applied yet
        # on the very first boot — the next startup will catch any remaining stale states.
        log.warning(
            "Could not reset stale SYNCING states at startup (non-fatal): %s", exc
        )


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Application lifespan context: runs startup checks before serving requests.

    Startup sequence:
    1. Verify + auto-apply Alembic migrations (development only).
    2. Reset any gmail_sync_states rows left at SYNCING by a prior crash.
    3. Yield control to FastAPI (begin serving requests).
    """
    _ensure_migrations_applied()
    _reset_stale_syncing_states()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="FastAPI Backend for MailOps AI work-intelligence platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(gmail_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(search_router, prefix=settings.API_V1_STR)
app.include_router(graph_router, prefix=settings.API_V1_STR)
app.include_router(reply_drafts_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "0.1.0",
    }
