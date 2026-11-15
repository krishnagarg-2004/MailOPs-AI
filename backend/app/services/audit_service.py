"""
Audit Logging Service for MailOps AI.
Provides centralized helpers for recording compliance, draft approval, and action assignment events.
"""

import logging
import uuid
from typing import Any
from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog

logger = logging.getLogger("mailops.audit")


class AuditService:
    """Centralized enterprise audit logging service."""

    @classmethod
    def record_event(
        cls,
        db: Session,
        action_type: str,
        target_entity_type: str,
        target_entity_id: str | None = None,
        user_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Appends an immutable audit event to the audit_logs table."""
        event = AuditLog(
            user_id=user_id,
            action_type=action_type,
            target_entity_type=target_entity_type,
            target_entity_id=target_entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        logger.info(
            f"AUDIT_RECORD: action={action_type} target={target_entity_type}:{target_entity_id} "
            f"user_id={user_id} ip={ip_address}"
        )
        return event
