from datetime import datetime
from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict, Field


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
    rationale_and_provenance: list[dict]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
