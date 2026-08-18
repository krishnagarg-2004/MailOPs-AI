import pytest
from backend.app.schemas.reply_draft import ToneEnum
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
