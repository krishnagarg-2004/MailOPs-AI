import json
from pathlib import Path
import pytest
from backend.app.documents.sanitizer import DocumentSanitizer


def test_document_evaluation_suite():
    fixture_path = Path(__file__).parent / "fixtures" / "document_samples.json"
    assert fixture_path.exists(), f"Evaluation fixture missing at {fixture_path}"

    with open(fixture_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    total_samples = len(samples)
    page_boundary_passes = 0
    sanitization_passes = 0

    for sample in samples:
        text = sample["raw_text"]

        # Check page boundary marker requirement
        if sample.get("has_page_boundaries"):
            if "--- [Page" in text:
                page_boundary_passes += 1

        # Check sanitization
        clean = DocumentSanitizer.sanitize_text(text)
        if "\x00" not in clean:
            sanitization_passes += 1

    page_boundary_rate = (page_boundary_passes / total_samples) * 100.0
    sanitization_rate = (sanitization_passes / total_samples) * 100.0

    print(f"\n--- M6 Document Intelligence Evaluation Results (n={total_samples}) ---")
    print(f"Page Boundary Marker Rate: {page_boundary_rate:.1f}%")
    print(f"Sanitization Pass Rate: {sanitization_rate:.1f}%")

    assert page_boundary_rate == 100.0
    assert sanitization_rate == 100.0
