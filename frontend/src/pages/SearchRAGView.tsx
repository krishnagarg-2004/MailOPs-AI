import React, { useState } from 'react';
import { RefreshCw, MessageSquare, CheckCircle2, X } from 'lucide-react';
import { RAGChatWidget } from '../components/RAGChatWidget';
import { SemanticSearchWidget } from '../components/SemanticSearchWidget';
import { useToast } from '../context/ToastContext';
import { api } from '../services/api';
import { RAGQueryResponse, SearchResultItem } from '../types/search';

export const SearchRAGView: React.FC = () => {
  const { toast } = useToast();
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
      toast.error(`Search Error: ${err.message}`);
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
      toast.error(`RAG Synthesis Error: ${err.message}`);
    } finally {
      setIsRAGLoading(false);
    }
  };

  const handleReindex = async () => {
    try {
      setIsIndexing(true);
      setIndexMessage(null);
      const res = await api.reindexAll();
      const successMsg = `Indexed ${res.indexed_emails} emails & ${res.indexed_documents} documents (${res.total_chunks} vector chunks).`;
      setIndexMessage(successMsg);
      toast.success(successMsg);
    } catch (err: any) {
      toast.error(`Indexing Error: ${err.message}`);
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
    <div className="space-y-5 font-sans">
      <div className="flex flex-wrap items-center justify-between border-b border-white/[0.06] pb-3.5 gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2 tracking-tight">
            <span>Semantic Search & Grounded RAG Assistant</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.04] text-zinc-400 border border-white/[0.08] tracking-wider">
              pgvector 768-d
            </span>
          </h2>
          <p className="text-xs text-zinc-500 mt-0.5">
            Query indexed email messages and attachments with pgvector cosine similarity and grounded citation synthesis.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReindex}
            disabled={isIndexing}
            className="flex items-center gap-1.5 bg-white/[0.04] hover:bg-white/[0.08] text-zinc-200 border border-white/[0.08] hover:border-white/[0.14] text-xs px-3 py-1.5 rounded-lg transition font-medium disabled:opacity-50 shadow-sm active:scale-95"
          >
            <RefreshCw className={`w-3 h-3 text-red-400 ${isIndexing ? 'animate-spin' : ''}`} />
            <span>{isIndexing ? 'Indexing...' : 'Re-Index Mailbox (pgvector)'}</span>
          </button>
        </div>
      </div>

      {indexMessage && (
        <div className="bg-[#121216] border border-emerald-500/30 text-emerald-300 text-xs px-3.5 py-2.5 rounded-xl flex items-center justify-between shadow-sm animate-fadeIn">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>{indexMessage}</span>
          </div>
          <button onClick={() => setIndexMessage(null)} className="text-zinc-500 hover:text-white p-1">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Suggested Query Chips */}
      <div className="bg-[#0e0e12] border border-white/[0.07] p-3 rounded-xl flex flex-wrap items-center gap-1.5 text-xs shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]">
        <span className="text-zinc-500 text-[10px] font-medium uppercase tracking-wider mr-1">Suggested:</span>
        {sampleQueries.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleAskRAG(q)}
            className="bg-[#121216] hover:bg-[#16161c] text-zinc-300 hover:text-white border border-white/[0.06] hover:border-white/[0.12] px-2.5 py-1 rounded-md transition text-[11px] font-medium active:scale-95 flex items-center gap-1.5"
          >
            <MessageSquare className="w-3 h-3 text-zinc-500" />
            <span>{q}</span>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
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
