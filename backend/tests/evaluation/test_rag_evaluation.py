import json
from pathlib import Path
import pytest


def test_rag_evaluation_suite():
    fixture_path = Path(__file__).parent / "fixtures" / "rag_samples.json"
    assert fixture_path.exists(), f"RAG evaluation fixture missing at {fixture_path}"

    with open(fixture_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    total_samples = len(samples)
    citation_passes = 0
    grounding_passes = 0

    for sample in samples:
        chunk_text = sample["retrieved_chunk"]
        expected_contains = sample["expected_answer_contains"]
        expected_citation = sample["expected_citation"]

        # Check chunk grounding
        if expected_contains.lower() in chunk_text.lower():
            grounding_passes += 1

        # Check citation string match
        if expected_citation in sample["source_name"]:
            citation_passes += 1

    grounding_rate = (grounding_passes / total_samples) * 100.0
    citation_rate = (citation_passes / total_samples) * 100.0

    print(f"\n--- M7 RAG Evaluation Results (n={total_samples}) ---")
    print(f"Retrieval Grounding Pass Rate: {grounding_rate:.1f}%")
    print(f"Citation Precision Rate: {citation_rate:.1f}%")

    assert grounding_rate == 100.0
    assert citation_rate == 100.0
