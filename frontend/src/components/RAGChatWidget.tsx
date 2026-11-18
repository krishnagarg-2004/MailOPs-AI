import React, { useState } from 'react';
import { Sparkles, Send, FileText } from 'lucide-react';
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
    <div className="bg-[#0e0e12] border border-white/[0.07] rounded-xl p-4 sm:p-5 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)] space-y-3.5 text-[#ededed] font-sans">
      <div className="border-b border-white/[0.06] pb-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-white flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-red-400" />
          Grounded RAG Assistant
        </h3>
        <p className="text-xs text-zinc-500 mt-0.5">
          Ask questions grounded strictly in your emails and extracted document text with source citations.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask e.g. What is the due date and total amount for the Acme invoice?"
          className="flex-1 bg-[#0a0a0d] border border-white/[0.07] rounded-lg px-3.5 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500/60 transition"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white text-xs px-4 py-2 rounded-lg font-medium transition disabled:opacity-50 shadow-sm active:scale-95 flex items-center gap-1.5"
        >
          {isLoading ? (
            <span>Synthesizing...</span>
          ) : (
            <>
              <Send className="w-3 h-3" />
              <span>Ask AI</span>
            </>
          )}
        </button>
      </form>

      {/* Answer & Citations Card */}
      {hasAsked && !isLoading && ragResponse && (
        <div className="bg-[#0a0a0d] p-3.5 rounded-lg border border-white/[0.07] space-y-3 animate-fadeIn">
          <div className="text-xs text-zinc-200 leading-relaxed font-sans">
            <span className="font-semibold text-red-400 block mb-1 uppercase tracking-wider text-[10px]">
              Grounded Synthesis:
            </span>
            <p className="bg-[#121216] p-3 rounded-lg border border-white/[0.05] text-zinc-200 leading-relaxed">
              {ragResponse.answer}
            </p>
          </div>

          {/* Citations List */}
          {ragResponse.citations.length > 0 && (
            <div className="pt-2 border-t border-white/[0.05] space-y-1.5">
              <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block">
                Source Citations ({ragResponse.citations.length})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {ragResponse.citations.map((cit, idx) => (
                  <span
                    key={idx}
                    className="text-[11px] bg-[#121216] border border-white/[0.06] px-2.5 py-1 rounded-md text-zinc-300 flex items-center gap-1.5 font-mono"
                  >
                    <FileText className="w-3 h-3 text-red-400" />
                    <strong className="text-zinc-200">{cit.source_name}</strong>
                    {cit.page_number && <span className="text-zinc-500">(p. {cit.page_number})</span>}
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
