"""
Demo Data Seeder for MailOps AI.
Populates realistic enterprise emails, attachments, AI analyses,
action graphs, vector embeddings, and reply drafts for instant offline testing and live showcase.
"""

from datetime import datetime, timedelta, timezone
import json
import logging
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.ai.embedding_provider import MockEmbeddingProvider
from backend.app.core.config import settings
from backend.app.core.crypto import encrypt_token
from backend.app.core.security import generate_session_token, hash_session_token
from backend.app.db.session import SessionLocal
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.attachment import Attachment
from backend.app.models.business_document_extraction import BusinessDocumentExtraction
from backend.app.models.document_extraction import DocumentExtraction
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.extracted_action import ExtractedAction
from backend.app.models.graph_edge import GraphEdge
from backend.app.models.graph_node import GraphNode
from backend.app.models.oauth import OAuthAccount
from backend.app.models.reply_draft import ReplyDraft
from backend.app.models.session import UserSession
from backend.app.models.user import User
from backend.app.models.vector_embedding import VectorEmbedding

logger = logging.getLogger(__name__)

DEMO_USER_EMAIL = "alex.morgan@enterprise-mailops.io"
DEMO_USER_NAME = "Alex Morgan (VP of Product Operations)"
DEMO_USER_AVATAR = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"


