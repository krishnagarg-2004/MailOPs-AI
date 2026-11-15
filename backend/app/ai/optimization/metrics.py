"""
DSPy Evaluation Metrics and Guardrails for MailOps AI.
Enforces intent accuracy, schema integrity, and zero-hallucination verbatim quote compliance.
"""

from typing import Any
import dspy
from backend.app.utils.evidence_validator import EvidenceValidator


def mailops_composite_metric(gold: dspy.Example, pred: Any, trace=None) -> float:
    """
    Evaluates extraction quality on a 0.0 to 1.0 continuous scale:
    - 40% Intent Classification Accuracy (exact enum match)
    - 40% Verbatim Evidence Guardrail (evidence_snippet strictly found in body)
    - 20% Structural Completeness (summary & actions populated)
    """
    total_score = 0.0

    # 1. Intent Match (40% weight)
    pred_intent = str(getattr(pred, "intent", "")).strip().upper()
    gold_intent = str(getattr(gold, "expected_intent", "")).strip().upper()
    if pred_intent and pred_intent == gold_intent:
        total_score += 0.40

    # 2. Verbatim Evidence Verification (40% weight)
    pred_actions = getattr(pred, "actions", [])
    if isinstance(pred_actions, list) and len(pred_actions) > 0:
        valid_snippets = 0
        for item in pred_actions:
            snippet = item.get("evidence_snippet", "") if isinstance(item, dict) else getattr(item, "evidence_snippet", "")
            if snippet and EvidenceValidator.validate_snippet(snippet, gold.body):
                valid_snippets += 1
        
        snippet_ratio = valid_snippets / len(pred_actions)
        total_score += 0.40 * snippet_ratio
    else:
        # If the sample legitimately had no actions, give full credit
        expected_actions = getattr(gold, "expected_actions", [])
        if not expected_actions:
            total_score += 0.40

    # 3. Structural Integrity (20% weight)
    has_summary = bool(getattr(pred, "summary", "").strip())
    total_score += 0.20 if has_summary else 0.0

    return round(total_score, 4)
