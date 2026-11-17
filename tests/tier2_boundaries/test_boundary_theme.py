"""
Tier 2 — Boundary & Corner Cases: Black/Gray/Red Theme Compliance
Tests boundaries: residual legacy color classes across components, canvas selection rings,
and accessibility contrast guarantees.
"""

import os
import re
import pytest

from tests.test_helpers import calculate_wcag_contrast, scan_frontend_for_forbidden_colors


def test_boundary_theme_no_slate_or_amber_in_action_graph_widget():
    """Verify ActionGraphWidget.tsx contains no legacy slate or amber Tailwind classes."""
    violations = scan_frontend_for_forbidden_colors(
        "frontend/src/components",
        target_components=["ActionGraphWidget.tsx"],
    )
    assert len(violations) == 0, (
        f"Found {len(violations)} forbidden color tokens in ActionGraphWidget: {violations}"
    )


def test_boundary_theme_canvas_selection_ring_color():
    """Verify InteractiveActionGraph canvas selection ring does not use sky blue (#38bdf8)."""
    file_path = "frontend/src/components/InteractiveActionGraph.tsx"
    assert os.path.exists(file_path), f"Missing {file_path}"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "#38bdf8" not in content, (
        "InteractiveActionGraph must not use sky-blue #38bdf8 for selection ring; use red-500 or zinc"
    )


def test_boundary_theme_no_purple_in_document_viewer():
    """Verify DocumentViewerWidget.tsx contains no purple or indigo badge tokens."""
    violations = scan_frontend_for_forbidden_colors(
        "frontend/src/components",
        target_components=["DocumentViewerWidget.tsx"],
    )
    assert len(violations) == 0, (
        f"Found {len(violations)} forbidden color tokens in DocumentViewerWidget: {violations}"
    )


def test_boundary_theme_gmail_sync_widget_palette():
    """Verify GmailSyncWidget.tsx does not use text-slate-400 or other slate tokens."""
    violations = scan_frontend_for_forbidden_colors(
        "frontend/src/components",
        target_components=["GmailSyncWidget.tsx"],
    )
    assert len(violations) == 0, (
        f"Found {len(violations)} forbidden color tokens in GmailSyncWidget: {violations}"
    )


def test_boundary_theme_wcag_aaa_contrast_verification():
    """Verify that light zinc text (#f4f4f5) on black (#000000) achieves AAA standard (>7:1)."""
    ratio = calculate_wcag_contrast("#f4f4f5", "#000000")
    assert ratio >= 15.0, f"Contrast ratio {ratio:.2f} should be very high on black background"
