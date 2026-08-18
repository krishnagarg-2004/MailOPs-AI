import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.api.v1.auth import get_current_user
from backend.app.db.session import get_db
from backend.app.models.business_document_extraction import BusinessDocumentExtraction
from backend.app.models.user import User
from backend.app.schemas.document import BusinessDocumentExtractionRead, DocumentExtractionRead
from backend.app.services.business_document_ai_service import BusinessDocumentAIService
from backend.app.services.document_service import DocumentProcessingService

router = APIRouter(prefix="/documents", tags=["Document Intelligence"])


@router.post("/process/{attachment_id}", response_model=DocumentExtractionRead)
async def process_document_attachment(
    attachment_id: uuid.UUID,
    force: bool = Query(default=False, description="Force re-processing of attachment"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger Layer 1 text extraction and OCR processing for an email attachment."""
    try:
        extraction = DocumentProcessingService.process_attachment(
            db=db,
            user_id=current_user.id,
            attachment_id=attachment_id,
            force_reprocess=force,
        )
        return extraction
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {exc}",
        )


@router.get("/extraction/{attachment_id}", response_model=DocumentExtractionRead)
async def get_document_extraction(
    attachment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve raw text extraction, page count, and OCR status for an attachment."""
    extraction = DocumentProcessingService.get_extraction(
        db=db,
        user_id=current_user.id,
        attachment_id=attachment_id,
    )
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No document extraction found for attachment {attachment_id}",
        )
    return extraction


@router.post("/analyze-business-doc/{attachment_id}", response_model=BusinessDocumentExtractionRead)
async def analyze_business_document(
    attachment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger Layer 2 AI business document intelligence parsing (Invoices, Contracts)."""
    service = BusinessDocumentAIService()
    try:
        biz_extraction = await service.analyze_business_document(
            db=db,
            user_id=current_user.id,
            attachment_id=attachment_id,
        )
        return biz_extraction
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Business document analysis failed: {exc}",
        )


@router.get("/business-doc/{attachment_id}", response_model=BusinessDocumentExtractionRead)
async def get_business_document_extraction(
    attachment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve existing structured invoice or contract extraction fields for an attachment."""
    biz_extraction = (
        db.query(BusinessDocumentExtraction)
        .filter(
            BusinessDocumentExtraction.attachment_id == attachment_id,
            BusinessDocumentExtraction.user_id == current_user.id,
        )
        .first()
    )
    if not biz_extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No business document intelligence found for attachment {attachment_id}",
        )
    return biz_extraction
