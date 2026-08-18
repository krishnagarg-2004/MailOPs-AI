import re
from backend.app.core.config import settings


class DocumentSanitizer:
    """Sanitizes raw extracted document text and formats page-level provenance boundaries."""

    @staticmethod
    def sanitize_text(text: str | None) -> str:
        """Strip null bytes, control characters, and dangerous terminal escape sequences."""
        if not text:
            return ""
        # Remove null bytes
        clean = text.replace("\x00", "")
        # Remove control characters except standard line breaks and tabs
        clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", clean)
        return clean.strip()

    @classmethod
    def format_page_text(cls, pages_text: list[str], max_chars: int | None = None) -> tuple[str, int]:
        """
        Format list of page text strings into structured text with page boundary headers.
        
        Example output:
            --- [Page 1] ---
            Text of page 1...
            
            --- [Page 2] ---
            Text of page 2...
        """
        limit = max_chars or settings.DOC_MAX_EXTRACT_CHARS
        formatted_pages = []
        page_count = len(pages_text)

        for idx, page in enumerate(pages_text, start=1):
            clean_page = cls.sanitize_text(page)
            if clean_page:
                formatted_pages.append(f"--- [Page {idx}] ---\n{clean_page}")

        full_text = "\n\n".join(formatted_pages)
        if len(full_text) > limit:
            full_text = full_text[:limit] + "\n\n[NOTE: Document text truncated for context safety]"

        return full_text, page_count
