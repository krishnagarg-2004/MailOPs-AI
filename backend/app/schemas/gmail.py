from datetime import datetime
import json
import uuid
from pydantic import BaseModel, ConfigDict, field_validator


class GmailSyncStateResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    sync_status: str
    last_synced_at: datetime | None = None
    synced_message_count: int
    error_message: str | None = None
    last_history_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class AttachmentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    mime_type: str | None = None
    size_bytes: int
    is_downloaded: bool

    model_config = ConfigDict(from_attributes=True)


class EmailMessageResponse(BaseModel):
    id: uuid.UUID
    gmail_message_id: str
    gmail_thread_id: str
    sender: str | None = None
    recipients: str | None = None
    subject: str | None = None
    snippet: str | None = None
    body_plain: str | None = None
    body_html: str | None = None
    sent_at: datetime | None = None
    received_at: datetime | None = None
    labels: list[str] = []
    has_attachments: bool
    attachments: list[AttachmentResponse] = []

    @field_validator("labels", mode="before")
    @classmethod
    def parse_labels_json(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        if isinstance(v, list):
            return v
        return []

    model_config = ConfigDict(from_attributes=True)


class EmailThreadResponse(BaseModel):
    id: uuid.UUID
    gmail_thread_id: str
    snippet: str | None = None
    last_message_at: datetime | None = None
    messages: list[EmailMessageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SyncTriggerResponse(BaseModel):
    status: str
    message: str
