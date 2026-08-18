export type DocumentCategoryEnum = 'INVOICE' | 'CONTRACT' | 'RECEIPT' | 'PURCHASE_ORDER' | 'OTHER';
export type ExtractionMethodEnum = 'NATIVE_TEXT' | 'OCR_TESSERACT' | 'HYBRID';

export interface DocumentExtractionResult {
  id: string;
  user_id: string;
  attachment_id: string;
  email_message_id: string;
  file_type: string;
  extraction_method: ExtractionMethodEnum;
  extracted_text: string;
  char_count: number;
  page_count?: number;
  is_ocr_applied: boolean;
  status: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface BusinessDocumentExtractionResult {
  id: string;
  user_id: string;
  attachment_id: string;
  document_extraction_id: string;
  document_category: DocumentCategoryEnum;
  extracted_data: Record<string, any>;
  vendor_or_party?: string;
  document_reference_number?: string;
  document_date?: string;
  due_or_expiration_date?: string;
  financial_total?: number;
  confidence_score: number;
  status: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}
