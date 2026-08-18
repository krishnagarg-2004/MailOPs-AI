from datetime import datetime
from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict, Field


class DocumentCategoryEnum(str, Enum):
    INVOICE = "INVOICE"
    CONTRACT = "CONTRACT"
    RECEIPT = "RECEIPT"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    OTHER = "OTHER"


class ExtractionMethodEnum(str, Enum):
    NATIVE_TEXT = "NATIVE_TEXT"
    OCR_TESSERACT = "OCR_TESSERACT"
    HYBRID = "HYBRID"


class InvoiceExtractionSchema(BaseModel):
    vendor_name: str | None = Field(default=None, description="Vendor or issuing company name")
    invoice_number: str | None = Field(default=None, description="Invoice reference number")
    invoice_date: str | None = Field(default=None, description="Invoice issuance date (ISO string)")
    due_date: str | None = Field(default=None, description="Payment due date (ISO string)")
    total_amount: float | None = Field(default=None, description="Total financial amount due")
    tax_or_gst: float | None = Field(default=None, description="Tax or GST value included")
    currency: str = Field(default="USD", description="Financial currency code")
    payment_terms: str | None = Field(default=None, description="Payment terms e.g. Net 30")
    line_items_summary: str | None = Field(default=None, description="Summary of billed products/services")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Model confidence score")
    evidence_snippet: str = Field(default="", description="Verbatim text excerpt supporting this invoice extraction")
    evidence_page_number: int | None = Field(default=None, description="Page number where evidence snippet occurs")


class ContractExtractionSchema(BaseModel):
    contracting_parties: list[str] = Field(default_factory=list, description="Parties entering into the contract")
    effective_date: str | None = Field(default=None, description="Contract effective start date")
    expiration_date: str | None = Field(default=None, description="Contract expiration or end date")
    key_obligations: list[str] = Field(default_factory=list, description="Primary duties or deliverables")
    renewal_terms: str | None = Field(default=None, description="Contract renewal or extension terms")
    risk_clauses: list[str] = Field(default_factory=list, description="Identified risk, indemnity, or liability clauses")
    governing_law: str | None = Field(default=None, description="Jurisdiction or governing law clause")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Model confidence score")
    evidence_snippet: str = Field(default="", description="Verbatim text excerpt supporting this contract extraction")
    evidence_page_number: int | None = Field(default=None, description="Page number where evidence snippet occurs")


class DocumentExtractionRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    attachment_id: uuid.UUID
    email_message_id: uuid.UUID
    file_type: str
    extraction_method: ExtractionMethodEnum
    extracted_text: str
    char_count: int
    page_count: int | None = None
    is_ocr_applied: bool
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BusinessDocumentExtractionRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    attachment_id: uuid.UUID
    document_extraction_id: uuid.UUID
    document_category: DocumentCategoryEnum
    extracted_data: dict
    vendor_or_party: str | None = None
    document_reference_number: str | None = None
    document_date: datetime | None = None
    due_or_expiration_date: datetime | None = None
    financial_total: float | None = None
    confidence_score: float
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
