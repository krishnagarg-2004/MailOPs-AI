import React, { useState } from 'react';
import { RAGChatWidget } from '../components/RAGChatWidget';
import { SemanticSearchWidget } from '../components/SemanticSearchWidget';
import { api } from '../services/api';
import { RAGQueryResponse, SearchResultItem } from '../types/search';

export const SearchRAGView: React.FC = () => {
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);

  const [ragResponse, setRagResponse] = useState<RAGQueryResponse | undefined>(undefined);
  const [isRAGLoading, setIsRAGLoading] = useState<boolean>(false);
  const [isIndexing, setIsIndexing] = useState<boolean>(false);
  const [indexMessage, setIndexMessage] = useState<string | null>(null);

  const handleSearch = async (query: string, mode: 'semantic' | 'hybrid') => {
    try {
      setIsSearching(true);
      const results = await api.searchSemantic(query, mode);
      setSearchResults(results);
    } catch (err: any) {
      alert(`Search Error: ${err.message}`);
    } finally {
      setIsSearching(false);
    }
  };

  const handleAskRAG = async (question: string) => {
    try {
      setRagResponse(undefined);
      setIsRAGLoading(true);

      const res = await api.queryRAG(question);
      setRagResponse(res);
    } catch (err: any) {
      alert(`RAG Synthesis Error: ${err.message}`);
    } finally {
      setIsRAGLoading(false);
    }
  };

  const handleReindex = async () => {
    try {
      setIsIndexing(true);
      setIndexMessage(null);
      const res = await api.reindexAll();
      setIndexMessage(`Indexed ${res.indexed_emails} emails & ${res.indexed_documents} documents (${res.total_chunks} vector chunks).`);
    } catch (err: any) {
      alert(`Indexing Error: ${err.message}`);
    } finally {
      setIsIndexing(false);
    }
  };

  const sampleQueries = [
    'What workflow run or CI/CD failures occurred?',
    'Are there any pending invoice payments or due dates?',
    'What are the urgent action items and blockers?',
    'Summarize recent conversations and next steps',
  ];

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-wrap items-center justify-between border-b border-zinc-800 pb-4 gap-3">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span>Semantic Search & Grounded RAG Assistant</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950/60 text-red-400 border border-red-800/60 font-semibold uppercase">pgvector</span>
          </h2>
          <p className="text-xs text-zinc-400">
            Query indexed email messages and attachments with 768-d pgvector cosine similarity and grounded citation synthesis.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReindex}
            disabled={isIndexing}
            className="flex items-center gap-1.5 bg-red-950/40 hover:bg-red-900/60 text-red-300 border border-red-800/60 hover:border-red-600 text-xs px-3 py-1.5 rounded-lg transition font-medium disabled:opacity-50 shadow-sm"
          >
            <span>{isIndexing ? '⏳ Indexing Mailbox...' : '⚡ Re-Index Mailbox (pgvector)'}</span>
          </button>
        </div>
      </div>

      {indexMessage && (
        <div className="bg-red-950/30 border border-red-800/50 text-red-300 text-xs px-4 py-2.5 rounded-xl flex items-center justify-between">
          <span>✅ {indexMessage}</span>
          <button onClick={() => setIndexMessage(null)} className="text-zinc-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Suggested Query Chips */}
      <div className="bg-zinc-950 border border-zinc-800 p-3 rounded-xl flex flex-wrap items-center gap-2 text-xs">
        <span className="text-zinc-400 font-semibold mr-1">Suggested Questions:</span>
        {sampleQueries.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleAskRAG(q)}
            className="bg-zinc-900 hover:bg-zinc-850 text-zinc-300 hover:text-red-400 border border-zinc-800 hover:border-red-900/60 px-2.5 py-1 rounded-lg transition text-[11px]"
          >
            💬 {q}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Semantic & Hybrid Search Widget */}
        <SemanticSearchWidget
          onSearch={handleSearch}
          results={searchResults}
          isLoading={isSearching}
        />

        {/* Right Column: Grounded RAG Chat Widget */}
        <RAGChatWidget
          onAskRAG={handleAskRAG}
          ragResponse={ragResponse}
          isLoading={isRAGLoading}
        />
      </div>
    </div>
  );
};
