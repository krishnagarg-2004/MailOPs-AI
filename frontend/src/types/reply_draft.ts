export type ToneEnum = 'PROFESSIONAL' | 'CONCISE' | 'URGENT' | 'EMPATHETIC';
export type StatusEnum = 'DRAFTED' | 'EDITED' | 'APPROVED' | 'SENT' | 'DISCARDED';

export interface ProvenanceItem {
  source_type: string;
  source_id: string;
  description: string;
  verbatim_text?: string;
}

export interface ReplyDraftResult {
  id: string;
  user_id: string;
  email_thread_id: string;
  email_message_id: string;
  gmail_draft_id?: string;
  subject: string;
  body_text: string;
  recipient_email: string;
  intent: string;
  tone: ToneEnum;
  status: StatusEnum;
  rationale_and_provenance: ProvenanceItem[];
  created_at: string;
  updated_at: string;
}

export interface ReplyDraftCreateRequest {
  email_message_id: string;
  tone?: ToneEnum;
  intent?: string;
}

export interface ReplyDraftUpdateRequest {
  subject?: string;
  body_text?: string;
  tone?: ToneEnum;
  intent?: string;
  status?: StatusEnum;
}
