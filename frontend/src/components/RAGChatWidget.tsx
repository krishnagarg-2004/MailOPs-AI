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
  const [hasAsked, setHasAsked] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (question.trim() && onAskRAG) {
      setHasAsked(true);
      onAskRAG(question.trim());
    }
  };

  return (
    <div className="bg-zinc-950/90 border border-zinc-800/80 rounded-2xl p-5 shadow-xl space-y-4 text-zinc-100 font-sans">
      <div className="border-b border-zinc-800/80 pb-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-red-400 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
          Grounded RAG Assistant (pgvector + Citations)
        </h3>
        <p className="text-xs text-zinc-400 mt-0.5">
          Ask questions grounded strictly in your emails and extracted document text with source citations.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask e.g. What is the due date and total amount for the Acme invoice?"
          className="flex-1 bg-zinc-900/90 border border-zinc-800 rounded-xl px-4 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500/80 focus:ring-1 focus:ring-red-500/30 transition"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white text-xs px-4 py-2 rounded-xl font-medium transition disabled:opacity-50 shadow-md shadow-red-950/50 active:scale-95"
        >
          {isLoading ? 'Synthesizing...' : 'Ask AI'}
        </button>
      </form>

      {/* Answer & Citations Card */}
      {hasAsked && !isLoading && ragResponse && (
        <div className="bg-zinc-900/60 p-4 rounded-xl border border-red-800/60 space-y-3.5 animate-fadeIn shadow-inner">
          <div className="text-xs text-zinc-200 leading-relaxed font-sans">
            <span className="font-semibold text-red-400 block mb-1 uppercase tracking-wider text-[10px]">
              Grounded Synthesis:
            </span>
            <p className="bg-black/60 p-3.5 rounded-xl border border-zinc-800 text-zinc-100 leading-relaxed">
              {ragResponse.answer}
            </p>
          </div>

          {/* Citations List */}
          {ragResponse.citations.length > 0 && (
            <div className="pt-2 border-t border-zinc-800/80 space-y-2">
              <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider block">
                Source Citations ({ragResponse.citations.length})
              </span>
              <div className="flex flex-wrap gap-2">
                {ragResponse.citations.map((cit, idx) => (
                  <span
                    key={idx}
                    className="text-[11px] bg-zinc-950 border border-zinc-800 px-3 py-1 rounded-lg text-zinc-300 flex items-center gap-1.5"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                    <strong className="text-zinc-200">{cit.source_name}</strong>
                    {cit.page_number && <span className="text-zinc-400 font-mono">(Page {cit.page_number})</span>}
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
