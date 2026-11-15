"""
Unit tests for PII Guardrail and LLM Observability Telemetry.
"""

from backend.app.core.pii_guardrail import PIIGuardrail
from backend.app.core.telemetry import LLMObservability


def test_pii_guardrail_redacts_credentials_and_secrets():
    """Verify API keys, bearer tokens, passwords, and SSNs are redacted."""
    raw_email = (
        "Hi Alex, please find the credentials:\n"
        "OpenAI API Key: sk-abcdef1234567890abcdef1234567890\n"
        "Customer SSN: 123-45-6789\n"
        "Credit card on file: 4111-2222-3333-4444\n"
        "Database password: password='SuperSecretPassword123'\n"
    )

    result = PIIGuardrail.sanitize(raw_email)

    assert result.redacted_count >= 4
    assert "sk-abcdef1234567890" not in result.sanitized_text
    assert "123-45-6789" not in result.sanitized_text
    assert "4111-2222-3333-4444" not in result.sanitized_text
    assert "SuperSecretPassword123" not in result.sanitized_text

    assert "[REDACTED_API_KEY]" in result.sanitized_text
    assert "[REDACTED_SSN]" in result.sanitized_text
    assert "[REDACTED_CREDIT_CARD]" in result.sanitized_text
    assert "password=[REDACTED_SECRET]" in result.sanitized_text


def test_pii_guardrail_handles_clean_text():
    """Clean operational emails without secrets should remain unmutated."""
    clean_text = "Let's schedule our quarterly team sync for Thursday at 10 AM EST."
    result = PIIGuardrail.sanitize(clean_text)

    assert result.redacted_count == 0
    assert result.sanitized_text == clean_text
    assert len(result.detected_types) == 0


def test_llm_observability_tracks_tokens_and_cost():
    """Verify LLM telemetry estimates tokens and calculates compute costs accurately."""
    metrics = LLMObservability.track_invocation(
        model_name="gemini-2.5-flash",
        input_text="A" * 400,  # ~100 tokens
        output_text="B" * 200,  # ~50 tokens
        latency_ms=125.4,
        metadata={"user_id": "test-user"},
    )

    assert metrics.model_name == "gemini-2.5-flash"
    assert metrics.prompt_tokens == 100
    assert metrics.completion_tokens == 50
    assert metrics.total_tokens == 150
    assert metrics.latency_ms == 125.4
    assert metrics.estimated_cost_usd > 0
