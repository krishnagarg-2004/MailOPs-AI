import uuid
from datetime import datetime, timezone
import pytest
from backend.app.schemas.reply_draft import ReplyDraftRead, StatusEnum, ToneEnum
from backend.app.services.reply_draft_service import build_raw_reply_mime


def test_build_raw_reply_mime_headers_and_prefix():
    raw_encoded = build_raw_reply_mime(
        sender="alice@company.com",
        recipient="bob@partner.com",
        subject="Project Update",
        body_text="Here is the requested project update.",
        in_reply_to_msg_id="msg_12345",
        references="msg_12345",
    )

    assert isinstance(raw_encoded, str)
    assert len(raw_encoded) > 0


def test_controlled_tone_enum():
    assert ToneEnum.PROFESSIONAL.value == "PROFESSIONAL"
    assert ToneEnum.CONCISE.value == "CONCISE"
    assert ToneEnum.URGENT.value == "URGENT"
    assert ToneEnum.EMPATHETIC.value == "EMPATHETIC"


def test_reply_draft_read_normalizes_string_provenance():
    """Verify that string items in rationale_and_provenance are seamlessly normalized to dicts."""
    now = datetime.now(timezone.utc)
    raw_data = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "email_thread_id": uuid.uuid4(),
        "email_message_id": uuid.uuid4(),
        "gmail_draft_id": None,
        "subject": "De-escalating payment cluster rate limits",
        "body_text": "We have increased rate limits and confirmed stabilization.",
        "recipient_email": "ops@partner.com",
        "intent": "REPLY_RESPONSE",
        "tone": ToneEnum.PROFESSIONAL,
        "status": StatusEnum.DRAFTED,
        "rationale_and_provenance": [
            "Drafted to de-escalate payment cluster rate limits and confirm threshold stabilization."
        ],
        "created_at": now,
        "updated_at": now,
    }

    read_model = ReplyDraftRead.model_validate(raw_data)
    assert len(read_model.rationale_and_provenance) == 1
    item = read_model.rationale_and_provenance[0]
    assert isinstance(item, dict)
    assert item["description"] == "Drafted to de-escalate payment cluster rate limits and confirm threshold stabilization."
    assert item["source_type"] == "EMAIL_THREAD"


def test_reply_draft_read_handles_dict_and_empty_provenance():
    """Verify ReplyDraftRead handles structured dict items and empty list gracefully."""
    now = datetime.now(timezone.utc)
    base_data = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "email_thread_id": uuid.uuid4(),
        "email_message_id": uuid.uuid4(),
        "gmail_draft_id": "r_12345",
        "subject": "Status Update",
        "body_text": "All systems operational.",
        "recipient_email": "team@company.com",
        "intent": "INFORMATIONAL",
        "tone": ToneEnum.CONCISE,
        "status": StatusEnum.APPROVED,
        "created_at": now,
        "updated_at": now,
    }

    # Dict items
    data_with_dict = {
        **base_data,
        "rationale_and_provenance": [
            {"source_type": "ACTION_ITEM", "source_id": "act_1", "description": "Resolved incident"}
        ],
    }
    model_dict = ReplyDraftRead.model_validate(data_with_dict)
    assert len(model_dict.rationale_and_provenance) == 1
    assert model_dict.rationale_and_provenance[0]["source_id"] == "act_1"

    # Empty list
    data_empty = {**base_data, "rationale_and_provenance": []}
    model_empty = ReplyDraftRead.model_validate(data_empty)
    assert model_empty.rationale_and_provenance == []
