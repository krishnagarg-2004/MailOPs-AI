import React, { useState } from 'react';
import { AIAnalysisResult, ActionStatusEnum, ExtractedActionItem } from '../types/ai';

interface EmailAnalysisCardProps {
  analysis: AIAnalysisResult;
  onActionStatusChange?: (actionId: string, newStatus: ActionStatusEnum) => void;
}

export const EmailAnalysisCard: React.FC<EmailAnalysisCardProps> = ({
  analysis,
  onActionStatusChange,
}) => {
  const [showEvidence, setShowEvidence] = useState(false);

  const getPriorityBadge = (p: string) => {
    switch (p) {
      case 'HIGH':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'LOW':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  const getIntentBadge = (intent: string) => {
    switch (intent) {
      case 'WORK_REQUEST':
      case 'URGENT_ACTION':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'FINANCIAL_INVOICE':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'CONTRACT_LEGAL':
        return 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4 font-sans text-slate-100">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">AI Intelligence</span>
          <span className={`text-xs px-2.5 py-0.5 rounded-full border ${getIntentBadge(analysis.intent)} font-medium`}>
            {analysis.intent.replace('_', ' ')}
          </span>
          <span className={`text-xs px-2 py-0.5 rounded border ${getPriorityBadge(analysis.priority)} font-medium`}>
            {analysis.priority}
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span>Confidence: <strong className="text-slate-200">{(analysis.confidence_score * 100).toFixed(0)}%</strong></span>
          <span>Model: <code className="text-slate-300 font-mono text-[11px]">{analysis.model_name}</code></span>
        </div>
      </div>

      {/* Executive Summary */}
      <div>
        <h4 className="text-sm font-semibold text-slate-200 mb-1">Executive Summary</h4>
        <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/50 p-3 rounded-lg border border-slate-800/60">
          {analysis.summary}
        </p>
      </div>

      {/* Evidence-Grounded Rationale */}
      <div>
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Rationale</h4>
        <p className="text-xs text-slate-400 italic">"{analysis.rationale}"</p>
      </div>

      {/* Extracted Actions & Intelligence Items */}
      {analysis.extracted_items && analysis.extracted_items.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-slate-200">Extracted Action Items ({analysis.extracted_items.length})</h4>
          <div className="space-y-2">
            {analysis.extracted_items.map((item: ExtractedActionItem) => (
              <div
                key={item.id}
                className="flex items-start justify-between gap-3 bg-slate-950/70 p-3 rounded-lg border border-slate-800/80 hover:border-slate-700 transition"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      {item.item_type}
                    </span>
                    <span className="text-xs font-medium text-slate-200">{item.description}</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400">
                    {item.assignee && <span>Assignee: <strong className="text-slate-300">{item.assignee}</strong></span>}
                    {item.due_date && <span>Due: <strong className="text-amber-400">{new Date(item.due_date).toLocaleDateString()}</strong></span>}
                    {!item.is_evidence_valid && (
                      <span className="text-red-400 bg-red-950/50 px-1.5 py-0.5 rounded border border-red-800/40" title="Evidence snippet not found verbatim in email text">
                        ⚠️ Invalid Evidence
                      </span>
                    )}
                  </div>
                </div>

                {/* Human-in-the-Loop Action Status Controls */}
                <div className="flex items-center gap-1.5">
                  {item.status === 'PENDING' ? (
                    <>
                      <button
                        onClick={() => onActionStatusChange && onActionStatusChange(item.id, 'CONFIRMED')}
                        className="text-[11px] px-2.5 py-1 rounded bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 border border-emerald-500/40 font-medium transition"
                      >
                        Confirm
                      </button>
                      <button
                        onClick={() => onActionStatusChange && onActionStatusChange(item.id, 'DISMISSED')}
                        className="text-[11px] px-2 py-1 rounded bg-slate-800 text-slate-400 hover:bg-slate-700 transition"
                      >
                        Dismiss
                      </button>
                    </>
                  ) : (
                    <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {item.status}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Provenance / Evidence Accordion */}
      <div className="pt-2 border-t border-slate-800/80">
        <button
          onClick={() => setShowEvidence(!showEvidence)}
          className="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-1 font-medium"
        >
          <span>{showEvidence ? '▼ Hide Evidence Snippets' : '▶ Show Explainability Evidence'}</span>
        </button>

        {showEvidence && (
          <div className="mt-2 space-y-2 text-xs bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-slate-300">
            {analysis.extracted_items.map((item, idx) => (
              <div key={idx} className="border-b border-slate-900 pb-2 last:border-0 last:pb-0">
                <span className="text-slate-400 font-sans block text-[11px] mb-0.5 font-semibold">
                  [{item.item_type}] {item.description}:
                </span>
                <p className="bg-slate-900 p-2 rounded text-emerald-300/90 text-[11px] italic">
                  "{item.evidence_snippet || 'No snippet provided'}"
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
