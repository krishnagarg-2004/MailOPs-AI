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
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-4 gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-100">Semantic Search & Grounded RAG Assistant</h2>
          <p className="text-xs text-slate-400">
            Query indexed email messages and attachments with 768-d pgvector cosine similarity and grounded citation synthesis.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReindex}
            disabled={isIndexing}
            className="flex items-center gap-1.5 bg-gradient-to-r from-purple-600/30 to-indigo-600/30 hover:from-purple-600/50 hover:to-indigo-600/50 text-purple-300 border border-purple-500/40 text-xs px-3 py-1.5 rounded-lg transition font-medium disabled:opacity-50"
          >
            <span>{isIndexing ? '⏳ Indexing Mailbox...' : '⚡ Re-Index Mailbox (pgvector)'}</span>
          </button>
        </div>
      </div>

      {indexMessage && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs px-4 py-2.5 rounded-xl flex items-center justify-between">
          <span>✅ {indexMessage}</span>
          <button onClick={() => setIndexMessage(null)} className="text-slate-400 hover:text-slate-200">✕</button>
        </div>
      )}

      {/* Suggested Query Chips */}
      <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl flex flex-wrap items-center gap-2 text-xs">
        <span className="text-slate-400 font-semibold mr-1">Suggested Questions:</span>
        {sampleQueries.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleAskRAG(q)}
            className="bg-slate-950 hover:bg-slate-800 text-slate-300 hover:text-purple-300 border border-slate-800 hover:border-purple-500/30 px-2.5 py-1 rounded-lg transition text-[11px]"
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
