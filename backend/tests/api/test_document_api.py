from pathlib import Path
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.app.models.attachment import Attachment
from backend.app.models.business_document_extraction import BusinessDocumentExtraction
from backend.app.models.document_extraction import DocumentExtraction
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.user import User
from backend.app.services.auth_service import create_user_session
from backend.tests.integration.test_database import db_session, test_engine

client = TestClient(app)


def test_document_api_unauthenticated_returns_401():
    fake_id = uuid.uuid4()
    response = client.get(f"/api/v1/documents/extraction/{fake_id}")
    assert response.status_code == 401


def test_document_api_extraction_and_business_analysis_flow(db_session: Session, tmp_path: Path):
    # Setup test user & session
    user = User(
        email=f"doc_api_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Doc API User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    session_token, _ = create_user_session(db_session, user)

    thread = EmailThread(
        user_id=user.id,
        gmail_thread_id=f"thread_api_{uuid.uuid4().hex[:8]}",
        snippet="API Thread",
    )
    db_session.add(thread)
    db_session.commit()

    message = EmailMessage(
        user_id=user.id,
        thread_id=thread.id,
        gmail_message_id=f"msg_api_{uuid.uuid4().hex[:8]}",
        gmail_thread_id=thread.gmail_thread_id,
        sender="vendor@company.com",
        subject="Invoice #8831 Attachment",
        body_plain="Please see attached invoice.",
        has_attachments=True,
    )
    db_session.add(message)
    db_session.commit()

    doc_file = tmp_path / "invoice_8831.docx"
    doc_file.write_bytes(b"dummy")  # dummy file on disk

    attachment = Attachment(
        user_id=user.id,
        message_id=message.id,
        filename="invoice_8831.docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=100,
        storage_path=str(doc_file),
        is_downloaded=True,
    )
    db_session.add(attachment)
    db_session.commit()

    # Pre-seed Layer 1 document extraction
    extraction = DocumentExtraction(
        user_id=user.id,
        attachment_id=attachment.id,
        email_message_id=message.id,
        file_type="DOCX",
        extraction_method="NATIVE_TEXT",
        extracted_text="--- [Page 1] ---\nINVOICE #8831 Vendor: Acme Software Total Due: $1,200.00",
        char_count=65,
        page_count=1,
        is_ocr_applied=False,
        status="COMPLETED",
    )
    db_session.add(extraction)
    db_session.commit()

    cookies = {"mailops_session": session_token}

    # Test GET Layer 1 extraction endpoint
    get_res = client.get(f"/api/v1/documents/extraction/{attachment.id}", cookies=cookies)
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["attachment_id"] == str(attachment.id)
    assert data["file_type"] == "DOCX"
    assert "INVOICE #8831" in data["extracted_text"]

    # Test POST Layer 2 business document analysis endpoint
    post_biz = client.post(f"/api/v1/documents/analyze-business-doc/{attachment.id}", cookies=cookies)
    assert post_biz.status_code == 200
    biz_data = post_biz.json()
    assert biz_data["document_category"] == "INVOICE"
    assert biz_data["financial_total"] == 4500.0

    # Test GET Layer 2 business document endpoint
    get_biz = client.get(f"/api/v1/documents/business-doc/{attachment.id}", cookies=cookies)
    assert get_biz.status_code == 200
    assert get_biz.json()["attachment_id"] == str(attachment.id)
