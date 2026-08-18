import uuid
import pytest
from sqlalchemy.orm import Session
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.user import User
from backend.app.models.vector_embedding import VectorEmbedding
from backend.app.services.rag_service import RAGService
from backend.app.services.vector_search_service import VectorSearchService
from backend.tests.integration.test_database import db_session, test_engine


@pytest.fixture
def sample_user_and_message(db_session: Session):
    user = User(
        email=f"vec_user_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Vector User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    thread = EmailThread(
        user_id=user.id,
        gmail_thread_id=f"thread_vec_{uuid.uuid4().hex[:8]}",
        snippet="Vector Thread",
    )
    db_session.add(thread)
    db_session.commit()

    message = EmailMessage(
        user_id=user.id,
        thread_id=thread.id,
        gmail_message_id=f"msg_vec_{uuid.uuid4().hex[:8]}",
        gmail_thread_id=thread.gmail_thread_id,
        sender="vendor@acme.com",
        subject="Invoice Payment Terms Net 30",
        body_plain="Please process invoice #9921 for $4,500.00 with payment terms Net 30 days.",
        has_attachments=False,
    )
    db_session.add(message)
    db_session.commit()

    return user, thread, message


def test_vector_search_indexing_and_semantic_retrieval(db_session: Session, sample_user_and_message):
    user, thread, message = sample_user_and_message

    vec_service = VectorSearchService()
    indexed_count = vec_service.index_email_message(db_session, user.id, message.id)
    assert indexed_count >= 1

    # Verify vector persistence in pgvector table
    saved_vec = (
        db_session.query(VectorEmbedding)
        .filter(VectorEmbedding.email_message_id == message.id, VectorEmbedding.user_id == user.id)
        .first()
    )
    assert saved_vec is not None
    assert len(saved_vec.embedding) == 768

    # Test semantic search
    results = vec_service.semantic_search(db_session, user.id, "invoice payment terms Net 30", top_k=5)
    assert len(results) >= 1
    assert results[0]["email_message_id"] == str(message.id)
    assert results[0]["similarity_score"] >= 0.0


    # Test multi-tenant isolation with different user
    other_user_id = uuid.uuid4()
    isolated_res = vec_service.semantic_search(db_session, other_user_id, "invoice payment terms Net 30")
    assert len(isolated_res) == 0

    # Test RAG query synthesis
    rag_service = RAGService(vector_service=vec_service)
    rag_res = rag_service.query_rag(db_session, user.id, "What are the payment terms?")
    assert "answer" in rag_res
    assert len(rag_res["citations"]) >= 1
    assert rag_res["citations"][0]["source_name"] == "Subject: Invoice Payment Terms Net 30"
