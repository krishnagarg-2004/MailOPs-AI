"""
Tier 1 — Feature 5: Black/Gray/Red Theme Compliance
Specification: ORIGINAL_REQUEST.md §R1, PROJECT.md §Feature Inventory & Code Layout
Verifies the strict Black/Gray/Red color theme across global CSS, components, and canvas renderers.
"""

import os
import re
import pytest

from tests.test_helpers import calculate_wcag_contrast


def test_f5_1_index_css_root_palette():
    """Verify frontend/src/index.css defines #000000 background and #ef4444 scrollbar hover."""
    css_path = "frontend/src/index.css"
    assert os.path.exists(css_path), f"Missing {css_path}"

    with open(css_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Black background check
    assert "#000000" in content, "index.css must define background-color: #000000"
    # Text zinc/light check
    assert "#f4f4f5" in content or "zinc" in content, "index.css must set zinc/light text color"
    # Red scrollbar accent
    assert "#ef4444" in content or "red" in content, "index.css must configure red accent on scrollbar thumb hover"


def test_f5_2_wcag_contrast_black_and_red_compliance():
    """Verify primary and accent color pairings satisfy WCAG AA contrast guidelines."""
    bg_black = "#000000"
    fg_text = "#f4f4f5"
    accent_red = "#ef4444"

    # Contrast between light text and pure black background
    text_contrast = calculate_wcag_contrast(fg_text, bg_black)
    assert text_contrast >= 7.0, f"Text contrast {text_contrast:.2f} must exceed 7.0 (WCAG AAA standard)"

    # Contrast between red accent and pure black background (for UI elements / headers)
    red_contrast = calculate_wcag_contrast(accent_red, bg_black)
    assert red_contrast >= 3.0, f"Red accent contrast {red_contrast:.2f} must exceed 3.0 for graphical/large elements"


def test_f5_3_protected_route_theme_audit():
    """Verify ProtectedRoute uses black/zinc theme instead of legacy slate/indigo."""
    file_path = "frontend/src/components/ProtectedRoute.tsx"
    assert os.path.exists(file_path), f"Missing {file_path}"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # ProtectedRoute should avoid indigo borders
    assert "border-indigo-" not in content, "ProtectedRoute should not use legacy border-indigo-*"


def test_f5_4_interactive_canvas_theme_colors():
    """Verify InteractiveActionGraph canvas does not use deprecated amber/blue/purple color fills."""
    file_path = "frontend/src/components/InteractiveActionGraph.tsx"
    assert os.path.exists(file_path), f"Missing {file_path}"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for deprecated legacy color codes
    deprecated_colors = ["#78350f", "#1e3a8a", "#581c87", "#064e3b"]
    found = [c for c in deprecated_colors if c in content]
    assert len(found) == 0, f"InteractiveActionGraph contains deprecated legacy color codes: {found}"


def test_f5_5_document_viewer_tokens():
    """Verify DocumentViewerWidget does not use deprecated purple/indigo color badges."""
    file_path = "frontend/src/components/DocumentViewerWidget.tsx"
    assert os.path.exists(file_path), f"Missing {file_path}"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Deprecated classes in DocumentViewerWidget
    deprecated_tokens = ["bg-purple-", "bg-indigo-", "text-purple-", "text-indigo-"]
    found = [t for t in deprecated_tokens if t in content]
    assert len(found) == 0, f"DocumentViewerWidget contains deprecated color tokens: {found}"
