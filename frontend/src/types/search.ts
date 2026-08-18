export interface SearchResultItem {
  id: string;
  source_type: 'EMAIL' | 'DOCUMENT';
  source_name: string;
  email_message_id?: string;
  attachment_id?: string;
  page_number?: number;
  chunk_text: string;
  similarity_score: number;
}

export interface CitationItem {
  source_type: string;
  source_name: string;
  email_message_id?: string;
  attachment_id?: string;
  page_number?: number;
  similarity_score: number;
}

export interface RAGQueryResponse {
  answer: string;
  citations: CitationItem[];
  retrieved_chunks: SearchResultItem[];
}
