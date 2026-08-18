from pathlib import Path
import uuid
import pytest
from sqlalchemy.orm import Session
from backend.app.models.attachment import Attachment
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.user import User
from backend.app.services.business_document_ai_service import BusinessDocumentAIService
from backend.app.services.document_service import DocumentProcessingService
from backend.tests.integration.test_database import db_session, test_engine


@pytest.fixture
def sample_user_and_attachment(db_session: Session, tmp_path: Path):
    user = User(
        email=f"doc_user_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Doc User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    thread = EmailThread(
        user_id=user.id,
        gmail_thread_id=f"thread_doc_{uuid.uuid4().hex[:8]}",
        snippet="Doc Thread",
    )
    db_session.add(thread)
    db_session.commit()
    db_session.refresh(thread)

    message = EmailMessage(
        user_id=user.id,
        thread_id=thread.id,
        gmail_message_id=f"msg_doc_{uuid.uuid4().hex[:8]}",
        gmail_thread_id=thread.gmail_thread_id,
        sender="billing@supplier.com",
        subject="Attached Invoice PDF",
        body_plain="Please see attached invoice.",
        has_attachments=True,
    )
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)

    # Create dummy disk file
    sample_file = tmp_path / "sample_doc.txt"
    sample_file.write_text("--- [Page 1] ---\nInvoice #9921 Total Due: $4,500.00 Vendor: Acme Enterprise Solutions", encoding="utf-8")

    attachment = Attachment(
        user_id=user.id,
        message_id=message.id,
        filename="sample_doc.pdf",
        mime_type="application/pdf",
        size_bytes=100,
        storage_path=str(sample_file),
        is_downloaded=True,
    )
    db_session.add(attachment)
    db_session.commit()
    db_session.refresh(attachment)

    return user, thread, message, attachment, sample_file


@pytest.mark.asyncio
async def test_document_processing_and_business_ai_service(db_session: Session, sample_user_and_attachment):
    user, thread, message, attachment, sample_file = sample_user_and_attachment

    # Test processing attachment (mock handling text file)
    # We directly create/verify DocumentExtraction persistence
    extraction = DocumentProcessingService.get_extraction(db_session, user.id, attachment.id)
    assert extraction is None

    # Manually trigger process
    from backend.app.models.document_extraction import DocumentExtraction
    extraction_obj = DocumentExtraction(
        user_id=user.id,
        attachment_id=attachment.id,
        email_message_id=message.id,
        file_type="PDF",
        extraction_method="NATIVE_TEXT",
        extracted_text=sample_file.read_text(encoding="utf-8"),
        char_count=100,
        page_count=1,
        is_ocr_applied=False,
        status="COMPLETED",
    )
    db_session.add(extraction_obj)
    db_session.commit()
    db_session.refresh(extraction_obj)

    # Test Business Document AI Service (Layer 2)
    biz_service = BusinessDocumentAIService()
    biz_result = await biz_service.analyze_business_document(db_session, user.id, attachment.id)

    assert biz_result.document_category == "INVOICE"
    assert biz_result.financial_total == 4500.0
    assert biz_result.vendor_or_party == "Acme Enterprise Solutions"
    assert biz_result.status == "COMPLETED"
