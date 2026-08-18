import logging
from pathlib import Path
from backend.app.core.config import settings
from backend.app.documents.sanitizer import DocumentSanitizer

logger = logging.getLogger(__name__)


class PDFParser:
    """Extracts text from PDF documents using native pypdf text streams or pdf2image/pytesseract OCR fallback."""

    @classmethod
    def parse_pdf(cls, file_path: Path | str) -> tuple[str, int, str, bool]:
        """
        Parse PDF file and return (extracted_text, page_count, extraction_method, is_ocr_applied).
        
        Invariant:
            If native text < threshold and Tesseract/Poppler OCR is required but missing/failing,
            raises RuntimeError to fail processing explicitly.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found at {path}")

        try:
            import pypdf
        except ImportError as exc:
            raise RuntimeError("pypdf package is not installed") from exc

        reader = pypdf.PdfReader(str(path))
        total_pages = len(reader.pages)
        pages_to_process = min(total_pages, settings.DOC_MAX_PDF_PAGES)

        native_pages_text: list[str] = []
        total_chars = 0

        for idx in range(pages_to_process):
            page_text = reader.pages[idx].extract_text() or ""
            clean = DocumentSanitizer.sanitize_text(page_text)
            native_pages_text.append(clean)
            total_chars += len(clean)

        avg_chars_per_page = (total_chars / pages_to_process) if pages_to_process > 0 else 0

        # Check if native text is sufficient
        if avg_chars_per_page >= settings.DOC_OCR_MIN_CHAR_THRESHOLD and total_chars > 0:
            formatted_text, _ = DocumentSanitizer.format_page_text(native_pages_text)
            return formatted_text, total_pages, "NATIVE_TEXT", False

        # Scanned PDF detected: Fallback OCR required
        logger.info("PDF %s has low native text (avg %.1f chars/page). Triggering OCR fallback...", path.name, avg_chars_per_page)
        return cls._parse_pdf_ocr(path, total_pages)

    @classmethod
    def _parse_pdf_ocr(cls, path: Path, total_pages: int) -> tuple[str, int, str, bool]:
        """Render PDF pages using pdf2image (host Poppler) and extract text via pytesseract (host Tesseract)."""
        try:
            import pdf2image
            import pytesseract
        except ImportError as exc:
            raise RuntimeError("pdf2image or pytesseract library is not installed") from exc

        poppler_kw = {}
        if settings.POPPLER_PATH:
            poppler_kw["poppler_path"] = settings.POPPLER_PATH

        if settings.OCR_TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.OCR_TESSERACT_PATH

        ocr_pages_count = min(total_pages, settings.DOC_MAX_OCR_PAGES)

        try:
            images = pdf2image.convert_from_path(
                str(path),
                first_page=1,
                last_page=ocr_pages_count,
                **poppler_kw,
            )
        except Exception as exc:
            raise RuntimeError(f"PDF OCR page rendering failed (Poppler dependency issue): {exc}") from exc

        ocr_pages_text: list[str] = []
        for idx, img in enumerate(images, start=1):
            try:
                page_text = pytesseract.image_to_string(img, lang="eng")
                clean = DocumentSanitizer.sanitize_text(page_text)
                ocr_pages_text.append(clean)
            except Exception as exc:
                raise RuntimeError(f"Tesseract OCR failed on page {idx} (Tesseract dependency issue): {exc}") from exc

        formatted_text, _ = DocumentSanitizer.format_page_text(ocr_pages_text)
        if not formatted_text.strip():
            raise RuntimeError("OCR executed but yielded empty text output")

        return formatted_text, total_pages, "OCR_TESSERACT", True
