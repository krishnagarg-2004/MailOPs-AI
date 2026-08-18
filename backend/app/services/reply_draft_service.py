import base64
from email.message import EmailMessage as MIMEEmailMessage
import logging
import uuid
from sqlalchemy.orm import Session
from backend.app.ai.provider import get_ai_provider
from backend.app.core.config import settings
from backend.app.integrations.gmail import GmailClient
from backend.app.integrations.google_oauth import has_compose_scope
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.extracted_action import ExtractedAction
from backend.app.models.oauth import OAuthAccount
from backend.app.models.reply_draft import ReplyDraft

logger = logging.getLogger(__name__)


def build_raw_reply_mime(
    sender: str,
    recipient: str,
    subject: str,
    body_text: str,
    in_reply_to_msg_id: str | None = None,
    references: str | None = None,
) -> str:
    """Construct RFC 2822 MIME message string and base64url encode for Gmail API."""
    mime_msg = MIMEEmailMessage()
    mime_msg["From"] = sender
    mime_msg["To"] = recipient

    clean_subj = subject
    if not clean_subj.lower().startswith("re:"):
        clean_subj = f"Re: {clean_subj}"
    mime_msg["Subject"] = clean_subj

    if in_reply_to_msg_id:
        msg_id_header = in_reply_to_msg_id if in_reply_to_msg_id.startswith("<") else f"<{in_reply_to_msg_id}>"
        mime_msg["In-Reply-To"] = msg_id_header
        mime_msg["References"] = references or msg_id_header

    mime_msg.set_content(body_text)

    raw_bytes = mime_msg.as_bytes()
    encoded = base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")
    return encoded


