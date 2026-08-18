import React, { useState } from 'react';
import { RAGQueryResponse } from '../types/search';

interface RAGChatWidgetProps {
  onAskRAG?: (question: string) => void;
  ragResponse?: RAGQueryResponse;
  isLoading?: boolean;
}

export const RAGChatWidget: React.FC<RAGChatWidgetProps> = ({
  onAskRAG,
  ragResponse,
  isLoading = false,
}) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && onAskRAG) {
      onAskRAG(question.trim());
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4 text-slate-100 font-sans">
      <div className="border-b border-slate-800 pb-3">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-purple-400">
          Grounded RAG Assistant (pgvector + Citations)
        </h3>
        <p className="text-xs text-slate-400 mt-0.5">
          Ask questions grounded strictly in your emails and extracted document text with source citations.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask e.g. What is the due date and total amount for the Acme invoice?"
          className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs px-4 py-2 rounded-lg font-medium transition disabled:opacity-50"
        >
          {isLoading ? 'Synthesizing...' : 'Ask AI'}
        </button>
      </form>

      {/* Answer & Citations Card */}
      {ragResponse && (
        <div className="bg-slate-950 p-4 rounded-xl border border-purple-500/30 space-y-3">
          <div className="text-xs text-slate-200 leading-relaxed font-sans">
            <span className="font-semibold text-purple-400 block mb-1">Grounded Answer:</span>
            {ragResponse.answer}
          </div>

          {/* Citations List */}
          {ragResponse.citations.length > 0 && (
            <div className="pt-2 border-t border-slate-900 space-y-1.5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Source Citations ({ragResponse.citations.length})
              </span>
              <div className="flex flex-wrap gap-2">
                {ragResponse.citations.map((cit, idx) => (
                  <span
                    key={idx}
                    className="text-[11px] bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-md text-slate-300 flex items-center gap-1.5"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                    <strong>{cit.source_name}</strong>
                    {cit.page_number && <span className="text-slate-400">(Page {cit.page_number})</span>}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
