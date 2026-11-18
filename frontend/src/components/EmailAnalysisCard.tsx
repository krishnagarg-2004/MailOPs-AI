import React, { useState } from 'react';
import { useToast } from '../context/ToastContext';
import { AIAnalysisResult, ActionStatusEnum, ExtractedActionItem } from '../types/ai';
import { api } from '../services/api';

interface EmailAnalysisCardProps {
  analysis: AIAnalysisResult;
  onActionStatusChange?: (actionId: string, newStatus: ActionStatusEnum) => void;
}

export const EmailAnalysisCard: React.FC<EmailAnalysisCardProps> = ({
  analysis,
  onActionStatusChange,
}) => {
  const { toast } = useToast();
  const [showEvidence, setShowEvidence] = useState(false);
  const [showExplainability, setShowExplainability] = useState(false);
  const [schedulingId, setSchedulingId] = useState<string | null>(null);
  const [scheduledLinks, setScheduledLinks] = useState<Record<string, string>>({});

  const handleScheduleAction = async (item: ExtractedActionItem) => {
    try {
      setSchedulingId(item.id);
      const res = await api.scheduleActionItem(item.id, `[MailOps] ${item.description}`);
      setScheduledLinks((prev) => ({ ...prev, [item.id]: res.calendar_url }));
      if (onActionStatusChange) {
        onActionStatusChange(item.id, 'CONFIRMED');
      }
      toast.success('Action item successfully scheduled on Google Calendar!');
    } catch (err: any) {
      toast.error(`Scheduling error: ${err.message}`);
    } finally {
      setSchedulingId(null);
    }
  };

  const getPriorityBadge = (p: string) => {
    switch (p) {
      case 'HIGH':
        return 'bg-red-950/70 text-rose-400 border-red-800/80 font-bold';
      case 'MEDIUM':
        return 'bg-zinc-800/80 text-zinc-300 border-zinc-700/80';
      case 'LOW':
        return 'bg-zinc-900 text-zinc-400 border-zinc-800';
      default:
        return 'bg-zinc-800 text-zinc-400 border-zinc-700';
    }
  };

  const getIntentBadge = (intent: string) => {
    switch (intent) {
      case 'WORK_REQUEST':
      case 'URGENT_ACTION':
        return 'bg-red-950/70 text-red-400 border-red-800/80 font-semibold';
      case 'FINANCIAL_INVOICE':
        return 'bg-zinc-900 text-zinc-200 border-zinc-700 font-medium';
      case 'CONTRACT_LEGAL':
        return 'bg-zinc-900 text-zinc-200 border-zinc-700 font-medium';
      default:
        return 'bg-zinc-900 text-zinc-400 border-zinc-800';
    }
  };

  const getConfidenceLevel = (score: number) => {
    if (score >= 0.9) return { label: 'High Confidence', color: 'text-red-400', bg: 'bg-red-950/50 border-red-800/60' };
    if (score >= 0.75) return { label: 'Moderate Confidence', color: 'text-zinc-300', bg: 'bg-zinc-900 border-zinc-700' };
    return { label: 'Review Suggested', color: 'text-zinc-400', bg: 'bg-zinc-900 border-zinc-800' };
  };

  const conf = getConfidenceLevel(analysis.confidence_score);

  return (
    <div className="bg-zinc-950/90 border border-zinc-800/80 rounded-2xl p-4 shadow-xl space-y-4 font-sans text-zinc-100 overflow-hidden break-words">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-800/80 pb-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 mr-1">AI Intelligence</span>
          <span className={`text-[11px] px-2.5 py-0.5 rounded-full border ${getIntentBadge(analysis.intent)}`}>
            {analysis.intent.replace('_', ' ')}
          </span>
          <span className={`text-[11px] px-2.5 py-0.5 rounded-full border ${getPriorityBadge(analysis.priority)}`}>
            {analysis.priority}
          </span>
          {analysis.sentiment && (
            <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-zinc-900 text-zinc-300 border border-zinc-800 font-medium">
              {analysis.sentiment === 'NEGATIVE' ? '⚠️ Negative' : analysis.sentiment === 'POSITIVE' ? '✅ Positive' : '⚖️ Neutral'}
            </span>
          )}
        </div>

        {/* Visual Confidence Gauge */}
        <div className="flex items-center gap-2 text-xs shrink-0">
          <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border ${conf.bg}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${analysis.confidence_score >= 0.9 ? 'bg-red-500' : 'bg-zinc-500'} animate-pulse`} />
            <span className={`font-bold text-xs ${conf.color} font-mono`}>
              {(analysis.confidence_score * 100).toFixed(0)}%
            </span>
            <span className="text-zinc-400 text-[10px]">({conf.label})</span>
          </div>
          <button
            onClick={() => setShowExplainability(!showExplainability)}
            className="text-[11px] text-red-400 hover:text-red-300 underline transition font-medium"
          >
            {showExplainability ? 'Hide Details' : 'Details'}
          </button>
        </div>
      </div>

      {/* AI Explainability & Verification Drawer */}
      {showExplainability && (
        <div className="bg-zinc-900/80 p-3.5 rounded-xl border border-red-800/60 space-y-2 text-xs animate-fadeIn">
          <div className="flex items-center justify-between text-red-400 font-semibold border-b border-zinc-800/80 pb-1.5">
            <span>Model Explainability Breakdown</span>
            <code className="text-[10px] text-zinc-400 font-mono">{analysis.model_name} (v{analysis.prompt_version})</code>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-zinc-300 pt-1">
            <div>
              <strong className="text-zinc-400 block mb-0.5">Intent Reasoning:</strong>
              <span>Classified as <code className="text-zinc-200">{analysis.intent}</code> based on explicit operational requests in text.</span>
            </div>
            <div>
              <strong className="text-zinc-400 block mb-0.5">Priority Calculation:</strong>
              <span>Weighted as <code className="text-zinc-200">{analysis.priority}</code> based on detected deadlines and SLA commitments.</span>
            </div>
          </div>
        </div>
      )}

      {/* Executive Summary */}
      <div>
        <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
          Executive Summary
        </h4>
        <p className="text-xs text-zinc-200 leading-relaxed bg-zinc-900/50 border-l-2 border-l-red-500 p-3.5 rounded-r-xl border-y border-r border-zinc-800/80 shadow-inner">
          {analysis.summary}
        </p>
      </div>

      {/* Evidence-Grounded Rationale */}
      <div>
        <h4 className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider mb-1">Rationale</h4>
        <p className="text-xs text-zinc-400 italic">"{analysis.rationale}"</p>
      </div>

      {/* Extracted Actions & Intelligence Items */}
      {analysis.extracted_items && analysis.extracted_items.length > 0 && (
        <div className="space-y-2.5">
          <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
            Extracted Action Items ({analysis.extracted_items.length})
          </h4>
          <div className="space-y-2">
            {analysis.extracted_items.map((item: ExtractedActionItem) => (
              <div
                key={item.id}
                className="flex items-start justify-between gap-3 bg-zinc-900/60 p-3 rounded-xl border border-zinc-800/80 hover:border-zinc-700 transition"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-zinc-800 text-red-400 border border-zinc-700/60">
                      {item.item_type}
                    </span>
                    <span className="text-xs font-medium text-white truncate">{item.description}</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-zinc-400">
                    {item.assignee && <span>Assignee: <strong className="text-zinc-200">{item.assignee}</strong></span>}
                    {item.due_date && <span>Due: <strong className="text-red-400 font-mono">{new Date(item.due_date).toLocaleDateString()}</strong></span>}
                    {!item.is_evidence_valid && (
                      <span className="text-rose-400 bg-red-950/50 px-1.5 py-0.5 rounded border border-red-800/40 text-[10px]" title="Evidence snippet not found verbatim in email text">
                        ⚠️ Invalid Evidence
                      </span>
                    )}
                  </div>
                </div>

                {/* Human-in-the-Loop Action Status Controls */}
                <div className="flex items-center gap-1.5 shrink-0">
                  {/* Google Calendar 1-Click Sync Button */}
                  {scheduledLinks[item.id] ? (
                    <a
                      href={scheduledLinks[item.id]}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] px-2.5 py-1 rounded-lg bg-zinc-800 text-red-400 border border-zinc-700 font-medium hover:bg-zinc-700 transition flex items-center gap-1"
                      title="Open in Google Calendar"
                    >
                      <span>📅</span> View GCal
                    </a>
                  ) : (
                    <button
                      onClick={() => handleScheduleAction(item)}
                      disabled={schedulingId === item.id}
                      className="text-[11px] px-2.5 py-1 rounded-lg bg-red-950/50 text-red-400 hover:bg-red-900/60 border border-red-800/60 font-medium transition flex items-center gap-1 disabled:opacity-50 active:scale-95"
                      title="Schedule Deadline into Google Calendar"
                    >
                      <span>📅</span> {schedulingId === item.id ? 'Syncing...' : 'Sync GCal'}
                    </button>
                  )}

                  {item.status === 'PENDING' ? (
                    <>
                      <button
                        onClick={() => onActionStatusChange && onActionStatusChange(item.id, 'CONFIRMED')}
                        className="text-[11px] px-2.5 py-1 rounded-lg bg-zinc-800/80 text-zinc-200 hover:bg-zinc-700 border border-zinc-700 font-medium transition active:scale-95"
                      >
                        Confirm
                      </button>
                      <button
                        onClick={() => onActionStatusChange && onActionStatusChange(item.id, 'COMPLETED')}
                        className="text-[11px] px-2.5 py-1 rounded-lg bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-medium shadow-sm transition active:scale-95"
                        title="Mark Complete"
                      >
                        Complete
                      </button>
                      <button
                        onClick={() => onActionStatusChange && onActionStatusChange(item.id, 'DISMISSED')}
                        className="text-[11px] px-2 py-1 rounded-lg bg-zinc-900 text-zinc-400 hover:text-white border border-zinc-800 font-medium transition active:scale-95"
                      >
                        Dismiss
                      </button>
                    </>
                  ) : (
                    <span className="text-[10px] px-2.5 py-0.5 rounded-full font-mono font-medium border bg-zinc-800 text-zinc-300 border-zinc-700">
                      {item.status}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Supporting Evidence Drawer Toggle */}
      {analysis.extracted_items && analysis.extracted_items.some((i) => i.evidence_snippet) && (
        <div className="border-t border-zinc-800/80 pt-3">
          <button
            onClick={() => setShowEvidence(!showEvidence)}
            className="text-xs text-red-400 hover:text-red-300 font-medium flex items-center gap-1.5 transition"
          >
            <span>{showEvidence ? '▼ Hide' : '▶ Show'} Grounding Evidence Snippets</span>
          </button>
          {showEvidence && (
            <div className="mt-2.5 space-y-2.5 bg-zinc-900/60 p-3.5 rounded-xl border border-zinc-800/80 text-xs animate-fadeIn">
              {analysis.extracted_items.map((item: ExtractedActionItem) =>
                item.evidence_snippet ? (
                  <div key={`ev-${item.id}`} className="space-y-1 border-b border-zinc-800/60 pb-2 last:border-b-0 last:pb-0">
                    <span className="text-[11px] font-semibold text-zinc-300">{item.description}:</span>
                    <blockquote className="text-zinc-400 italic border-l-2 border-red-500 pl-2.5 text-xs">
                      "{item.evidence_snippet}"
                    </blockquote>
                  </div>
                ) : null
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
