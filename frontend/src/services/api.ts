import { AIAnalysisResult, ActionStatusEnum } from '../types/ai';
import { BusinessDocumentExtractionResult, DocumentExtractionResult } from '../types/document';
import { DependencyChainResponse, GraphNetworkResponse } from '../types/graph';
import { ReplyDraftResult, ReplyDraftUpdateRequest, ToneEnum } from '../types/reply_draft';
import { RAGQueryResponse, SearchResultItem } from '../types/search';


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

async function fetchJSON<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.headers,
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `HTTP ${response.status} Error`;
    try {
      const parsed = JSON.parse(errorText);
      const detail = parsed.detail ?? parsed.message;
      if (typeof detail === 'string') {
        errorMessage = detail;
      } else if (Array.isArray(detail)) {
        errorMessage = detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
      } else if (detail && typeof detail === 'object') {
        errorMessage = JSON.stringify(detail);
      } else {
        errorMessage = errorText || errorMessage;
      }
    } catch {
      errorMessage = errorText || errorMessage;
    }
    const err = new Error(errorMessage) as any;
    err.status = response.status;
    throw err;
  }

  return response.json() as Promise<T>;
}

// --- Gmail API ---
export interface EmailMessageSummary {
  id: string;
  thread_id: string;
  gmail_message_id: string;
  sender?: string;
  subject?: string;
  snippet?: string;
  body_plain?: string;
  date_received?: string;
  has_attachments: boolean;
  attachments?: Array<{ id: string; filename: string; mime_type: string; size_bytes: number }>;
}

export interface EmailThreadSummary {
  id: string;
  gmail_thread_id: string;
  snippet?: string;
  messages: EmailMessageSummary[];
}

export const api = {
  // Gmail & Threads
  getGmailThreads: () => fetchJSON<EmailThreadSummary[]>('/api/v1/gmail/threads'),
  getGmailThread: (id: string) => fetchJSON<EmailThreadSummary>(`/api/v1/gmail/threads/${id}`),
  getGmailMessage: (id: string) => fetchJSON<EmailMessageSummary>(`/api/v1/gmail/messages/${id}`),

  // AI Intelligence
  analyzeMessage: (messageId: string) =>
    fetchJSON<AIAnalysisResult>(`/api/v1/ai/analyze/message/${messageId}`, { method: 'POST' }),
  getMessageAnalysis: (messageId: string) =>
    fetchJSON<AIAnalysisResult>(`/api/v1/ai/analysis/message/${messageId}`),
  updateActionStatus: (actionId: string, status: ActionStatusEnum) =>
    fetchJSON<any>(`/api/v1/ai/actions/${actionId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        status,
      }),
    }),


  // Document Intelligence
  processDocument: (attachmentId: string) =>
    fetchJSON<DocumentExtractionResult>(`/api/v1/documents/process/${attachmentId}`, { method: 'POST' }),
  getDocumentExtraction: (attachmentId: string) =>
    fetchJSON<DocumentExtractionResult>(`/api/v1/documents/extraction/${attachmentId}`),
  analyzeBusinessDocument: (attachmentId: string) =>
    fetchJSON<BusinessDocumentExtractionResult>(`/api/v1/documents/analyze-business-doc/${attachmentId}`, { method: 'POST' }),
  getBusinessDocumentExtraction: (attachmentId: string) =>
    fetchJSON<BusinessDocumentExtractionResult>(`/api/v1/documents/business-doc/${attachmentId}`),

  // Search & RAG
  searchSemantic: (query: string, mode: 'semantic' | 'hybrid') => {
    const endpoint = mode === 'hybrid' ? '/api/v1/search/hybrid' : '/api/v1/search/semantic';
    return fetchJSON<SearchResultItem[]>(endpoint, {
      method: 'POST',
      body: JSON.stringify({ query, top_k: 5 }),
    });
  },
  queryRAG: (question: string) =>
    fetchJSON<RAGQueryResponse>('/api/v1/search/rag-query', {
      method: 'POST',
      body: JSON.stringify({ query: question, question }),
    }),
  reindexAll: () =>
    fetchJSON<{ indexed_emails: number; indexed_documents: number; total_chunks: number }>(
      '/api/v1/search/reindex',
      { method: 'POST' }
    ),

  // Action Graph
  getGraphVisual: () => fetchJSON<GraphNetworkResponse>('/api/v1/graph/visual'),
  rebuildGraph: () => fetchJSON<{ status: string; message: string }>('/api/v1/graph/rebuild', { method: 'POST' }),
  getGraphDependencies: (actionId: string) => fetchJSON<DependencyChainResponse>(`/api/v1/graph/dependencies/${actionId}`),

  // Human-in-the-Loop Reply Drafts
  getReplyDraftsForMessage: (messageId: string) =>
    fetchJSON<ReplyDraftResult[]>(`/api/v1/reply-drafts/message/${messageId}`),
  generateReplyDraft: (messageId: string, tone: ToneEnum = 'PROFESSIONAL', intent: string = 'REPLY_RESPONSE') =>
    fetchJSON<ReplyDraftResult>('/api/v1/reply-drafts/generate', {
      method: 'POST',
      body: JSON.stringify({ email_message_id: messageId, tone, intent }),
    }),
  updateReplyDraft: (draftId: string, payload: ReplyDraftUpdateRequest) =>
    fetchJSON<ReplyDraftResult>(`/api/v1/reply-drafts/${draftId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  syncGmailDraft: (draftId: string) =>
    fetchJSON<ReplyDraftResult>(`/api/v1/reply-drafts/${draftId}/sync-gmail`, { method: 'POST' }),
  sendReplyEmail: (draftId: string) =>
    fetchJSON<ReplyDraftResult>(`/api/v1/reply-drafts/${draftId}/send`, { method: 'POST' }),
  discardReplyDraft: (draftId: string) =>
    fetchJSON<{ id: string; status: string }>(`/api/v1/reply-drafts/${draftId}`, { method: 'DELETE' }),

  // Calendar Scheduling
  scheduleActionItem: (actionId: string, calendarTitle?: string) =>
    fetchJSON<{
      status: string;
      event_id: string;
      action_id: string;
      title: string;
      start_time: string;
      end_time: string;
      calendar_url: string;
      message: string;
    }>('/api/v1/calendar/schedule', {
      method: 'POST',
      body: JSON.stringify({ action_id: actionId, calendar_title: calendarTitle }),
    }),

  // Executive Digest & Reporting
  getExecutiveDigest: () =>
    fetchJSON<{
      generated_at: string;
      user_email: string;
      total_emails_analyzed: number;
      total_actions: number;
      pending_actions: number;
      confirmed_actions: number;
      completed_actions: number;
      total_risks: number;
      high_severity_risks: number;
      total_decisions: number;
      total_financial_value: number;
      top_actions: Array<any>;
      active_risks: Array<any>;
      recent_decisions: Array<any>;
    }>('/api/v1/digest/summary'),

  downloadDigestExport: async (format: 'csv' | 'markdown' | 'json' = 'csv') => {
    const res = await fetch(`${API_BASE_URL}/api/v1/digest/export?format=${format}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error(`Export download failed: ${res.statusText}`);
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mailops-executive-digest.${format === 'markdown' ? 'md' : format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  },

  // Demo Environment
  seedDemoData: () =>
    fetchJSON<{ status: string; message: string; details: any }>('/api/v1/auth/seed-demo', {
      method: 'POST',
    }),
};
