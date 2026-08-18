from datetime import datetime, timezone
import logging
import uuid
from sqlalchemy.orm import Session
from backend.app.ai.prompts import PROMPT_VERSION
from backend.app.ai.provider import AIProvider, get_ai_provider
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.repositories.ai_repository import AIRepository
from backend.app.utils.evidence_validator import EvidenceValidator

logger = logging.getLogger(__name__)


class AIExtractionService:
    """Service orchestrating email intelligence extraction, evidence validation, and persistence."""

    def __init__(self, provider: AIProvider | None = None):
        self.provider = provider or get_ai_provider()

    async def analyze_message(
        self,
        db: Session,
        user_id: uuid.UUID,
        message_id: uuid.UUID,
        force_reanalyze: bool = False,
    ) -> AIAnalysis:
        """
        Analyze an EmailMessage by ID, validate extracted evidence snippets, and save results idempotently.
        """
        # 1. Fetch message enforcing user isolation
        stmt = (
            db.query(EmailMessage)
            .filter(EmailMessage.id == message_id, EmailMessage.user_id == user_id)
            .first()
        )
        if not stmt:
            raise ValueError(f"EmailMessage {message_id} not found for user {user_id}")

        email_message: EmailMessage = stmt

        # 2. Check for existing analysis matching current model and prompt version (Idempotency)
        if not force_reanalyze:
            existing = AIRepository.get_analysis_by_message_and_version(
                db,
                user_id=user_id,
                email_message_id=message_id,
                model_name=self.provider.model_name,
                prompt_version=PROMPT_VERSION,
            )
            if existing and existing.status == "COMPLETED":
                return existing

        # 3. Extract text payload
        source_text = email_message.body_plain or email_message.snippet or ""

        # 4. Invoke LLM provider
        try:
            result = await self.provider.extract_email_intelligence(
                subject=email_message.subject,
                body=source_text,
                sender=email_message.sender,
            )
        except Exception as exc:
            logger.error("AI Provider extraction failed for message %s: %s", message_id, exc)
            # Record failed analysis
            return AIRepository.save_analysis_with_items(
                db=db,
                user_id=user_id,
                email_message_id=message_id,
                email_thread_id=email_message.thread_id,
                summary="AI Extraction Failed",
                intent="OTHER",
                priority="LOW",
                sentiment="NEUTRAL",
                confidence_score=0.0,
                rationale="Extraction failed due to provider error.",
                model_name=self.provider.model_name,
                prompt_version=PROMPT_VERSION,
                extracted_items=[],
                status="FAILED",
                error_message=str(exc),
            )

        # 5. Process & Validate Evidence Snippets
        items_to_save: list[dict] = []

        # Process actions
        for act in result.actions:
            is_valid = EvidenceValidator.validate_snippet(act.evidence_snippet, source_text)
            due_dt = None
            if act.due_date:
                try:
                    due_dt = datetime.fromisoformat(act.due_date.replace("Z", "+00:00"))
                except ValueError:
                    due_dt = None

            items_to_save.append({
                "item_type": "ACTION",
                "description": act.description,
                "assignee": act.assignee,
                "due_date": due_dt,
                "priority": act.priority.value if hasattr(act.priority, "value") else str(act.priority),
                "confidence": act.confidence if is_valid else act.confidence * 0.5,
                "evidence_snippet": act.evidence_snippet,
                "is_evidence_valid": is_valid,
                "status": "PENDING",
            })

        # Process decisions
        for dec in result.decisions:
            is_valid = EvidenceValidator.validate_snippet(dec.evidence_snippet, source_text)
            items_to_save.append({
                "item_type": "DECISION",
                "description": dec.description,
                "assignee": dec.made_by,
                "due_date": None,
                "priority": "MEDIUM",
                "confidence": dec.confidence if is_valid else dec.confidence * 0.5,
                "evidence_snippet": dec.evidence_snippet,
                "is_evidence_valid": is_valid,
                "status": "CONFIRMED",
            })

        # Process risks
        for rsk in result.risks:
            is_valid = EvidenceValidator.validate_snippet(rsk.evidence_snippet, source_text)
            items_to_save.append({
                "item_type": "RISK",
                "description": rsk.description,
                "assignee": None,
                "due_date": None,
                "priority": rsk.severity.value if hasattr(rsk.severity, "value") else str(rsk.severity),
                "confidence": rsk.confidence if is_valid else rsk.confidence * 0.5,
                "evidence_snippet": rsk.evidence_snippet,
                "is_evidence_valid": is_valid,
                "status": "PENDING",
            })

        # 6. Save to repository idempotently
        analysis = AIRepository.save_analysis_with_items(
            db=db,
            user_id=user_id,
            email_message_id=message_id,
            email_thread_id=email_message.thread_id,
            summary=result.summary,
            intent=result.intent.value if hasattr(result.intent, "value") else str(result.intent),
            priority=result.priority.value if hasattr(result.priority, "value") else str(result.priority),
            sentiment=result.sentiment.value if hasattr(result.sentiment, "value") else str(result.sentiment),
            confidence_score=result.confidence_score,
            rationale=result.rationale,
            model_name=self.provider.model_name,
            prompt_version=PROMPT_VERSION,
            extracted_items=items_to_save,
            status="COMPLETED",
        )

        return analysis

    async def analyze_thread(
        self,
        db: Session,
        user_id: uuid.UUID,
        thread_id: uuid.UUID,
    ) -> list[AIAnalysis]:
        """Analyze all messages in a thread."""
        thread = db.query(EmailThread).filter(EmailThread.id == thread_id, EmailThread.user_id == user_id).first()
        if not thread:
            raise ValueError(f"EmailThread {thread_id} not found for user {user_id}")

        analyses = []
        for msg in thread.messages:
            ana = await self.analyze_message(db, user_id, msg.id)
            analyses.append(ana)
        return analyses
