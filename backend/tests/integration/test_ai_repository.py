import uuid
import pytest
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.models.email_thread import EmailThread
from backend.app.models.email_message import EmailMessage
from backend.app.repositories.ai_repository import AIRepository
from backend.app.services.ai_extraction_service import AIExtractionService
from backend.app.ai.provider import MockAIProvider
from backend.tests.integration.test_database import db_session, test_engine


@pytest.fixture
def sample_user_and_message(db_session: Session):
    user = User(
        email=f"user_{uuid.uuid4().hex[:8]}@example.com",
        full_name="AI Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    thread = EmailThread(
        user_id=user.id,
        gmail_thread_id=f"thread_{uuid.uuid4().hex[:8]}",
        snippet="Test thread snippet",
    )
    db_session.add(thread)
    db_session.commit()
    db_session.refresh(thread)

    message = EmailMessage(
        user_id=user.id,
        thread_id=thread.id,
        gmail_message_id=f"msg_{uuid.uuid4().hex[:8]}",
        gmail_thread_id=thread.gmail_thread_id,
        sender="billing@vendor.com",
        subject="Invoice #101 Payment Request",
        body_plain="Please pay invoice #101 by 2026-08-30.",
        snippet="Please pay invoice #101 by 2026-08-30.",
    )
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)

    return user, thread, message


@pytest.mark.asyncio
async def test_ai_extraction_service_and_repository(db_session: Session, sample_user_and_message):
    user, thread, message = sample_user_and_message
    service = AIExtractionService(provider=MockAIProvider())

    analysis = await service.analyze_message(db_session, user.id, message.id)

    assert analysis.user_id == user.id
    assert analysis.email_message_id == message.id
    assert analysis.status == "COMPLETED"
    assert len(analysis.extracted_items) > 0
    assert analysis.extracted_items[0].is_evidence_valid is True

    # Test Idempotency: Re-analyzing same message with same model/prompt version should return existing record
    re_analysis = await service.analyze_message(db_session, user.id, message.id)
    assert re_analysis.id == analysis.id


@pytest.mark.asyncio
async def test_update_action_status(db_session: Session, sample_user_and_message):
    user, thread, message = sample_user_and_message
    service = AIExtractionService(provider=MockAIProvider())
    analysis = await service.analyze_message(db_session, user.id, message.id)
    action_item = analysis.extracted_items[0]

    updated = AIRepository.update_action_status(
        db=db_session,
        user_id=user.id,
        action_id=action_item.id,
        new_status="CONFIRMED",
    )

    assert updated is not None
    assert updated.status == "CONFIRMED"
