import logging
from pathlib import Path
import uuid
from sqlalchemy.orm import Session
from backend.app.documents.docx_parser import DOCXParser
from backend.app.documents.image_parser import ImageParser
from backend.app.documents.pdf_parser import PDFParser
from backend.app.models.attachment import Attachment
from backend.app.models.document_extraction import DocumentExtraction

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """Layer 1 Service coordinating file extraction, OCR rendering, and database persistence."""

    @classmethod
    def process_attachment(
        self,
        db: Session,
        user_id: uuid.UUID,
        attachment_id: uuid.UUID,
        force_reprocess: bool = False,
    ) -> DocumentExtraction:
        """
        Extract text from an email attachment file, handle OCR fallback, and save to document_extractions table.
        """
        # 1. Fetch attachment enforcing user isolation
        attachment = (
            db.query(Attachment)
            .filter(Attachment.id == attachment_id, Attachment.user_id == user_id)
            .first()
        )
        if not attachment:
            raise ValueError(f"Attachment {attachment_id} not found for user {user_id}")

        if not attachment.is_downloaded or not attachment.storage_path:
            raise ValueError(f"Attachment {attachment_id} is not downloaded on disk.")

        file_path = Path(attachment.storage_path)
        if not file_path.exists():
            # Try absolute path if relative fails
            file_path = Path.cwd() / attachment.storage_path
            if not file_path.exists():
                raise FileNotFoundError(f"Attachment file missing at path {attachment.storage_path}")

        # 2. Check for existing extraction
        existing = (
            db.query(DocumentExtraction)
            .filter(DocumentExtraction.attachment_id == attachment_id, DocumentExtraction.user_id == user_id)
            .first()
        )
        if existing and existing.status == "COMPLETED" and not force_reprocess:
            return existing

        # 3. Route to specific parser based on file extension
        ext = file_path.suffix.lower()
        if not ext and attachment.filename:
            ext = Path(attachment.filename).suffix.lower()

        extracted_text = ""
        page_count = 1
        extraction_method = "NATIVE_TEXT"
        is_ocr_applied = False
        file_type = "OTHER"
        status = "COMPLETED"
        error_message = None

        try:
            if ext == ".pdf":
                file_type = "PDF"
                extracted_text, page_count, extraction_method, is_ocr_applied = PDFParser.parse_pdf(file_path)
            elif ext in [".png", ".jpg", ".jpeg", ".tif", ".tiff"]:
                file_type = "IMAGE"
                extracted_text, page_count, extraction_method, is_ocr_applied = ImageParser.parse_image(file_path)
            elif ext == ".docx":
                file_type = "DOCX"
                extracted_text, page_count, extraction_method, is_ocr_applied = DOCXParser.parse_docx(file_path)
            else:
                raise ValueError(f"Unsupported attachment file extension: '{ext}'")

        except Exception as exc:
            logger.error("Document extraction failed for attachment %s: %s", attachment_id, exc)
            status = "FAILED"
            error_message = str(exc)
            extracted_text = ""

        # 4. Save or update DocumentExtraction record
        if existing:
            existing.file_type = file_type
            existing.extraction_method = extraction_method
            existing.extracted_text = extracted_text
            existing.char_count = len(extracted_text)
            existing.page_count = page_count
            existing.is_ocr_applied = is_ocr_applied
            existing.status = status
            existing.error_message = error_message
            extraction_obj = existing
        else:
            extraction_obj = DocumentExtraction(
                user_id=user_id,
                attachment_id=attachment_id,
                email_message_id=attachment.message_id,
                file_type=file_type,
                extraction_method=extraction_method,
                extracted_text=extracted_text,
                char_count=len(extracted_text),
                page_count=page_count,
                is_ocr_applied=is_ocr_applied,
                status=status,
                error_message=error_message,
            )
            db.add(extraction_obj)

        db.commit()
        db.refresh(extraction_obj)
        return extraction_obj

    @classmethod
    def get_extraction(
        cls,
        db: Session,
        user_id: uuid.UUID,
        attachment_id: uuid.UUID,
    ) -> DocumentExtraction | None:
        """Fetch existing DocumentExtraction record for attachment."""
        return (
            db.query(DocumentExtraction)
            .filter(DocumentExtraction.attachment_id == attachment_id, DocumentExtraction.user_id == user_id)
            .first()
        )
