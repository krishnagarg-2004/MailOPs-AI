import logging
from pathlib import Path
from backend.app.core.config import settings
from backend.app.documents.sanitizer import DocumentSanitizer

logger = logging.getLogger(__name__)


class ImageParser:
    """Extracts text from image files (PNG, JPEG) using PIL pre-processing and Tesseract OCR."""

    @classmethod
    def parse_image(cls, file_path: Path | str) -> tuple[str, int, str, bool]:
        """
        Parse image file and return (extracted_text, page_count=1, extraction_method="OCR_TESSERACT", is_ocr_applied=True).
        
        Enforces pixel and dimension safety bounds before decoding.
        Raises RuntimeError if Tesseract OCR fails or binary is missing.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found at {path}")

        try:
            from PIL import Image, ImageOps
            import pytesseract
        except ImportError as exc:
            raise RuntimeError("Pillow or pytesseract package is not installed") from exc

        if settings.OCR_TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.OCR_TESSERACT_PATH

        try:
            with Image.open(path) as img:
                width, height = img.size
                total_pixels = width * height

                # Enforce pixel and dimension safety limits
                if total_pixels > settings.DOC_MAX_IMAGE_PIXELS:
                    raise ValueError(
                        f"Image resolution ({width}x{height} = {total_pixels} px) exceeds safety limit ({settings.DOC_MAX_IMAGE_PIXELS} px)"
                    )
                if width > settings.DOC_MAX_IMAGE_DIMENSION or height > settings.DOC_MAX_IMAGE_DIMENSION:
                    raise ValueError(
                        f"Image dimension ({width}x{height}) exceeds maximum allowed dimension ({settings.DOC_MAX_IMAGE_DIMENSION} px)"
                    )

                # Pre-processing: convert to grayscale and auto-contrast
                gray = ImageOps.grayscale(img)
                processed_img = ImageOps.autocontrast(gray)

                raw_text = pytesseract.image_to_string(processed_img, lang="eng")
                clean_text = DocumentSanitizer.sanitize_text(raw_text)

                if not clean_text:
                    clean_text = DocumentSanitizer.sanitize_text(pytesseract.image_to_string(img, lang="eng"))

                formatted_text, _ = DocumentSanitizer.format_page_text([clean_text])
                return formatted_text, 1, "OCR_TESSERACT", True

        except ValueError as val_err:
            raise val_err
        except Exception as exc:
            raise RuntimeError(f"Tesseract OCR image extraction failed: {exc}") from exc
