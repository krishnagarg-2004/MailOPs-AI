from datetime import datetime
import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.extracted_action import ExtractedAction


class AIRepository:
    """Database repository for AI analyses and extracted action items."""

    @staticmethod
    def get_analysis_by_message_and_version(
        db: Session,
        user_id: uuid.UUID,
        email_message_id: uuid.UUID,
        model_name: str,
        prompt_version: str,
    ) -> AIAnalysis | None:
        """Fetch analysis matching specific message, model, and prompt version."""
        stmt = (
            select(AIAnalysis)
            .where(
                AIAnalysis.user_id == user_id,
                AIAnalysis.email_message_id == email_message_id,
                AIAnalysis.model_name == model_name,
                AIAnalysis.prompt_version == prompt_version,
            )
            .options(selectinload(AIAnalysis.extracted_items))
        )
        return db.scalar(stmt)

    @staticmethod
    def get_latest_analysis_by_message(
        db: Session,
        user_id: uuid.UUID,
        email_message_id: uuid.UUID,
    ) -> AIAnalysis | None:
        """Fetch the most recent AI analysis for a message."""
        stmt = (
            select(AIAnalysis)
            .where(
                AIAnalysis.user_id == user_id,
                AIAnalysis.email_message_id == email_message_id,
            )
            .order_by(AIAnalysis.created_at.desc())
            .options(selectinload(AIAnalysis.extracted_items))
        )
        return db.scalar(stmt)

    @staticmethod
    def save_analysis_with_items(
        db: Session,
        user_id: uuid.UUID,
        email_message_id: uuid.UUID | None,
        email_thread_id: uuid.UUID | None,
        summary: str,
        intent: str,
        priority: str,
        sentiment: str,
        confidence_score: float,
        rationale: str,
        model_name: str,
        prompt_version: str,
        extracted_items: list[dict],
        status: str = "COMPLETED",
        error_message: str | None = None,
    ) -> AIAnalysis:
        """
        Idempotently save or update an AI analysis record and its derived action items.
        
        Enforces composite uniqueness on (user_id, email_message_id, model_name, prompt_version).
        """
        existing = None
        if email_message_id:
            existing = AIRepository.get_analysis_by_message_and_version(
                db, user_id, email_message_id, model_name, prompt_version
            )

        if existing:
            # Update existing record
            existing.summary = summary
            existing.intent = intent
            existing.priority = priority
            existing.sentiment = sentiment
            existing.confidence_score = confidence_score
            existing.rationale = rationale
            existing.status = status
            existing.error_message = error_message
            existing.updated_at = datetime.now()
            
            # Clear old items to re-insert updated extractions
            existing.extracted_items.clear()
            analysis_obj = existing
        else:
            # Create new record
            analysis_obj = AIAnalysis(
                user_id=user_id,
                email_message_id=email_message_id,
                email_thread_id=email_thread_id,
                summary=summary,
                intent=intent,
                priority=priority,
                sentiment=sentiment,
                confidence_score=confidence_score,
                rationale=rationale,
                model_name=model_name,
                prompt_version=prompt_version,
                status=status,
                error_message=error_message,
            )
            db.add(analysis_obj)
            db.flush()

        # Add extracted items
        for item in extracted_items:
            action_obj = ExtractedAction(
                user_id=user_id,
                ai_analysis_id=analysis_obj.id,
                email_message_id=email_message_id,
                email_thread_id=email_thread_id,
                item_type=item.get("item_type", "ACTION"),
                description=item["description"],
                assignee=item.get("assignee"),
                due_date=item.get("due_date"),
                severity_or_priority=item.get("priority", "MEDIUM"),
                confidence_score=item.get("confidence", 1.0),
                evidence_snippet=item.get("evidence_snippet", ""),
                is_evidence_valid=item.get("is_evidence_valid", True),
                status=item.get("status", "PENDING"),
            )
            db.add(action_obj)

        db.commit()
        db.refresh(analysis_obj)
        return analysis_obj

    @staticmethod
    def get_actions_for_user(
        db: Session,
        user_id: uuid.UUID,
        status_filter: str | None = None,
        priority_filter: str | None = None,
    ) -> Sequence[ExtractedAction]:
        """Fetch all action items for a user with optional status and priority filtering."""
        stmt = select(ExtractedAction).where(ExtractedAction.user_id == user_id)
        if status_filter:
            stmt = stmt.where(ExtractedAction.status == status_filter)
        if priority_filter:
            stmt = stmt.where(ExtractedAction.severity_or_priority == priority_filter)
        stmt = stmt.order_by(ExtractedAction.created_at.desc())
        return db.scalars(stmt).all()

    @staticmethod
    def update_action_status(
        db: Session,
        user_id: uuid.UUID,
        action_id: uuid.UUID,
        new_status: str,
        assignee: str | None = None,
        due_date: datetime | None = None,
    ) -> ExtractedAction | None:
        """Update status and assignment details of an extracted action item (Human-in-the-Loop)."""
        stmt = select(ExtractedAction).where(
            ExtractedAction.id == action_id,
            ExtractedAction.user_id == user_id,
        )
        action = db.scalar(stmt)
        if not action:
            return None

        action.status = new_status
        if assignee is not None:
            action.assignee = assignee
        if due_date is not None:
            action.due_date = due_date
        action.updated_at = datetime.now()

        db.commit()
        db.refresh(action)
        return action
