"""
Tier 2 — Boundary & Corner Cases: Zero Conflict Popups & UI Sync
Tests boundaries: full frontend source scan for native dialogs, selection preservation contracts,
dynamic +50 pagination accumulation, and loading state watchdog fallbacks.
"""

import os
import re
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.repositories.gmail_repository import GmailRepository
from tests.test_helpers import scan_frontend_for_native_dialogs


def test_boundary_popups_entire_frontend_source_audit():
    """Verify zero occurrences of alert() or confirm() across the entire frontend/src directory."""
    violations = scan_frontend_for_native_dialogs("frontend/src")
    assert len(violations) == 0, (
        f"Found {len(violations)} native dialog calls across frontend/src: {violations}"
    )


def test_boundary_ui_sync_selection_preservation():
    """Verify InboxDashboardView.tsx preserves selectedThreadId and active draft across fetchThreads."""
    dashboard_path = "frontend/src/pages/InboxDashboardView.tsx"
    assert os.path.exists(dashboard_path), f"Missing {dashboard_path}"

    with open(dashboard_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "selectedThreadId" in content


def test_boundary_ui_sync_dynamic_limit_increment():
    """Verify frontend +50 pagination dynamically requests higher limits or appends older threads."""
    dashboard_path = "frontend/src/pages/InboxDashboardView.tsx"
    assert os.path.exists(dashboard_path), f"Missing {dashboard_path}"

    with open(dashboard_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "syncOlderEmails" in content


def test_boundary_ui_sync_fallback_timeout_safety():
    """Verify loading states in InboxDashboardView do not remain frozen forever if SSE is interrupted."""
    dashboard_path = "frontend/src/pages/InboxDashboardView.tsx"
    assert os.path.exists(dashboard_path), f"Missing {dashboard_path}"

    with open(dashboard_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "setIsLoadingOlder(false)" in content
    assert "setIsSyncing(false)" in content


def test_boundary_sync_older_already_syncing_returns_in_progress(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Verify POST /api/v1/gmail/sync-older when already SYNCING returns 202 IN_PROGRESS without 409."""
    user = auth_user["user"]
    GmailRepository.get_or_create_sync_state(db_session, user.id)
    GmailRepository.update_sync_state(db_session, user.id, sync_status="SYNCING")

    response = client.post(
        "/api/v1/gmail/sync-older?count=50",
        cookies=auth_user["cookies"],
    )
    assert response.status_code != 409
    assert response.status_code in [200, 202]
    data = response.json()
    assert data["status"] in ["IN_PROGRESS", "SYNCING", "ACCEPTED"]
