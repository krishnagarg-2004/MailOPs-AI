"""
Unit tests for Phase 9: Executive Digest & Intelligence Multi-Format Export.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from backend.app.api.v1.digest import _build_digest_data
from backend.app.models.extracted_action import ExtractedAction
from backend.app.models.user import User


def test_build_digest_data_aggregation():
    """Verify digest calculation computes accurate KPIs, pending actions, and risks."""
    user = User(
        id=uuid.uuid4(),
        email="executive@enterprise.com",
        full_name="Executive Leader",
    )

    action1 = ExtractedAction(
        id=uuid.uuid4(),
        user_id=user.id,
        ai_analysis_id=uuid.uuid4(),
        item_type="ACTION",
        description="Renew SSL certificates before expiration",
        assignee="devops@enterprise.com",
        severity_or_priority="HIGH",
        status="PENDING",
        evidence_snippet="SSL certificates expire on Friday",
        created_at=datetime.now(timezone.utc),
    )

    action2 = ExtractedAction(
        id=uuid.uuid4(),
        user_id=user.id,
        ai_analysis_id=uuid.uuid4(),
        item_type="ACTION",
        description="Verify Q3 revenue forecast spreadsheet",
        assignee="finance@enterprise.com",
        severity_or_priority="MEDIUM",
        status="COMPLETED",
        evidence_snippet="Please check the revenue forecast tab",
        created_at=datetime.now(timezone.utc),
    )

    risk1 = ExtractedAction(
        id=uuid.uuid4(),
        user_id=user.id,
        ai_analysis_id=uuid.uuid4(),
        item_type="RISK",
        description="Potential SLA breach if vendor delivery is delayed",
        severity_or_priority="HIGH",
        status="PENDING",
        evidence_snippet="Vendor warned of supply chain disruption",
        created_at=datetime.now(timezone.utc),
    )

    decision1 = ExtractedAction(
        id=uuid.uuid4(),
        user_id=user.id,
        ai_analysis_id=uuid.uuid4(),
        item_type="DECISION",
        description="Approved migration to cloud-native worker queues",
        severity_or_priority="LOW",
        status="CONFIRMED",
        evidence_snippet="Board approved cloud migration roadmap",
        created_at=datetime.now(timezone.utc),
    )

    # Mock DB Session
    mock_db = MagicMock()
    # Return count 1 for AI analyses
    # Then all_items
    # Then sum of financial total = 14500.0
    mock_db.execute.side_effect = [
        MagicMock(scalar=lambda: 1),  # count analyses
        MagicMock(scalars=lambda: MagicMock(all=lambda: [action1, action2, risk1, decision1])),  # actions query
        MagicMock(scalar=lambda: 14500.50),  # financial sum
    ]

    digest = _build_digest_data(user, mock_db)

    assert digest["user_email"] == "executive@enterprise.com"
    assert digest["total_emails_analyzed"] == 1
    assert digest["total_actions"] == 2
    assert digest["pending_actions"] == 1
    assert digest["completed_actions"] == 1
    assert digest["total_risks"] == 1
    assert digest["high_severity_risks"] == 1
    assert digest["total_decisions"] == 1
    assert digest["total_financial_value"] == 14500.50
    assert len(digest["top_actions"]) == 2
    assert len(digest["active_risks"]) == 1
    assert len(digest["recent_decisions"]) == 1


@pytest.mark.asyncio
async def test_digest_export_csv_and_markdown():
    """Verify CSV and Markdown formats generate valid executive outputs."""
    from backend.app.api.v1.digest import export_digest

    user = User(
        id=uuid.uuid4(),
        email="leader@company.com",
        full_name="Team Leader",
    )

    action = ExtractedAction(
        id=uuid.uuid4(),
        user_id=user.id,
        ai_analysis_id=uuid.uuid4(),
        item_type="ACTION",
        description="Submit monthly compliance filings",
        assignee="compliance@company.com",
        severity_or_priority="HIGH",
        status="PENDING",
        evidence_snippet="Due before end of quarter",
        created_at=datetime.now(timezone.utc),
    )

    mock_db = MagicMock()
    mock_db.execute.side_effect = [
        MagicMock(scalar=lambda: 5),  # 5 emails
        MagicMock(scalars=lambda: MagicMock(all=lambda: [action])),  # items
        MagicMock(scalar=lambda: 25000.0),  # financial
        MagicMock(scalar=lambda: 5),
        MagicMock(scalars=lambda: MagicMock(all=lambda: [action])),
        MagicMock(scalar=lambda: 25000.0),
    ]

    # Test CSV Export
    csv_resp = await export_digest(format="csv", current_user=user, db=mock_db)
    assert csv_resp.media_type == "text/csv"
    assert "attachment; filename=\"mailops-executive-digest.csv\"" in csv_resp.headers["Content-Disposition"]
    csv_text = csv_resp.body.decode("utf-8")
    assert "Submit monthly compliance filings" in csv_text
    assert "compliance@company.com" in csv_text

    # Test Markdown Export
    md_resp = await export_digest(format="markdown", current_user=user, db=mock_db)
    assert md_resp.media_type == "text/markdown"
    assert "attachment; filename=\"mailops-executive-digest.md\"" in md_resp.headers["Content-Disposition"]
    md_text = md_resp.body.decode("utf-8")
    assert "# MailOps AI — Executive Intelligence Digest" in md_text
    assert "Submit monthly compliance filings" in md_text
    assert "$25,000.00" in md_text
