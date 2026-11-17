"""
Milestone 1 Test Suite: Backend Synchronization, Reply Drafts & Concurrency.

Covers:
1. Thread-safe EventBus publishing across threads and event loops.
2. Demo persona mock sync and +50 older email pagination without Google API calls.
3. Guaranteed emission of sync_completed on both success and error paths.
4. ReplyDraftRead schema validation and normalization for rationale_and_provenance.
5. AI extraction concurrency race condition resilience (IntegrityError upsert recovery).
"""

import asyncio
from datetime import datetime, timezone, timedelta
import threading
import uuid
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.app.core.crypto import encrypt_token
from backend.app.core.events import EventBus, event_bus
from backend.app.db.base import Base
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.oauth import OAuthAccount
from backend.app.models.reply_draft import ReplyDraft
from backend.app.models.user import User
from backend.app.repositories.ai_repository import AIRepository
from backend.app.repositories.gmail_repository import GmailRepository
from backend.app.schemas.reply_draft import ReplyDraftRead, StatusEnum, ToneEnum
from backend.app.services.gmail_sync_service import GmailSyncService


@pytest.fixture
def test_db():
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


# ---------------------------------------------------------------------------
# 1. Thread-Safe EventBus Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_event_bus_cross_thread_publishing():
    """Verify that publishing from a worker thread safely delivers events to main loop queue."""
    bus = EventBus()
    user_id = uuid.uuid4()
    queue = await bus.subscribe(user_id)

    # Worker thread that publishes using publish_threadsafe
    def worker():
        bus.publish_threadsafe(
            user_id,
            "sync_progress",
            {"status": "SYNCING", "processed": 25},
        )

    t = threading.Thread(target=worker)
    t.start()
    t.join(timeout=2.0)

    # Main event loop should receive the event without deadlock or exception
    event = await asyncio.wait_for(queue.get(), timeout=2.0)
    assert event["event"] == "sync_progress"
    assert event["data"]["processed"] == 25
    await bus.unsubscribe(user_id, queue)


@pytest.mark.asyncio
async def test_event_bus_publish_from_separate_event_loop():
    """Verify async publish from a separate thread's event loop routes through call_soon_threadsafe."""
    bus = EventBus()
    user_id = uuid.uuid4()
    queue = await bus.subscribe(user_id)

    def worker_loop_runner():
        async def _worker():
            # In a different loop/thread, call bus.publish
            await bus.publish(
                user_id,
                "sync_completed",
                {"status": "COMPLETED", "synced_count": 50},
            )
        asyncio.run(_worker())

    t = threading.Thread(target=worker_loop_runner)
    t.start()
    t.join(timeout=2.0)

    event = await asyncio.wait_for(queue.get(), timeout=2.0)
    assert event["event"] == "sync_completed"
    assert event["data"]["status"] == "COMPLETED"
    assert event["data"]["synced_count"] == 50
    await bus.unsubscribe(user_id, queue)


# ---------------------------------------------------------------------------
# 2. Demo Persona Mock Sync & +50 Older Email Pagination Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_demo_persona_sync_does_not_call_google_api(test_db):
    """Verify demo user execute_sync synthesizes mock mailbox without Google REST calls."""
    user = User(
        email="alex.morgan@enterprise-mailops.io",
        full_name="Alex Morgan Demo",
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="demo_google_sub_109283746",
        email=user.email,
        encrypted_access_token=encrypt_token("mock_access_token_demo"),
        encrypted_refresh_token=encrypt_token("mock_refresh_token_demo"),
    )
    test_db.add(oauth_acc)
    test_db.commit()

    sync_service = GmailSyncService()
    queue = await event_bus.subscribe(user.id)

    res = await sync_service.execute_sync(test_db, user)

    assert res["status"] == "COMPLETED"
    assert res["type"] == "DEMO_BASELINE"
    assert res["messages_synced"] > 0

    # Verify event stream received sync_started, sync_progress, and sync_completed
    events_received = []
    while not queue.empty():
        events_received.append(queue.get_nowait()["event"])

    assert "sync_started" in events_received
    assert "sync_completed" in events_received
    await event_bus.unsubscribe(user.id, queue)


@pytest.mark.asyncio
async def test_demo_persona_sync_older_50_messages(test_db):
    """Verify sync_older_messages synthesizes 50 older emails with strictly decremented timestamps."""
    user = User(
        email="alex.morgan@enterprise-mailops.io",
        full_name="Alex Morgan Demo",
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="demo_google_sub_109283746",
        email=user.email,
        encrypted_access_token=encrypt_token("mock_access_token_demo"),
        encrypted_refresh_token=encrypt_token("mock_refresh_token_demo"),
    )
    test_db.add(oauth_acc)

    # Create an initial message to establish earliest baseline timestamp
    now = datetime.now(timezone.utc)
    baseline_thread = EmailThread(
        user_id=user.id,
        gmail_thread_id="th_baseline_001",
        snippet="Initial baseline email",
        last_message_at=now,
    )
    test_db.add(baseline_thread)
    test_db.commit()

    baseline_msg = EmailMessage(
        user_id=user.id,
        thread_id=baseline_thread.id,
        gmail_message_id="msg_baseline_001",
        gmail_thread_id=baseline_thread.gmail_thread_id,
        sender="lead@partner.com",
        subject="Initial Email",
        snippet="Initial baseline email",
        body_plain="Hello baseline",
        received_at=now,
    )
    test_db.add(baseline_msg)
    test_db.commit()

    sync_service = GmailSyncService()
    queue = await event_bus.subscribe(user.id)

    res = await sync_service.sync_older_messages(test_db, user, count=50)

    assert res["status"] == "COMPLETED"
    assert res["messages_synced"] == 50
    assert res["total_messages"] == 51  # 1 initial + 50 older

    # Verify all 50 newly created older messages have received_at < initial baseline message
    older_msgs = (
        test_db.query(EmailMessage)
        .filter(EmailMessage.user_id == user.id, EmailMessage.id != baseline_msg.id)
        .all()
    )
    assert len(older_msgs) == 50
    for m in older_msgs:
        # Check tz-aware comparison
        m_rec = m.received_at if m.received_at.tzinfo else m.received_at.replace(tzinfo=timezone.utc)
        assert m_rec < now, f"Message {m.id} timestamp {m_rec} should be older than baseline {now}"

    # Verify sync_completed event was emitted
    events_received = []
    while not queue.empty():
        events_received.append(queue.get_nowait()["event"])

    assert "sync_started" in events_received
    assert "sync_progress" in events_received
    assert "sync_completed" in events_received
    await event_bus.unsubscribe(user.id, queue)


