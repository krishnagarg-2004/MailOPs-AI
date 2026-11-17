"""
Endpoint Verification Script for Milestone 1.

Validates that:
1. GET /api/v1/reply-drafts/message/{id} returns 200 OK with normalized provenance.
2. POST /api/v1/gmail/sync returns 202 Accepted.
3. POST /api/v1/gmail/sync-older?count=50 returns 202 Accepted and creates 50 older emails.
4. SSE event stream receives sync_completed without hanging.
"""

import asyncio
import uuid
from datetime import datetime, timezone
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.api.deps import get_current_user
from backend.app.core.crypto import encrypt_token
from backend.app.core.events import event_bus
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.oauth import OAuthAccount
from backend.app.models.reply_draft import ReplyDraft
from backend.app.models.user import User


async def run_verification():
    print("\n" + "=" * 60)
    print("STARTING MILESTONE 1 BACKEND ENDPOINT VERIFICATION")
    print("=" * 60)

    # 1. Setup in-memory test database and session
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    # 2. Setup demo user and OAuth credentials
    demo_user = User(
        id=uuid.uuid4(),
        email="alex.morgan@enterprise-mailops.io",
        full_name="Alex Morgan (VP of Product Operations)",
        is_active=True,
    )
    db.add(demo_user)
    db.commit()

    oauth_acc = OAuthAccount(
        user_id=demo_user.id,
        provider="google",
        provider_account_id="demo_google_sub_109283746",
        email=demo_user.email,
        encrypted_access_token=encrypt_token("mock_access_token_demo"),
        encrypted_refresh_token=encrypt_token("mock_refresh_token_demo"),
    )
    db.add(oauth_acc)

    # 3. Setup baseline thread & message
    now = datetime.now(timezone.utc)
    thread = EmailThread(
        id=uuid.uuid4(),
        user_id=demo_user.id,
        gmail_thread_id="th_demo_base_001",
        snippet="Payment cluster rate limit alert",
        last_message_at=now,
    )
    db.add(thread)
    db.commit()

    message = EmailMessage(
        id=uuid.uuid4(),
        user_id=demo_user.id,
        thread_id=thread.id,
        gmail_message_id="msg_demo_base_001",
        gmail_thread_id=thread.gmail_thread_id,
        sender="stripe-alerts@partner.com",
        recipients=demo_user.email,
        subject="Payment cluster rate limits exceeded",
        snippet="Payment cluster rate limits exceeded",
        body_plain="Rate limits reached 95% threshold on billing cluster.",
        received_at=now,
    )
    db.add(message)
    db.commit()

    # 4. Setup reply draft with plain string rationale_and_provenance (the previous 500 bug condition)
    draft = ReplyDraft(
        id=uuid.uuid4(),
        user_id=demo_user.id,
        email_thread_id=thread.id,
        email_message_id=message.id,
        subject="Re: Payment cluster rate limits exceeded",
        body_text="We have stabilized the rate limit configurations.",
        recipient_email="stripe-alerts@partner.com",
        intent="REPLY_RESPONSE",
        tone="PROFESSIONAL",
        status="DRAFTED",
        rationale_and_provenance=[
            "Drafted to de-escalate payment cluster rate limits and confirm threshold stabilization."
        ],
    )
    db.add(draft)
    db.commit()

    # Override FastAPI dependencies
    def override_get_db():
        try:
            yield db
        finally:
            pass

    def override_get_current_user():
        return demo_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Also override SessionLocal inside background tasks to use our in-memory engine
    import backend.app.db.session as session_mod
    orig_session_local = session_mod.SessionLocal
    session_mod.SessionLocal = TestingSession

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # TEST 1: GET /api/v1/reply-drafts/message/{id}
            print("\n[VERIFY 1] Testing GET /api/v1/reply-drafts/message/{id}...")
            resp = await client.get(f"/api/v1/reply-drafts/message/{message.id}")
            print(f"Status: {resp.status_code}")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert isinstance(data, list) and len(data) == 1
            prov = data[0]["rationale_and_provenance"]
            assert len(prov) == 1
            assert isinstance(prov[0], dict)
            assert "de-escalate payment cluster" in prov[0]["description"]
            print("  --> PASS: Returned 200 OK with normalized provenance dictionaries (no 500!).")

            # TEST 2: POST /api/v1/gmail/sync
            print("\n[VERIFY 2] Testing POST /api/v1/gmail/sync...")
            resp_sync = await client.post("/api/v1/gmail/sync")
            print(f"Status: {resp_sync.status_code}")
            assert resp_sync.status_code == 202, f"Expected 202, got {resp_sync.status_code}: {resp_sync.text}"
            sync_data = resp_sync.json()
            assert sync_data["status"] in ("ACCEPTED", "IN_PROGRESS")
            print(f"Response: {sync_data}")
            print("  --> PASS: Returned 202 Accepted for background mailbox sync.")

            # TEST 3: POST /api/v1/gmail/sync-older?count=50
            print("\n[VERIFY 3] Testing POST /api/v1/gmail/sync-older?count=50...")
            queue = await event_bus.subscribe(demo_user.id)
            resp_older = await client.post("/api/v1/gmail/sync-older?count=50")
            print(f"Status: {resp_older.status_code}")
            assert resp_older.status_code == 202, f"Expected 202, got {resp_older.status_code}: {resp_older.text}"
            older_data = resp_older.json()
            assert older_data["status"] == "ACCEPTED"
            print(f"Response: {older_data}")
            print("  --> PASS: Returned 202 Accepted for background older email sync.")

            # Wait briefly for background task to complete and SSE event to arrive
            print("\n[VERIFY 4] Waiting for background task and sync_completed event...")
            completed_received = False
            for _ in range(30):
                await asyncio.sleep(0.1)
                while not queue.empty():
                    evt = queue.get_nowait()
                    if evt.get("event") == "sync_completed":
                        completed_received = True
                        print(f"  Received event: {evt}")
                        break
                if completed_received:
                    break

            await event_bus.unsubscribe(demo_user.id, queue)
            assert completed_received, "Expected sync_completed SSE event was not received!"
            print("  --> PASS: sync_completed event received cleanly.")

            # TEST 5: Verify 50 older messages exist in database
            total_msgs = db.query(EmailMessage).filter(EmailMessage.user_id == demo_user.id).count()
            print(f"\n[VERIFY 5] Checking synthesized older emails count in DB: {total_msgs} messages")
            assert total_msgs == 51, f"Expected 51 messages (1 baseline + 50 older), found {total_msgs}"
            print("  --> PASS: Exactly 50 older historical emails synthesized with valid metadata.")

    finally:
        session_mod.SessionLocal = orig_session_local
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=engine)

    print("\n" + "=" * 60)
    print("ALL MILESTONE 1 ENDPOINT CHECKS PASSED SUCCESSFULLY (2xx responses, 0 errors)!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_verification())
