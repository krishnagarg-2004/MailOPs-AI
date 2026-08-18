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
      setIsRAGLoading(true);
      const res = await api.queryRAG(question);
      setRagResponse(res);
    } catch (err: any) {
      alert(`RAG Synthesis Error: ${err.message}`);
    } finally {
      setIsRAGLoading(false);
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-lg font-bold text-slate-100">Semantic Search & Grounded RAG Assistant</h2>
        <p className="text-xs text-slate-400">
          Query indexed email messages and attachments with 768-d pgvector cosine similarity and grounded citation synthesis.
        </p>
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
