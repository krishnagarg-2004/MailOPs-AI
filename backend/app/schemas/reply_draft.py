from datetime import datetime
from enum import Enum
import json
from typing import Any, Union
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToneEnum(str, Enum):
    PROFESSIONAL = "PROFESSIONAL"
    CONCISE = "CONCISE"
    URGENT = "URGENT"
    EMPATHETIC = "EMPATHETIC"


class StatusEnum(str, Enum):
    DRAFTED = "DRAFTED"
    EDITED = "EDITED"
    APPROVED = "APPROVED"
    SENT = "SENT"
    DISCARDED = "DISCARDED"


class ReplyDraftCreateRequest(BaseModel):
    email_message_id: uuid.UUID
    tone: ToneEnum = ToneEnum.PROFESSIONAL
    intent: str = "REPLY_RESPONSE"


class ReplyDraftUpdateRequest(BaseModel):
    subject: str | None = None
    body_text: str | None = None
    tone: ToneEnum | None = None
    intent: str | None = None
    status: StatusEnum | None = None


class ProvenanceItem(BaseModel):
    source_type: str  # EMAIL_THREAD, ACTION_ITEM, BUSINESS_DOCUMENT, RAG_CHUNK, ACTION_GRAPH
    source_id: str
    description: str
    verbatim_text: str | None = None


class ReplyDraftResult(BaseModel):
    """Schema returned by AI Provider when generating an email reply draft."""
    subject: str
    body_text: str
    recipient_email: str
    rationale_and_provenance: list[ProvenanceItem] = Field(default_factory=list)

class ReplyDraftRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email_thread_id: uuid.UUID
    email_message_id: uuid.UUID
    gmail_draft_id: str | None = None
    subject: str
    body_text: str
    recipient_email: str
    intent: str
    tone: ToneEnum
    status: StatusEnum
    rationale_and_provenance: list[Union[dict[str, Any], str]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @field_validator("rationale_and_provenance", mode="before")
    @classmethod
    def normalize_provenance(cls, v: Any) -> list[dict[str, Any]]:
        if not v:
            return []
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except Exception:
                v = [{"source_type": "EMAIL_THREAD", "source_id": "seed", "description": v}]
        if not isinstance(v, list):
            v = [v]
        normalized: list[dict[str, Any]] = []
        for item in v:
            if isinstance(item, str):
                normalized.append({
                    "source_type": "EMAIL_THREAD",
                    "source_id": "seed",
                    "description": item,
                })
            elif isinstance(item, dict):
                normalized.append(item)
            elif hasattr(item, "model_dump"):
                normalized.append(item.model_dump())
            else:
                normalized.append({
                    "source_type": "GENERAL",
                    "source_id": "auto",
                    "description": str(item),
                })
        return normalized

    model_config = ConfigDict(from_attributes=True)
