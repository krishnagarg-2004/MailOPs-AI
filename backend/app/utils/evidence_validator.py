import re


class EvidenceValidator:
    """Validates that evidence snippets extracted by AI models exist verbatim within source email content."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Collapse whitespace and convert to lowercase for flexible verbatim matching."""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip().lower()

    @classmethod
    def validate_snippet(cls, snippet: str | None, source_text: str | None) -> bool:
        """
        Validate whether a snippet exists verbatim (or normalized verbatim) within source text.
        
        Invariant:
            An empty snippet is considered invalid unless no extraction occurred.
            Non-empty snippets MUST appear within the source email text.
        """
        if not snippet or not snippet.strip():
            return False
        if not source_text or not source_text.strip():
            return False

        clean_snippet = snippet.strip()
        clean_source = source_text

        # 1. Exact string match check
        if clean_snippet in clean_source:
            return True

        # 2. Whitespace-normalized & case-insensitive match check
        norm_snippet = cls.normalize_text(clean_snippet)
        norm_source = cls.normalize_text(clean_source)

        return norm_snippet in norm_source
