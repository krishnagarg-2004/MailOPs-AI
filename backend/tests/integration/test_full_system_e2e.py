import uuid
import pytest
from sqlalchemy.orm import Session
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.attachment import Attachment
from backend.app.models.business_document_extraction import BusinessDocumentExtraction
from backend.app.models.document_extraction import DocumentExtraction
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.extracted_action import ExtractedAction
from backend.app.models.oauth import OAuthAccount
from backend.app.models.reply_draft import ReplyDraft
from backend.app.models.user import User
from backend.app.services.action_graph_service import ActionGraphService
from backend.app.services.ai_extraction_service import AIExtractionService
from backend.app.services.business_document_ai_service import BusinessDocumentAIService
from backend.app.services.document_service import DocumentProcessingService
from backend.app.services.rag_service import RAGService
from backend.app.services.reply_draft_service import ReplyDraftService
from backend.app.services.vector_search_service import VectorSearchService
from backend.tests.integration.test_database import db_session, test_engine


@pytest.mark.asyncio
async def test_full_system_end_to_end_deterministic_pipeline(db_session: Session):
    """
    DETERMINISTIC FULL-SYSTEM E2E INTEGRATION TEST:
    Executes the complete M1 through M9 user workflow offline using mock providers:
    User Creation -> Message Sync -> AI Extraction -> Attachment OCR -> RAG Vector Indexing ->
    Action Graph Sync -> Human-in-the-Loop Reply Draft -> Manual Edit -> Scope Verification.
    """
    # 1. User Creation & OAuth Account Linking (M2 / M3)
    user = User(
        email=f"e2e_user_{uuid.uuid4().hex[:8]}@example.com",
        full_name="E2E Pipeline User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    oauth_account = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id=f"g_e2e_{uuid.uuid4().hex[:8]}",
        email=user.email,
        scopes="openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.compose",
    )
    db_session.add(oauth_account)
    db_session.commit()

    # 2. Email Thread & Message Ingestion (M4)
    thread = EmailThread(
        user_id=user.id,
        gmail_thread_id=f"th_e2e_{uuid.uuid4().hex[:8]}",
        snippet="Invoice & Contract Review Request",
    )
    db_session.add(thread)
    db_session.commit()

    message = EmailMessage(
        user_id=user.id,
        thread_id=thread.id,
        gmail_message_id=f"msg_e2e_{uuid.uuid4().hex[:8]}",
        gmail_thread_id=thread.gmail_thread_id,
        sender="vendor@enterprise.com",
        subject="Invoice #9901 and Service Contract",
        body_plain="Please process payment of $12,500 for Invoice #9901 due on 2026-09-01.",
        has_attachments=True,
    )
    db_session.add(message)
    db_session.commit()

    # 3. Attachment & Document Intelligence Pipeline (M6)
    attachment = Attachment(
        user_id=user.id,
        message_id=message.id,
        gmail_attachment_id=f"att_e2e_{uuid.uuid4().hex[:8]}",
        filename="Invoice_9901.pdf",
        mime_type="application/pdf",
        size_bytes=4096,
        storage_path=f"storage/attachments/{user.id}/test_invoice.dat",
    )

    db_session.add(attachment)
    db_session.commit()

    doc_extraction = DocumentExtraction(
        user_id=user.id,
        attachment_id=attachment.id,
        email_message_id=message.id,
        file_type="PDF",
        page_count=1,
        extracted_text="--- [Page 1] ---\nINVOICE #9901\nTotal: $12,500.00\nVendor: Enterprise Corp\nDue Date: 2026-09-01",
        extraction_method="NATIVE_TEXT",
        status="COMPLETED",
    )

    db_session.add(doc_extraction)
    db_session.commit()

    # 4. AI Email Extraction Engine (M5)
    ai_service = AIExtractionService()
    ai_analysis = await ai_service.analyze_message(db_session, user.id, message.id)
    actions = ai_analysis.extracted_items
    assert ai_analysis is not None
    assert ai_analysis.user_id == user.id
    assert len(actions) >= 1



    # 5. Semantic Search & pgvector Indexing (M7)
    v_service = VectorSearchService()
    indexed_count = v_service.index_email_message(db_session, user.id, message.id)
    assert indexed_count >= 1

    search_results = v_service.semantic_search(db_session, user.id, "Invoice payment")
    assert len(search_results) >= 1
    assert search_results[0]["email_message_id"] == str(message.id)



    # 6. Action Graph & Relationship Mapping (M8)
    graph_node = ActionGraphService.sync_action_nodes(db_session, user.id, actions[0].id)
    assert graph_node is not None
    assert graph_node.user_id == user.id

    root_node, blocking, edges = ActionGraphService.get_dependency_chain(db_session, user.id, actions[0].id)
    assert root_node.id == graph_node.id

    # 7. Human-in-the-Loop Reply Draft Generation (M9)
    reply_draft = await ReplyDraftService.generate_draft(
        db=db_session,
        user_id=user.id,
        message_id=message.id,
        tone="PROFESSIONAL",
        intent="REPLY_RESPONSE",
    )
    assert reply_draft is not None
    assert reply_draft.status == "DRAFTED"
    assert reply_draft.gmail_draft_id is None  # LOCAL-BY-DEFAULT GUARANTEE

    # 8. Human-in-the-Loop User Manual Editing (M9)
    updated_draft = ReplyDraftService.update_draft(
        db=db_session,
        user_id=user.id,
        draft_id=reply_draft.id,
        body_text="We have approved Invoice #9901 for payment on September 1st.",
        tone="PROFESSIONAL",
    )
    assert updated_draft.status == "EDITED"
    assert "approved Invoice #9901" in updated_draft.body_text

    # 9. Incremental OAuth Compose Scope Verification (M9)
    oauth_acc = ReplyDraftService.verify_compose_scope(db_session, user.id)
    assert oauth_acc is not None
    assert oauth_acc.user_id == user.id
