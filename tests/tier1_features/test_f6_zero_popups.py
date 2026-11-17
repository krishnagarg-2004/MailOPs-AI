"""
Tier 1 — Feature 6: Zero Conflict Popups & UI Sync
Specification: ORIGINAL_REQUEST.md §R2, PROJECT.md §Zero Conflict Popup Contract
Enforces the elimination of native browser alert() and confirm() popups across frontend views
and verifies non-blocking backend synchronization responses.
"""

import os
import re
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from backend.app.models.gmail_sync_state import GmailSyncState
from backend.app.repositories.gmail_repository import GmailRepository
from tests.test_helpers import scan_frontend_for_native_dialogs


def test_f6_1_no_alert_in_inbox_dashboard():
    """Verify InboxDashboardView.tsx contains zero native alert() calls."""
    violations = scan_frontend_for_native_dialogs("frontend/src/pages")
    dashboard_alerts = [
        v for v in violations
        if "InboxDashboardView" in v["file"] and v["dialog_type"] == "alert"
    ]
    assert len(dashboard_alerts) == 0, (
        f"Found {len(dashboard_alerts)} native alert() calls in InboxDashboardView: {dashboard_alerts}"
    )


def test_f6_2_no_confirm_in_inbox_dashboard():
    """Verify InboxDashboardView.tsx contains zero native confirm() calls."""
    violations = scan_frontend_for_native_dialogs("frontend/src/pages")
    dashboard_confirms = [
        v for v in violations
        if "InboxDashboardView" in v["file"] and v["dialog_type"] == "confirm"
    ]
    assert len(dashboard_confirms) == 0, (
        f"Found {len(dashboard_confirms)} native confirm() calls in InboxDashboardView: {dashboard_confirms}"
    )


def test_f6_3_no_alert_in_gmail_sync_widget():
    """Verify GmailSyncWidget.tsx contains zero native alert() calls."""
    violations = scan_frontend_for_native_dialogs("frontend/src/components")
    widget_alerts = [
        v for v in violations
        if "GmailSyncWidget" in v["file"] and v["dialog_type"] == "alert"
    ]
    assert len(widget_alerts) == 0, (
        f"Found {len(widget_alerts)} native alert() calls in GmailSyncWidget: {widget_alerts}"
    )


def test_f6_4_no_dialogs_in_layout_and_commands():
    """Verify Layout.tsx and CommandPalette.tsx do not use native alert() or confirm()."""
    violations = scan_frontend_for_native_dialogs("frontend/src/components")
    layout_violations = [
        v for v in violations
        if ("Layout" in v["file"] or "CommandPalette" in v["file"])
    ]
    assert len(layout_violations) == 0, (
        f"Found {len(layout_violations)} native dialogs in Layout/CommandPalette: {layout_violations}"
    )


def test_f6_5_backend_sync_does_not_return_409(
    client: TestClient,
    auth_user: dict,
    db_session: Session,
):
    """Verify triggering sync when already syncing returns IN_PROGRESS (202), NEVER HTTP 409 Conflict."""
    user = auth_user["user"]
    # Force sync_status to SYNCING
    GmailRepository.get_or_create_sync_state(db_session, user.id)
    GmailRepository.update_sync_state(db_session, user.id, sync_status="SYNCING")

    response = client.post(
        "/api/v1/gmail/sync",
        cookies=auth_user["cookies"],
    )
    # Must NOT be 409 Conflict
    assert response.status_code != 409, "Backend must not return HTTP 409 Conflict on concurrent sync!"
    assert response.status_code in [200, 202]
    data = response.json()
    assert data["status"] in ["IN_PROGRESS", "SYNCING", "ACCEPTED"]