def seed_demo_environment(db: Session | None = None, include_embeddings: bool = True) -> dict[str, str | int]:
    """
    Seeds comprehensive realistic enterprise mock data into the database.
    Returns summary metrics.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        now = datetime.now(timezone.utc)

        # 1. Create or retrieve demo user
        user = db.execute(select(User).where(User.email == DEMO_USER_EMAIL)).scalar_one_or_none()
        if not user:
            user = User(
                email=DEMO_USER_EMAIL,
                full_name=DEMO_USER_NAME,
                avatar_url=DEMO_USER_AVATAR,
                is_active=True,
                is_superuser=False,
            )
            db.add(user)
            db.flush()

        # 2. Add or update linked OAuth account
        oauth = db.execute(select(OAuthAccount).where(OAuthAccount.user_id == user.id)).scalar_one_or_none()
        if not oauth:
            oauth = OAuthAccount(
                user_id=user.id,
                provider="google",
                provider_account_id="demo_google_sub_109283746",
                email=DEMO_USER_EMAIL,
                encrypted_access_token=encrypt_token("mock_access_token_demo"),
                encrypted_refresh_token=encrypt_token("mock_refresh_token_demo"),
                token_expires_at=now + timedelta(days=365),
                scopes="openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.compose",
            )
            db.add(oauth)

        # 3. Create active demo session so user can log in with 1 click
        demo_session_token = "mailops_demo_session_token_key_2026"
        session_hash = hash_session_token(demo_session_token)
        existing_session = db.execute(
            select(UserSession).where(UserSession.session_token_hash == session_hash)
        ).scalar_one_or_none()
        if not existing_session:
            db.add(
                UserSession(
                    session_token_hash=session_hash,
                    user_id=user.id,
                    ip_address="127.0.0.1",
                    user_agent="MailOps-Demo-Client",
                    expires_at=now + timedelta(days=30),
                    last_accessed_at=now,
                )
            )

        # 4. Realistic Enterprise Threads Dataset
        threads_data = [
            {
                "thread_id": "thread_escalation_001",
                "message_id": "msg_esc_001",
                "subject": "URGENT: Production API Rate Limits Exceeded - Enterprise Tier Customer",
                "sender": "sarah.chen@fintech-client.corp",
                "recipients": DEMO_USER_EMAIL,
                "sent_offset_hours": 1,
                "snippet": "We are observing 429 errors across our European payment gateway cluster starting at 14:00 UTC...",
                "body": (
                    "Hi Alex,\n\n"
                    "We are observing 429 errors across our European payment gateway cluster starting at 14:00 UTC. "
                    "Our transaction processing volume has surged 3x due to the Black Friday promotional launch.\n\n"
                    "Please upgrade our rate limit quota to 50,000 requests per minute immediately before 18:00 UTC today. "
                    "If this is not addressed by then, we will be forced to failover to our secondary provider.\n\n"
                    "Regards,\nSarah Chen\nVP Engineering, FinTech Corp"
                ),
                "intent": "URGENT_ACTION",
                "priority": "HIGH",
                "sentiment": "NEGATIVE",
                "summary": "FinTech Corp is experiencing 429 rate limit errors on European payment clusters and requires quota increase before 18:00 UTC.",
                "rationale": "Customer explicitly stated European gateway cluster failure and requested emergency quota upgrade before 18:00 UTC deadline.",
                "actions": [
                    {
                        "description": "Upgrade FinTech Corp rate limit quota to 50,000 req/min",
                        "due_date": (now + timedelta(hours=4)).isoformat(),
                        "priority": "HIGH",
                        "evidence": "upgrade our rate limit quota to 50,000 requests per minute immediately before 18:00 UTC today",
                    }
                ],
                "risks": [
                    {
                        "description": "Customer will failover to secondary provider if outage continues",
                        "severity": "HIGH",
                        "evidence": "we will be forced to failover to our secondary provider",
                    }
                ],
                "decisions": [],
                "reply": {
                    "subject": "Re: URGENT: Production API Rate Limits Exceeded - Enterprise Tier Customer",
                    "recipient": "sarah.chen@fintech-client.corp",
                    "body": "Hi Sarah,\n\nOur infrastructure team has temporarily boosted your European cluster rate limits to 65,000 req/min to absorb the traffic spike. The gateway is now operating within safe thresholds.\n\nBest,\nAlex Morgan",
                    "intent": "REPLY_RESPONSE",
                    "tone": "PROFESSIONAL",
                },
            },
            {
                "thread_id": "thread_invoice_002",
                "message_id": "msg_inv_002",
                "subject": "Vendor Invoice #INV-2026-8891 - Cloud Infrastructure Services",
                "sender": "billing@apex-datacenter.io",
                "recipients": DEMO_USER_EMAIL,
                "sent_offset_hours": 6,
                "snippet": "Attached please find invoice INV-2026-8891 for your dedicated GPU training cluster compute hours...",
                "body": (
                    "Dear MailOps Accounts Payable,\n\n"
                    "Attached please find invoice INV-2026-8891 for your dedicated GPU training cluster compute hours for October 2026. "
                    "Total amount due is $14,850.00 USD, payable within Net-30 days via ACH wire transfer before November 30, 2026.\n\n"
                    "Please confirm receipt and schedule disbursement at your earliest convenience.\n\n"
                    "Apex Data Systems Billing Operations"
                ),
                "intent": "FINANCIAL_INVOICE",
                "priority": "MEDIUM",
                "sentiment": "NEUTRAL",
                "summary": "Monthly cloud infrastructure invoice #INV-2026-8891 for $14,850.00 due by November 30, 2026.",
                "rationale": "Direct invoice transmission requesting payment of $14,850.00 Net-30 terms.",
                "actions": [
                    {
                        "description": "Schedule disbursement for Invoice INV-2026-8891 ($14,850.00)",
                        "due_date": (now + timedelta(days=14)).isoformat(),
                        "priority": "MEDIUM",
                        "evidence": "payable within Net-30 days via ACH wire transfer before November 30, 2026",
                    }
                ],
                "risks": [],
                "decisions": [],
                "attachment": {
                    "filename": "Invoice_INV_2026_8891.pdf",
                    "mime_type": "application/pdf",
                    "size_bytes": 184520,
                    "category": "INVOICE",
                    "extracted_json": {
                        "invoice_number": "INV-2026-8891",
                        "vendor_name": "Apex Data Systems",
                        "invoice_date": "2026-10-31",
                        "due_date": "2026-11-30",
                        "total_amount": 14850.00,
                        "currency": "USD",
                        "line_items": [
                            {"description": "Dedicated H100 GPU Cluster (720 hrs)", "quantity": 1, "total": 12600.00},
                            {"description": "High-IOPS NVMe Volume Storage", "quantity": 15, "total": 2250.00},
                        ],
                    },
                },
            },
            {
                "thread_id": "thread_legal_003",
                "message_id": "msg_leg_003",
                "subject": "Mutual Non-Disclosure & IP Agreement - Enterprise Partnership",
                "sender": "elena.rostova@globalventures-legal.com",
                "recipients": DEMO_USER_EMAIL,
                "sent_offset_hours": 12,
                "snippet": "We have finalized the revised Mutual NDA incorporating our discussions regarding data privacy and GDPR...",
                "body": (
                    "Alex,\n\n"
                    "We have finalized the revised Mutual NDA incorporating our discussions regarding data privacy and GDPR compliance. "
                    "We have approved the 3-year term clause and accepted section 8.4 regarding confidential AI weights.\n\n"
                    "Please have your authorized legal officer execute the signature page and return the countersigned PDF by Friday 5 PM EST.\n\n"
                    "Best regards,\nElena Rostova\nGeneral Counsel, Global Ventures LLC"
                ),
                "intent": "CONTRACT_LEGAL",
                "priority": "HIGH",
                "sentiment": "POSITIVE",
                "summary": "Revised Mutual NDA finalized with 3-year term and confidential AI weights clause; countersignature required by Friday 5 PM EST.",
                "rationale": "Legal counsel confirmed agreement terms and requested countersigned execution by Friday deadline.",
                "actions": [
                    {
                        "description": "Execute and return countersigned Mutual NDA",
                        "due_date": (now + timedelta(days=2)).isoformat(),
                        "priority": "HIGH",
                        "evidence": "execute the signature page and return the countersigned PDF by Friday 5 PM EST",
                    }
                ],
                "risks": [],
                "decisions": [
                    {
                        "description": "Approved 3-year term clause and section 8.4 AI weights confidentiality",
                        "evidence": "We have approved the 3-year term clause and accepted section 8.4 regarding confidential AI weights",
                    }
                ],
                "attachment": {
                    "filename": "Mutual_NDA_GlobalVentures_v2.docx",
                    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "size_bytes": 94210,
                    "category": "CONTRACT",
                    "extracted_json": {
                        "contract_title": "Mutual Non-Disclosure Agreement",
                        "parties": ["MailOps AI Technologies Inc", "Global Ventures LLC"],
                        "effective_date": "2026-11-01",
                        "term_years": 3,
                        "governing_law": "Delaware, United States",
                        "key_clauses": [
                            "Confidential AI Weights and Algorithmic Intellectual Property Protection",
                            "GDPR & CCPA Data Processing Conformity",
                            "Non-Solicitation 12-month Covenant",
                        ],
                    },
                },
            },
            {
                "thread_id": "thread_status_004",
                "message_id": "msg_stat_004",
                "subject": "Sprint 42 Status Update: Semantic Search & Hybrid Vector Indexing",
                "sender": "marcus.vance@engineering-mailops.internal",
                "recipients": DEMO_USER_EMAIL,
                "sent_offset_hours": 24,
                "snippet": "Here is the summary of progress for Sprint 42 across the core data pipeline team...",
                "body": (
                    "Team,\n\n"
                    "Here is the summary of progress for Sprint 42 across the core data pipeline team. "
                    "We completed the pgvector HNSW index tuning, reducing p99 semantic query latency from 320ms to 48ms.\n\n"
                    "Action for Marcus: Run benchmark regression tests on 50,000 synthetic vector chunks before tomorrow's all-hands.\n"
                    "Action for Alex: Review the architecture memo on cross-encoder rerankers.\n\n"
                    "Cheers,\nMarcus Vance\nLead Search Engineer"
                ),
                "intent": "STATUS_UPDATE",
                "priority": "LOW",
                "sentiment": "POSITIVE",
                "summary": "Sprint 42 completed pgvector HNSW indexing, dropping p99 latency to 48ms. Benchmark and memo review pending.",
                "rationale": "Engineering status update outlining performance improvements and upcoming sprint action items.",
                "actions": [
                    {
                        "description": "Review architecture memo on cross-encoder rerankers",
                        "due_date": (now + timedelta(days=1)).isoformat(),
                        "priority": "LOW",
                        "evidence": "Review the architecture memo on cross-encoder rerankers",
                    }
                ],
                "risks": [],
                "decisions": [
                    {
                        "description": "Adopted HNSW indexing configuration for pgvector tables",
                        "evidence": "We completed the pgvector HNSW index tuning, reducing p99 semantic query latency from 320ms to 48ms",
                    }
                ],
            },
        ]

        embedder = MockEmbeddingProvider()
        created_threads = 0
        created_actions = 0
        created_embeddings = 0

        # Maintain node mapping for graph edges
        graph_nodes_cache = {}

        for tdata in threads_data:
            # Check if thread already exists
            thread = db.execute(
                select(EmailThread).where(
                    EmailThread.user_id == user.id,
                    EmailThread.gmail_thread_id == tdata["thread_id"],
                )
            ).scalar_one_or_none()

            sent_at = now - timedelta(hours=tdata["sent_offset_hours"])

            if not thread:
                thread = EmailThread(
                    user_id=user.id,
                    gmail_thread_id=tdata["thread_id"],
                    snippet=tdata["snippet"],
                    last_message_at=sent_at,
                )
                db.add(thread)
                db.flush()
                created_threads += 1

            # Check or create message
            msg = db.execute(
                select(EmailMessage).where(
                    EmailMessage.user_id == user.id,
                    EmailMessage.gmail_message_id == tdata["message_id"],
                )
            ).scalar_one_or_none()

            has_att = "attachment" in tdata
            if not msg:
                msg = EmailMessage(
                    user_id=user.id,
                    thread_id=thread.id,
                    gmail_message_id=tdata["message_id"],
                    gmail_thread_id=tdata["thread_id"],
                    sender=tdata["sender"],
                    recipients=tdata["recipients"],
                    subject=tdata["subject"],
                    snippet=tdata["snippet"],
                    body_plain=tdata["body"],
                    sent_at=sent_at,
                    received_at=sent_at,
                    labels='["INBOX", "UNREAD", "IMPORTANT"]' if tdata["priority"] == "HIGH" else '["INBOX"]',
                    has_attachments=has_att,
                )
                db.add(msg)
                db.flush()

            # Create AI Analysis record
            analysis = db.execute(
                select(AIAnalysis).where(
                    AIAnalysis.user_id == user.id,
                    AIAnalysis.email_message_id == msg.id,
                )
            ).scalar_one_or_none()

            if not analysis:
                analysis = AIAnalysis(
                    user_id=user.id,
                    email_message_id=msg.id,
                    email_thread_id=thread.id,
                    summary=tdata["summary"],
                    intent=tdata["intent"],
                    priority=tdata["priority"],
                    sentiment=tdata["sentiment"],
                    confidence_score=0.98,
                    rationale=tdata["rationale"],
                    model_name="gemini-2.5-flash (demo)",
                    prompt_version="1.0.0",
                    status="COMPLETED",
                )
                db.add(analysis)
                db.flush()

                # Action Items
                for act in tdata.get("actions", []):
                    action_item = ExtractedAction(
                        user_id=user.id,
                        ai_analysis_id=analysis.id,
                        email_message_id=msg.id,
                        email_thread_id=thread.id,
                        item_type="ACTION",
                        description=act["description"],
                        assignee=user.email,
                        due_date=datetime.fromisoformat(act["due_date"]) if act.get("due_date") else None,
                        severity_or_priority=act["priority"],
                        status="PENDING",
                        confidence_score=0.95,
                        evidence_snippet=act["evidence"],
                    )
                    db.add(action_item)
                    db.flush()
                    created_actions += 1

                # Decisions
                for dec in tdata.get("decisions", []):
                    db.add(
                        ExtractedAction(
                            user_id=user.id,
                            ai_analysis_id=analysis.id,
                            email_message_id=msg.id,
                            email_thread_id=thread.id,
                            item_type="DECISION",
                            description=dec["description"],
                            status="CONFIRMED",
                            confidence_score=0.96,
                            evidence_snippet=dec["evidence"],
                        )
                    )

                # Risks
                for rsk in tdata.get("risks", []):
                    db.add(
                        ExtractedAction(
                            user_id=user.id,
                            ai_analysis_id=analysis.id,
                            email_message_id=msg.id,
                            email_thread_id=thread.id,
                            item_type="RISK",
                            description=rsk["description"],
                            severity_or_priority=rsk["severity"],
                            status="PENDING",
                            confidence_score=0.97,
                            evidence_snippet=rsk["evidence"],
                        )
                    )

            # Optional attachment and document extraction
            if has_att:
                att_info = tdata["attachment"]
                att = db.execute(
                    select(Attachment).where(
                        Attachment.user_id == user.id,
                        Attachment.message_id == msg.id,
                    )
                ).scalar_one_or_none()

                if not att:
                    att = Attachment(
                        user_id=user.id,
                        message_id=msg.id,
                        gmail_attachment_id=f"att_{uuid.uuid4().hex[:12]}",
                        filename=att_info["filename"],
                        mime_type=att_info["mime_type"],
                        size_bytes=att_info["size_bytes"],
                        storage_path=f"demo_storage/{att_info['filename']}",
                        is_downloaded=True,
                    )
                    db.add(att)
                    db.flush()

                    raw_text = json.dumps(att_info["extracted_json"], indent=2)
                    doc_ext = DocumentExtraction(
                        user_id=user.id,
                        attachment_id=att.id,
                        email_message_id=msg.id,
                        file_type="PDF" if "pdf" in att_info["filename"].lower() else "DOCX",
                        extraction_method="NATIVE_TEXT",
                        extracted_text=raw_text,
                        char_count=len(raw_text),
                        page_count=1,
                        is_ocr_applied=False,
                        status="COMPLETED",
                    )
                    db.add(doc_ext)
                    db.flush()

                    biz_ext = BusinessDocumentExtraction(
                        user_id=user.id,
                        attachment_id=att.id,
                        document_extraction_id=doc_ext.id,
                        document_category=att_info["category"],
                        extracted_data=att_info["extracted_json"],
                        vendor_or_party=att_info["extracted_json"].get("vendor_name") or "Global Ventures LLC",
                        document_reference_number=att_info["extracted_json"].get("invoice_number", "DOC-REF-001"),
                    )
                    db.add(biz_ext)

            # Reply draft if defined
            if "reply" in tdata:
                rdata = tdata["reply"]
                existing_reply = db.execute(
                    select(ReplyDraft).where(
                        ReplyDraft.user_id == user.id,
                        ReplyDraft.email_thread_id == thread.id,
                    )
                ).scalar_one_or_none()
                if not existing_reply:
                    db.add(
                        ReplyDraft(
                            user_id=user.id,
                            email_thread_id=thread.id,
                            email_message_id=msg.id,
                            subject=rdata["subject"],
                            body_text=rdata["body"],
                            recipient_email=rdata["recipient"],
                            intent=rdata["intent"],
                            tone=rdata["tone"],
                            status="DRAFTED",
                            rationale_and_provenance=[
                                "Drafted to de-escalate payment cluster rate limits and confirm threshold stabilization."
                            ],
                        )
                    )

            # Vector Embeddings for Semantic Search & RAG
            if include_embeddings:
                existing_emb = db.execute(
                    select(VectorEmbedding).where(
                        VectorEmbedding.user_id == user.id,
                        VectorEmbedding.email_message_id == msg.id,
                    )
                ).first()

                if not existing_emb:
                    vector = embedder.embed_query(f"{msg.subject} {msg.body_plain}")
                    db.add(
                        VectorEmbedding(
                            user_id=user.id,
                            source_type="EMAIL",
                            email_message_id=msg.id,
                            chunk_index=0,
                            chunk_text=f"Subject: {msg.subject}\nFrom: {msg.sender}\n\n{msg.body_plain}",
                            embedding=vector,
                            embedding_model=settings.EMBEDDING_MODEL,
                        )
                    )
                    created_embeddings += 1

            # Graph Nodes
            thread_node = db.execute(
                select(GraphNode).where(
                    GraphNode.user_id == user.id,
                    GraphNode.entity_reference_id == thread.id,
                )
            ).scalar_one_or_none()
            if not thread_node:
                thread_node = GraphNode(
                    user_id=user.id,
                    node_type="EMAIL_THREAD",
                    label=tdata["subject"][:40] + "...",
                    entity_reference_id=thread.id,
                    properties={"priority": tdata["priority"], "intent": tdata["intent"]},
                )
                db.add(thread_node)
                db.flush()
            graph_nodes_cache[tdata["thread_id"]] = thread_node

        # Create Graph Dependency Edge
        # Thread 001 depends on API team resolution
        if "thread_escalation_001" in graph_nodes_cache and "thread_status_004" in graph_nodes_cache:
            src = graph_nodes_cache["thread_escalation_001"]
            tgt = graph_nodes_cache["thread_status_004"]
            edge = db.execute(
                select(GraphEdge).where(
                    GraphEdge.user_id == user.id,
                    GraphEdge.source_node_id == src.id,
                    GraphEdge.target_node_id == tgt.id,
                )
            ).scalar_one_or_none()
            if not edge:
                db.add(
                    GraphEdge(
                        user_id=user.id,
                        source_node_id=src.id,
                        target_node_id=tgt.id,
                        relationship_type="DEPENDS_ON",
                        weight=1.0,
                        properties={"reason": "Customer outage mitigation depends on database index stability"},
                    )
                )

        db.commit()

        summary = {
            "demo_user": DEMO_USER_EMAIL,
            "session_token": demo_session_token,
            "threads_created": created_threads,
            "actions_created": created_actions,
            "embeddings_created": created_embeddings,
        }
        logger.info(f"Demo environment successfully seeded: {summary}")
        return summary

    except Exception as exc:
        db.rollback()
        logger.error(f"Error seeding demo data: {exc}", exc_info=True)
        raise
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = seed_demo_environment()
    print("Seeding Complete:", res)