class ReplyDraftService:
    """Service orchestrating multi-source context assembly, AI reply drafting, local persistence, and Gmail sync/send."""

    @classmethod
    def assemble_reply_context(
        cls,
        db: Session,
        user_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> tuple[EmailMessage, EmailThread, str]:
        """Assemble multi-source context across M4 thread, M5 actions, M6 docs, and M8 graph."""
        msg = db.query(EmailMessage).filter(EmailMessage.id == message_id, EmailMessage.user_id == user_id).first()
        if not msg:
            raise ValueError(f"Email message {message_id} not found for user {user_id}")

        thread = db.query(EmailThread).filter(EmailThread.id == msg.thread_id, EmailThread.user_id == user_id).first()
        if not thread:
            raise ValueError(f"Email thread for message {message_id} not found for user {user_id}")

        # Fetch M5 Extracted Actions
        actions = db.query(ExtractedAction).filter(ExtractedAction.email_message_id == msg.id, ExtractedAction.user_id == user_id).all()
        actions_context = "\n".join([f"- Action [{a.item_type}]: {a.description} (Priority: {a.severity_or_priority})" for a in actions]) or "None"

        # Assemble prompt context
        context_prompt = (
            f"<email_message_context>\n"
            f"Sender: {msg.sender}\n"
            f"Subject: {msg.subject}\n"
            f"Body:\n{msg.body_plain or msg.snippet or ''}\n"
            f"</email_message_context>\n"
            f"<extracted_actions>\n"
            f"{actions_context}\n"
            f"</extracted_actions>\n"
        )
        return msg, thread, context_prompt

    @classmethod
    async def generate_draft(
        cls,
        db: Session,
        user_id: uuid.UUID,
        message_id: uuid.UUID,
        tone: str = "PROFESSIONAL",
        intent: str = "REPLY_RESPONSE",
    ) -> ReplyDraft:
        """
        Generate context-aware reply draft using configured AI Provider and persist locally in PostgreSQL.
        STRICT NO-AUTOMATIC-SENDING GUARANTEE: Does NOT contact Gmail API.
        """
        msg, thread, context_prompt = cls.assemble_reply_context(db, user_id, message_id)

        ai_provider = get_ai_provider()
        draft_result = await ai_provider.generate_reply_draft(context_prompt=context_prompt, tone=tone, intent=intent)

        recipient = msg.sender or "recipient@example.com"
        subject = draft_result.subject if draft_result.subject else f"Re: {msg.subject or 'Email'}"
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        draft = ReplyDraft(
            user_id=user_id,
            email_thread_id=thread.id,
            email_message_id=msg.id,
            subject=subject,
            body_text=draft_result.body_text,
            recipient_email=recipient,
            intent=intent,
            tone=tone.upper(),
            status="DRAFTED",
            rationale_and_provenance=draft_result.rationale_and_provenance,
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft

    @classmethod
    def update_draft(
        cls,
        db: Session,
        user_id: uuid.UUID,
        draft_id: uuid.UUID,
        subject: str | None = None,
        body_text: str | None = None,
        tone: str | None = None,
        intent: str | None = None,
        status: str | None = None,
    ) -> ReplyDraft:
        """Update draft properties from Human-in-the-Loop user manual edits."""
        draft = db.query(ReplyDraft).filter(ReplyDraft.id == draft_id, ReplyDraft.user_id == user_id).first()
        if not draft:
            raise ValueError(f"Reply draft {draft_id} not found for user {user_id}")

        if subject is not None:
            draft.subject = subject
        if body_text is not None:
            draft.body_text = body_text
        if tone is not None:
            draft.tone = tone.upper()
        if intent is not None:
            draft.intent = intent
        if status is not None:
            draft.status = status
        elif draft.status == "DRAFTED":
            draft.status = "EDITED"

        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft

    @classmethod
    def verify_compose_scope(cls, db: Session, user_id: uuid.UUID) -> OAuthAccount:
        """Verify user's OAuth account has gmail.compose permission. Raises PermissionError if missing."""
        oauth_account = db.query(OAuthAccount).filter(OAuthAccount.user_id == user_id, OAuthAccount.provider == "google").first()
        if not oauth_account:
            raise PermissionError("No Google OAuth account linked. Please authenticate.")

        if not has_compose_scope(oauth_account.scopes):
            raise PermissionError(
                "Gmail compose permissions are required to sync/send email. "
                "Please reauthorize with compose scope at /api/v1/auth/google/authorize-compose"
            )

        return oauth_account

    @classmethod
    async def sync_gmail_draft(cls, db: Session, user_id: uuid.UUID, draft_id: uuid.UUID) -> ReplyDraft:
        """
        Push draft to user's Gmail mailbox as a Gmail Draft.
        Requires explicit user action and verified gmail.compose OAuth scope.
        Preserves thread context (threadId, In-Reply-To, References, Subject).
        """
        oauth_account = cls.verify_compose_scope(db, user_id)

        draft = db.query(ReplyDraft).filter(ReplyDraft.id == draft_id, ReplyDraft.user_id == user_id).first()
        if not draft:
            raise ValueError(f"Reply draft {draft_id} not found for user {user_id}")

        msg = db.query(EmailMessage).filter(EmailMessage.id == draft.email_message_id, EmailMessage.user_id == user_id).first()
        if not msg:
            raise ValueError("Associated parent email message not found.")

        # Build raw MIME message
        raw_mime = build_raw_reply_mime(
            sender=oauth_account.email or "me",
            recipient=draft.recipient_email,
            subject=draft.subject,
            body_text=draft.body_text,
            in_reply_to_msg_id=msg.gmail_message_id,
            references=msg.gmail_message_id,
        )

        client = GmailClient()
        access_token = client.get_valid_access_token(db, oauth_account)

        resp = await client.create_draft(
            access_token=access_token,
            raw_mime=raw_mime,
            thread_id=msg.gmail_thread_id,
        )

        draft.gmail_draft_id = resp.get("id")
        draft.status = "APPROVED"
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft

    @classmethod
    async def send_reply_email(cls, db: Session, user_id: uuid.UUID, draft_id: uuid.UUID) -> ReplyDraft:
        """
        Send reply email directly via Gmail REST API.
        Requires explicit separate user action and verified gmail.compose OAuth scope.
        Preserves thread context (threadId, In-Reply-To, References, Subject).
        """
        oauth_account = cls.verify_compose_scope(db, user_id)

        draft = db.query(ReplyDraft).filter(ReplyDraft.id == draft_id, ReplyDraft.user_id == user_id).first()
        if not draft:
            raise ValueError(f"Reply draft {draft_id} not found for user {user_id}")

        msg = db.query(EmailMessage).filter(EmailMessage.id == draft.email_message_id, EmailMessage.user_id == user_id).first()
        if not msg:
            raise ValueError("Associated parent email message not found.")

        raw_mime = build_raw_reply_mime(
            sender=oauth_account.email or "me",
            recipient=draft.recipient_email,
            subject=draft.subject,
            body_text=draft.body_text,
            in_reply_to_msg_id=msg.gmail_message_id,
            references=msg.gmail_message_id,
        )

        client = GmailClient()
        access_token = client.get_valid_access_token(db, oauth_account)

        await client.send_message(
            access_token=access_token,
            raw_mime=raw_mime,
            thread_id=msg.gmail_thread_id,
        )

        draft.status = "SENT"
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft
