from backend.app.ai.prompts import PROMPT_VERSION, SYSTEM_EXTRACTION_PROMPT, build_email_extraction_prompt


def test_prompt_version():
    assert PROMPT_VERSION == "1.0.0"


def test_system_prompt_contains_untrusted_directives():
    assert "<untrusted_content>" in SYSTEM_EXTRACTION_PROMPT
    assert "VERBATIM" in SYSTEM_EXTRACTION_PROMPT
    assert "SECURITY DIRECTIVE:" in SYSTEM_EXTRACTION_PROMPT


def test_build_email_extraction_prompt():
    subject = "Urgent: Contract Review"
    sender = "legal@enterprise.com"
    body = "Please review the attached contract before EOD."

    prompt = build_email_extraction_prompt(subject, body, sender)
    assert f"Sender: {sender}" in prompt
    assert f"Subject: {subject}" in prompt
    assert "<untrusted_content>" in prompt
    assert body in prompt
    assert "</untrusted_content>" in prompt


def test_build_email_extraction_prompt_truncation():
    long_body = "x" * 15000
    prompt = build_email_extraction_prompt("Long Email", long_body, "sender@test.com")
    assert "[NOTE: Email content was truncated for context safety]" in prompt
    assert len(prompt) < 15000
