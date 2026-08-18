export type IntentEnum =
  | 'WORK_REQUEST'
  | 'STATUS_UPDATE'
  | 'FINANCIAL_INVOICE'
  | 'CONTRACT_LEGAL'
  | 'URGENT_ACTION'
  | 'INFORMATIONAL'
  | 'OTHER';

export type PriorityEnum = 'HIGH' | 'MEDIUM' | 'LOW';

export type SentimentEnum = 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE';

export type ItemTypeEnum = 'ACTION' | 'DECISION' | 'RISK';

export type ActionStatusEnum = 'PENDING' | 'CONFIRMED' | 'DISMISSED' | 'COMPLETED';

export interface ExtractedActionItem {
  id: string;
  user_id: string;
  ai_analysis_id: string;
  email_message_id?: string;
  email_thread_id?: string;
  item_type: ItemTypeEnum;
  description: string;
  assignee?: string;
  due_date?: string;
  severity_or_priority: PriorityEnum;
  confidence_score: number;
  evidence_snippet: string;
  is_evidence_valid: boolean;
  status: ActionStatusEnum;
  created_at: string;
  updated_at: string;
}

export interface AIAnalysisResult {
  id: string;
  user_id: string;
  email_message_id?: string;
  email_thread_id?: string;
  summary: string;
  intent: IntentEnum;
  priority: PriorityEnum;
  sentiment: SentimentEnum;
  confidence_score: number;
  rationale: string;
  model_name: string;
  prompt_version: string;
  status: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  extracted_items: ExtractedActionItem[];
}
