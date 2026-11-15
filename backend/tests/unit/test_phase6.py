"""
Unit tests for Phase 6: Precision Reranker, Agentic Tools, and Calendar Synchronization.
"""

from unittest.mock import MagicMock
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.ai.agent_tools import AgentToolRegistry
from backend.app.db.base import Base
from backend.app.models.business_document_extraction import BusinessDocumentExtraction
from backend.app.models.document_extraction import DocumentExtraction
from backend.app.models.attachment import Attachment
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.extracted_action import ExtractedAction
from backend.app.models.user import User
from backend.app.services.calendar_service import CalendarSyncService
from backend.app.services.reranker import CrossEncoderReranker


@pytest.fixture
def in_memory_db():
    """Provides an isolated SQLite in-memory database."""
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_cross_encoder_reranker_relevance_ordering():
    """Verify that candidates with exact query terms and phrase matches rank highest."""
    query = "VAT tax return deadline Friday"

    candidates = [
        {
            "chunk_text": "Random status update about weekly frontend build changes.",
            "source_name": "Weekly Update",
            "similarity_score": 0.85,
        },
        {
            "chunk_text": "Please make sure to file the VAT tax return before the deadline Friday.",
            "source_name": "VAT Filing Email",
            "similarity_score": 0.60,
        },
        {
            "chunk_text": "Lunch order form for team gathering on Friday.",
            "source_name": "Social",
            "similarity_score": 0.70,
        },
    ]

    reranked = CrossEncoderReranker.rerank(query=query, candidates=candidates, top_n=3)

    assert len(reranked) == 3
    # The VAT Filing email should jump to 1st place despite lower initial vector score
    assert reranked[0]["source_name"] == "VAT Filing Email"
    assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]


def test_agent_tools_lookup_previous_invoice(in_memory_db):
    """Verify agent tool successfully retrieves invoice historical data."""
    user = User(email="test.user@mailops.io", is_active=True)
    in_memory_db.add(user)
    in_memory_db.commit()

    thread = EmailThread(user_id=user.id, gmail_thread_id="t_inv_1")
    in_memory_db.add(thread)
    in_memory_db.commit()

    msg = EmailMessage(
        user_id=user.id,
        thread_id=thread.id,
        gmail_message_id="m_inv_1",
        gmail_thread_id="t_inv_1",
    )
    in_memory_db.add(msg)
    in_memory_db.commit()

    att = Attachment(
        user_id=user.id,
        message_id=msg.id,
        filename="Apex_Invoice.pdf",
    )
    in_memory_db.add(att)
    in_memory_db.commit()

    doc_ext = DocumentExtraction(
        user_id=user.id,
        attachment_id=att.id,
        email_message_id=msg.id,
        file_type="PDF",
        extracted_text="Invoice Details",
    )
    in_memory_db.add(doc_ext)
    in_memory_db.commit()

    biz_ext = BusinessDocumentExtraction(
        user_id=user.id,
        attachment_id=att.id,
        document_extraction_id=doc_ext.id,
        document_category="INVOICE",
        vendor_or_party="Apex Data Systems",
        document_reference_number="INV-2026-999",
        extracted_data={"total_amount": 12500.0, "currency": "USD"},
    )
    in_memory_db.add(biz_ext)
    in_memory_db.commit()

    tool_res = AgentToolRegistry.execute_tool_call(
        db=in_memory_db,
        user_id=user.id,
        tool_name="lookup_previous_invoice",
        arguments={"vendor_name": "Apex Data"},
    )

    assert tool_res["found"] is True
    assert len(tool_res["invoices"]) == 1
    assert tool_res["invoices"][0]["invoice_number"] == "INV-2026-999"
    assert tool_res["invoices"][0]["total_amount"] == 12500.0


def test_calendar_sync_service_schedules_action(in_memory_db):
    """Verify action item scheduling updates status and generates Google Calendar URL."""
    user = User(email="test.calendar@mailops.io", is_active=True)
    in_memory_db.add(user)
    in_memory_db.commit()

    action = ExtractedAction(
        user_id=user.id,
        ai_analysis_id=uuid.uuid4(),
        item_type="ACTION",
        description="Submit Q4 budget proposal",
        status="PENDING",
        evidence_snippet="Submit Q4 budget proposal by Monday",
    )
    in_memory_db.add(action)
    in_memory_db.commit()

    sched_res = CalendarSyncService.schedule_action_item(
        db=in_memory_db,
        user=user,
        action_id=action.id,
    )

    assert sched_res["status"] == "SCHEDULED"
    assert "calendar.google.com" in sched_res["calendar_url"]
    assert action.status == "CONFIRMED"
