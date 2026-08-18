import re


class TextChunker:
    """Utility for splitting emails and document extractions into semantic search chunks."""

    @staticmethod
    def chunk_email_message(text: str, max_chars: int = 2000, overlap: int = 200) -> list[str]:
        """Split plain text email message body into overlapping character windows."""
        if not text or not text.strip():
            return []

        clean_text = text.strip()
        if len(clean_text) <= max_chars:
            return [clean_text]

        chunks = []
        start = 0
        text_len = len(clean_text)

        while start < text_len:
            end = min(start + max_chars, text_len)
            chunk = clean_text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())

            if end == text_len:
                break
            start += max_chars - overlap

        return chunks

    @staticmethod
    def chunk_document_extraction(extracted_text: str, max_chars: int = 2000) -> list[tuple[str, int | None]]:
        """
        Split document extraction text into (chunk_text, page_number) tuples.
        Respects page boundary headers ('--- [Page X] ---') and page provenance.
        """
        if not extracted_text or not extracted_text.strip():
            return []

        page_blocks = re.split(r"(--- \[Page \d+\] ---)", extracted_text)
        results: list[tuple[str, int | None]] = []

        current_page_num: int | None = None
        current_text_buf = ""

        for block in page_blocks:
            match = re.match(r"--- \[Page (\d+)\] ---", block.strip())
            if match:
                # Flush existing buffer before changing page
                if current_text_buf.strip():
                    results.extend(TextChunker._subchunk(current_text_buf.strip(), current_page_num, max_chars))
                    current_text_buf = ""
                current_page_num = int(match.group(1))
            else:
                current_text_buf += block

        if current_text_buf.strip():
            results.extend(TextChunker._subchunk(current_text_buf.strip(), current_page_num, max_chars))

        return results if results else [(extracted_text.strip(), 1)]

    @staticmethod
    def _subchunk(text: str, page_num: int | None, max_chars: int) -> list[tuple[str, int | None]]:
        """Sub-split large single page text if it exceeds max_chars."""
        if len(text) <= max_chars:
            return [(text, page_num)]

        res = []
        for i in range(0, len(text), max_chars - 100):
            sub = text[i : i + max_chars].strip()
            if sub:
                res.append((sub, page_num))
        return res
