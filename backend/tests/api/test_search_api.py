import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.user import User
from backend.app.services.auth_service import create_user_session
from backend.app.services.vector_search_service import VectorSearchService
from backend.tests.integration.test_database import db_session, test_engine

client = TestClient(app)


def test_search_api_unauthenticated_returns_401():
    response = client.post("/api/v1/search/semantic", json={"query": "invoice"})
    assert response.status_code == 401


def test_search_api_semantic_hybrid_rag_flow(db_session: Session):
    user = User(
        email=f"search_api_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Search API User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

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
        sender="legal@vendor.com",
        subject="Vendor Master Service Agreement",
        body_plain="Agreement between Alpha Corp and Beta Solutions effective September 1 2026.",
        has_attachments=False,
    )
    db_session.add(message)
    db_session.commit()

    # Index message into pgvector
    vec_service = VectorSearchService()
    vec_service.index_email_message(db_session, user.id, message.id)

    cookies = {"mailops_session": session_token}

    # Test POST /api/v1/search/semantic
    sem_res = client.post(
        "/api/v1/search/semantic",
        json={"query": "Service Agreement", "top_k": 5},
        cookies=cookies,
    )
    assert sem_res.status_code == 200
    sem_data = sem_res.json()
    assert len(sem_data) >= 1
    assert "Alpha Corp" in sem_data[0]["chunk_text"]

    # Test POST /api/v1/search/hybrid
    hyb_res = client.post(
        "/api/v1/search/hybrid",
        json={"query": "Alpha Corp", "top_k": 5},
        cookies=cookies,
    )
    assert hyb_res.status_code == 200
    assert len(hyb_res.json()) >= 1

    # Test POST /api/v1/search/rag-query
    rag_res = client.post(
        "/api/v1/search/rag-query",
        json={"query": "When is the agreement effective?", "top_k": 5},
        cookies=cookies,
    )
    assert rag_res.status_code == 200
    rag_data = rag_res.json()
    assert "answer" in rag_data
    assert len(rag_data["citations"]) >= 1
