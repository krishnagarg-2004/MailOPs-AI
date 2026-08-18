import pytest
from backend.app.utils.evidence_validator import EvidenceValidator


def test_evidence_validator_exact_match():
    source_text = "Please submit the final quarterly budget report by Friday end of day."
    snippet = "quarterly budget report by Friday"
    assert EvidenceValidator.validate_snippet(snippet, source_text) is True


def test_evidence_validator_whitespace_normalized():
    source_text = "Please submit the   final quarterly\n  budget report by Friday end of day."
    snippet = "quarterly budget report by Friday"
    assert EvidenceValidator.validate_snippet(snippet, source_text) is True


def test_evidence_validator_case_insensitive():
    source_text = "PLEASE SUBMIT THE REPORT BY FRIDAY."
    snippet = "please submit the report"
    assert EvidenceValidator.validate_snippet(snippet, source_text) is True


def test_evidence_validator_invalid_snippet_hallucinated():
    source_text = "Hi Team, let's meet tomorrow at 10 AM."
    snippet = "Please process invoice payment of $5000"
    assert EvidenceValidator.validate_snippet(snippet, source_text) is False


def test_evidence_validator_empty_inputs():
    assert EvidenceValidator.validate_snippet("", "Some text") is False
    assert EvidenceValidator.validate_snippet("Some snippet", "") is False
    assert EvidenceValidator.validate_snippet(None, None) is False
