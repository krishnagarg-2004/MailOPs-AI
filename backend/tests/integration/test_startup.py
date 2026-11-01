"""Integration tests for startup lifecycle functions in backend.app.main.

Tests cover:
- FIX-DB-1: _ensure_migrations_applied (migration state detection, auto-upgrade in dev)
- FIX-SYNC-1: _reset_stale_syncing_states (stale SYNCING → FAILED transition)
"""
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.db.base import Base
from backend.app.models.gmail_sync_state import GmailSyncState
from backend.app.models.user import User
from backend.app.main import _reset_stale_syncing_states
from backend.tests.integration.test_database import db_session, test_engine


@pytest.fixture(autouse=True)
def setup_db():
    """Create schema before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    with test_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        conn.commit()


class TestResetStaleSyncingStates:
    """FIX-SYNC-1: Stale SYNCING rows are reset to FAILED at server restart."""

    def test_stale_syncing_reset_to_failed(self, db_session: Session):
        """SYNCING state left from a crash is reset to FAILED on startup."""
        user = User(email="stalefail@enterprise.com", full_name="Stale User")
        db_session.add(user)
        db_session.commit()

        # Simulate a state stuck in SYNCING (e.g., from a prior server crash)
        state = GmailSyncState(
            user_id=user.id,
            sync_status="SYNCING",
            synced_message_count=5,
        )
        db_session.add(state)
        db_session.commit()

        # Run the startup recovery function
        _reset_stale_syncing_states()

        db_session.refresh(state)
        assert state.sync_status == "FAILED"
        assert state.error_message == "Sync interrupted by server restart."
        # Existing data (synced_message_count, last_history_id) must be preserved
        assert state.synced_message_count == 5

    def test_completed_state_not_affected(self, db_session: Session):
        """States that are COMPLETED, IDLE, or FAILED are not touched by the reset."""
        user = User(email="completedok@enterprise.com", full_name="Completed User")
        db_session.add(user)
        db_session.commit()

        state = GmailSyncState(
            user_id=user.id,
            sync_status="COMPLETED",
            synced_message_count=10,
            last_history_id=99999,
        )
        db_session.add(state)
        db_session.commit()

        _reset_stale_syncing_states()

        db_session.refresh(state)
        assert state.sync_status == "COMPLETED"
        assert state.last_history_id == 99999

    def test_idle_state_not_affected(self, db_session: Session):
        """IDLE states are untouched by the stale-SYNCING reset."""
        user = User(email="idleuser@enterprise.com", full_name="Idle User")
        db_session.add(user)
        db_session.commit()

        state = GmailSyncState(user_id=user.id, sync_status="IDLE", synced_message_count=0)
        db_session.add(state)
        db_session.commit()

        _reset_stale_syncing_states()

        db_session.refresh(state)
        assert state.sync_status == "IDLE"

    def test_multiple_stale_users_all_reset(self, db_session: Session):
        """Multiple SYNCING states from different users are all reset."""
        user1 = User(email="stale1@enterprise.com", full_name="Stale One")
        user2 = User(email="stale2@enterprise.com", full_name="Stale Two")
        db_session.add_all([user1, user2])
        db_session.commit()

        s1 = GmailSyncState(user_id=user1.id, sync_status="SYNCING", synced_message_count=1)
        s2 = GmailSyncState(user_id=user2.id, sync_status="SYNCING", synced_message_count=2)
        db_session.add_all([s1, s2])
        db_session.commit()

        _reset_stale_syncing_states()

        db_session.refresh(s1)
        db_session.refresh(s2)
        assert s1.sync_status == "FAILED"
        assert s2.sync_status == "FAILED"

    def test_failed_state_not_overwritten(self, db_session: Session):
        """An already-FAILED state with an existing error message is untouched."""
        user = User(email="alreadyfailed@enterprise.com", full_name="Failed User")
        db_session.add(user)
        db_session.commit()

        state = GmailSyncState(
            user_id=user.id,
            sync_status="FAILED",
            error_message="Original failure reason.",
        )
        db_session.add(state)
        db_session.commit()

        _reset_stale_syncing_states()

        db_session.refresh(state)
        assert state.sync_status == "FAILED"
        assert state.error_message == "Original failure reason."

    def test_no_db_does_not_crash(self):
        """_reset_stale_syncing_states handles DB unavailability gracefully (non-fatal)."""
        import unittest.mock as mock
        # SessionLocal is imported locally inside _reset_stale_syncing_states,
        # so we patch it at the source module (backend.app.db.session).
        with mock.patch(
            "backend.app.db.session.SessionLocal",
            side_effect=Exception("Simulated DB unavailable"),
        ):
            # Must not raise — returns quietly with a warning log
            _reset_stale_syncing_states()


class TestEnsureMigrationsApplied:
    """FIX-DB-1: Startup migration check logic (environment-gated)."""

    def test_ensure_migrations_noop_when_at_head(self):
        """When DB is already at HEAD, _ensure_migrations_applied is a no-op (no upgrade called)."""
        from backend.app.main import _ensure_migrations_applied
        from unittest.mock import patch, MagicMock

        mock_conn = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.get_current_revision.return_value = "008_create_reply_drafts"
        mock_script = MagicMock()
        mock_script.get_current_head.return_value = "008_create_reply_drafts"
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s, *a: mock_conn
        mock_engine.connect.return_value.__exit__ = lambda s, *a: None

        with patch("backend.app.core.config.settings") as mock_settings, \
             patch("backend.app.db.session.engine", mock_engine), \
             patch("alembic.runtime.migration.MigrationContext.configure", return_value=mock_ctx), \
             patch("alembic.script.ScriptDirectory.from_config", return_value=mock_script), \
             patch("alembic.command.upgrade") as mock_upgrade:
            mock_settings.APP_ENV = "development"
            _ensure_migrations_applied()
            mock_upgrade.assert_not_called()

    def test_ensure_migrations_upgrades_when_behind(self):
        """When DB revision is behind HEAD, upgrade is triggered in development mode."""
        from backend.app.main import _ensure_migrations_applied
        from unittest.mock import patch, MagicMock

        mock_conn = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.get_current_revision.return_value = "001_initial"
        mock_script = MagicMock()
        mock_script.get_current_head.return_value = "008_create_reply_drafts"
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s, *a: mock_conn
        mock_engine.connect.return_value.__exit__ = lambda s, *a: None

        with patch("backend.app.core.config.settings") as mock_settings, \
             patch("backend.app.db.session.engine", mock_engine), \
             patch("alembic.runtime.migration.MigrationContext.configure", return_value=mock_ctx), \
             patch("alembic.script.ScriptDirectory.from_config", return_value=mock_script), \
             patch("alembic.command.upgrade") as mock_upgrade:
            mock_settings.APP_ENV = "development"
            _ensure_migrations_applied()
            mock_upgrade.assert_called_once()

    def test_ensure_migrations_no_upgrade_in_production(self):
        """In production mode, auto-migration is skipped (CI/CD responsibility)."""
        from backend.app.main import _ensure_migrations_applied
        from unittest.mock import patch, MagicMock
        from backend.app.core.config import settings as real_settings

        mock_conn = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.get_current_revision.return_value = None  # Empty DB
        mock_script = MagicMock()
        mock_script.get_current_head.return_value = "008_create_reply_drafts"
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s, *a: mock_conn
        mock_engine.connect.return_value.__exit__ = lambda s, *a: None

        # patch.object on the singleton so the local `from ... import settings` binding sees it
        with patch.object(real_settings, "APP_ENV", "production"), \
             patch("backend.app.db.session.engine", mock_engine), \
             patch("alembic.runtime.migration.MigrationContext.configure", return_value=mock_ctx), \
             patch("alembic.script.ScriptDirectory.from_config", return_value=mock_script), \
             patch("alembic.command.upgrade") as mock_upgrade:
            _ensure_migrations_applied()
            # In production, upgrade must NOT be triggered automatically
            mock_upgrade.assert_not_called()
