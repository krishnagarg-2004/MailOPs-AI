import { AIAnalysisResult, ActionStatusEnum } from '../types/ai';
import { BusinessDocumentExtractionResult, DocumentExtractionResult } from '../types/document';
import { DependencyChainResponse, GraphNetworkResponse } from '../types/graph';
import { ReplyDraftResult, ReplyDraftUpdateRequest, ToneEnum } from '../types/reply_draft';
import { RAGQueryResponse, SearchResultItem } from '../types/search';


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
      errorMessage = parsed.detail || parsed.message || errorMessage;
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
    return fetchJSON<SearchResultItem[]>(`${endpoint}?q=${encodeURIComponent(query)}`);
  },
  queryRAG: (question: string) =>
    fetchJSON<RAGQueryResponse>('/api/v1/search/rag-query', {
      method: 'POST',
      body: JSON.stringify({ question }),
    }),

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
};
