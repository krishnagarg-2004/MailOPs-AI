"""
Tests for DSPy MIPRO Optimization Module.
Verifies Signature mapping, composite metric evaluation, and prompt compilation pipeline.
"""

from pathlib import Path
import pytest

dspy = pytest.importorskip("dspy")

from backend.app.ai.optimization.signatures import EmailIntelligenceSignature, RAGQuestionAnsweringSignature
from backend.app.ai.optimization.metrics import mailops_composite_metric
from backend.app.ai.optimization.run_mipro import EmailExtractorModule, load_dataset
from backend.app.ai.prompts import get_active_system_prompt, SYSTEM_EXTRACTION_PROMPT


def test_dspy_signatures_initialization():
    """Verify DSPy signatures instantiate and define expected fields."""
    sig = EmailIntelligenceSignature
    assert "sender" in sig.input_fields
    assert "subject" in sig.input_fields
    assert "body" in sig.input_fields
    assert "intent" in sig.output_fields
    assert "actions" in sig.output_fields

    rag_sig = RAGQuestionAnsweringSignature
    assert "context" in rag_sig.input_fields
    assert "question" in rag_sig.input_fields
    assert "answer" in rag_sig.output_fields
    assert "citations" in rag_sig.output_fields


def test_mailops_composite_metric_scoring():
    """Verify composite metric correctly weights intent, verbatim evidence, and structure."""
    body_text = "Please submit the quarterly VAT return before Friday."
    gold = dspy.Example(
        sender="boss@enterprise.com",
        subject="VAT Return Due",
        body=body_text,
        expected_intent="WORK_REQUEST",
        expected_actions=[{"description": "Submit VAT return", "evidence_snippet": "submit the quarterly VAT return"}],
    )

    # 1. Perfect prediction (Intent matches, snippet is exact verbatim)
    pred_perfect = dspy.Prediction(
        summary="VAT return task due Friday",
        intent="WORK_REQUEST",
        priority="HIGH",
        actions=[{"description": "Submit VAT return", "evidence_snippet": "submit the quarterly VAT return"}],
    )
    score_perfect = mailops_composite_metric(gold, pred_perfect)
    assert score_perfect == 1.0

    # 2. Rephrased/Hallucinated snippet (Evidence fails verbatim check)
    pred_hallucinated = dspy.Prediction(
        summary="VAT return task due Friday",
        intent="WORK_REQUEST",
        priority="HIGH",
        actions=[{"description": "Submit VAT return", "evidence_snippet": "submit your tax paperwork immediately"}],
    )
    score_hallucinated = mailops_composite_metric(gold, pred_hallucinated)
    # 0.40 (intent) + 0.00 (evidence failed) + 0.20 (summary) = 0.60
    assert score_hallucinated == 0.60

    # 3. Wrong intent
    pred_wrong_intent = dspy.Prediction(
        summary="VAT return task due Friday",
        intent="FINANCIAL_INVOICE",
        priority="HIGH",
        actions=[{"description": "Submit VAT return", "evidence_snippet": "submit the quarterly VAT return"}],
    )
    score_wrong_intent = mailops_composite_metric(gold, pred_wrong_intent)
    # 0.00 (intent wrong) + 0.40 (evidence passed) + 0.20 (summary) = 0.60
    assert score_wrong_intent == 0.60


def test_load_dataset_into_dspy_examples():
    """Verify fixtures load properly into dspy.Example format."""
    dataset_path = Path(__file__).resolve().parents[1] / "evaluation" / "fixtures" / "email_samples.json"
    assert dataset_path.exists()

    examples = load_dataset(dataset_path)
    assert len(examples) > 0
    first_ex = examples[0]
    assert hasattr(first_ex, "body")
    assert hasattr(first_ex, "expected_intent")


def test_get_active_system_prompt_fallback():
    """Verify get_active_system_prompt falls back safely when no compiled file exists."""
    prompt = get_active_system_prompt()
    assert prompt == SYSTEM_EXTRACTION_PROMPT