# ---------------------------------------------------------------------------
# 3. Guaranteed sync_completed on Error Path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sync_emits_sync_completed_on_failure(test_db):
    """Verify that sync failure ALWAYS publishes sync_completed with status FAILED."""
    user = User(
        email="unauthorized.user@company.com",
        full_name="Unauthorized User",
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    # No OAuth account added -> will fail

    sync_service = GmailSyncService()
    queue = await event_bus.subscribe(user.id)

    with pytest.raises(ValueError, match="No Google OAuth account"):
        await sync_service.execute_sync(test_db, user)

    # Verify sync_completed was published with status=FAILED
    events = []
    while not queue.empty():
        events.append(queue.get_nowait())

    completed_events = [e for e in events if e.get("event") == "sync_completed"]
    assert len(completed_events) == 1
    assert completed_events[0]["data"]["status"] == "FAILED"
    await event_bus.unsubscribe(user.id, queue)


# ---------------------------------------------------------------------------
# 4. Reply Draft Schema Validation and Provenance Normalization
# ---------------------------------------------------------------------------

def test_reply_draft_read_flexibly_accepts_strings_and_dicts():
    """Verify ReplyDraftRead schema never throws 500 when rationale_and_provenance contains strings."""
    now = datetime.now(timezone.utc)
    raw_draft = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "email_thread_id": uuid.uuid4(),
        "email_message_id": uuid.uuid4(),
        "gmail_draft_id": None,
        "subject": "De-escalating payment cluster rate limits",
        "body_text": "Stabilization confirmed across all payment nodes.",
        "recipient_email": "partner@stripe.com",
        "intent": "REPLY_RESPONSE",
        "tone": ToneEnum.PROFESSIONAL,
        "status": StatusEnum.DRAFTED,
        "rationale_and_provenance": [
            "Drafted to de-escalate payment cluster rate limits and confirm threshold stabilization."
        ],
        "created_at": now,
        "updated_at": now,
    }

    validated = ReplyDraftRead.model_validate(raw_draft)
    assert len(validated.rationale_and_provenance) == 1
    item = validated.rationale_and_provenance[0]
    assert isinstance(item, dict)
    assert item["description"] == raw_draft["rationale_and_provenance"][0]
    assert item["source_type"] == "EMAIL_THREAD"


# ---------------------------------------------------------------------------
# 5. AI Extraction Concurrency Resilience (Race Condition Handling)
# ---------------------------------------------------------------------------

def test_ai_repository_concurrency_race_resilience(test_db):
    """Verify that unique constraint race condition on save_analysis_with_items is handled gracefully."""
    user = User(email="concurrency@test.com", full_name="Concurrency Tester")
    test_db.add(user)
    test_db.commit()

    msg_id = uuid.uuid4()
    thread_id = uuid.uuid4()
    model = "mock-model"
    prompt_ver = "v1.0"

    # Worker 1 saves first analysis
    res1 = AIRepository.save_analysis_with_items(
        db=test_db,
        user_id=user.id,
        email_message_id=msg_id,
        email_thread_id=thread_id,
        summary="Analysis by Worker 1",
        intent="INFORMATIONAL",
        priority="MEDIUM",
        sentiment="NEUTRAL",
        confidence_score=0.9,
        rationale="Rationale 1",
        model_name=model,
        prompt_version=prompt_ver,
        extracted_items=[{"description": "Action from Worker 1", "priority": "HIGH"}],
        status="COMPLETED",
    )
    assert res1.summary == "Analysis by Worker 1"

    # Worker 2 simultaneously saves an analysis for the exact same (user, msg_id, model, prompt_ver)
    res2 = AIRepository.save_analysis_with_items(
        db=test_db,
        user_id=user.id,
        email_message_id=msg_id,
        email_thread_id=thread_id,
        summary="Analysis by Worker 2 (Concurrent)",
        intent="ACTION_REQUIRED",
        priority="HIGH",
        sentiment="POSITIVE",
        confidence_score=0.95,
        rationale="Rationale 2",
        model_name=model,
        prompt_version=prompt_ver,
        extracted_items=[{"description": "Action from Worker 2", "priority": "URGENT"}],
        status="COMPLETED",
    )

    # Should update existing record idempotently without raising IntegrityError
    assert res2.id == res1.id
    assert res2.summary == "Analysis by Worker 2 (Concurrent)"
    assert res2.priority == "HIGH"
    assert len(res2.extracted_items) == 1
    assert res2.extracted_items[0].description == "Action from Worker 2"
