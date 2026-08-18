import json
from pathlib import Path
import pytest
from backend.app.ai.provider import MockAIProvider
from backend.app.utils.evidence_validator import EvidenceValidator


@pytest.mark.asyncio
async def test_ai_evaluation_suite():
    """
    Automated evaluation suite on regression fixture dataset.
    
    Evaluates:
    - Schema Validity Rate
    - Intent Classification Accuracy
    - Evidence Snippet Verbatim Validity
    """
    fixture_path = Path(__file__).parent / "fixtures" / "email_samples.json"
    assert fixture_path.exists(), "Evaluation fixture dataset file missing"

    with open(fixture_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    provider = MockAIProvider()

    valid_schema_count = 0
    intent_match_count = 0
    valid_evidence_count = 0
    total_evidence_extracted = 0

    for sample in samples:
        result = await provider.extract_email_intelligence(
            subject=sample["subject"],
            body=sample["body"],
            sender=sample["sender"],
        )

        # 1. Schema Validity Check
        if result and hasattr(result, "summary") and hasattr(result, "intent"):
            valid_schema_count += 1

        # 2. Intent Classification Match Check
        if result.intent.value == sample["expected_intent"]:
            intent_match_count += 1

        # 3. Evidence Snippet Verbatim Verification
        for action in result.actions:
            total_evidence_extracted += 1
            if EvidenceValidator.validate_snippet(action.evidence_snippet, sample["body"]):
                valid_evidence_count += 1

    total_samples = len(samples)
    schema_pass_rate = valid_schema_count / total_samples
    intent_accuracy = intent_match_count / total_samples
    evidence_validity_rate = (valid_evidence_count / total_evidence_extracted) if total_evidence_extracted > 0 else 1.0

    print(f"\n--- AI Evaluation Results (Regression Set n={total_samples}) ---")
    print(f"Schema Validity Rate: {schema_pass_rate * 100:.1f}%")
    print(f"Intent Classification Accuracy: {intent_accuracy * 100:.1f}%")
    print(f"Evidence Snippet Verbatim Rate: {evidence_validity_rate * 100:.1f}%")

    assert schema_pass_rate == 1.0, "Schema validity rate must be 100%"
    assert intent_accuracy >= 0.80, "Intent accuracy on regression set must be >= 80%"
    assert evidence_validity_rate >= 0.90, "Evidence snippet verbatim rate must be >= 90%"
