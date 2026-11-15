import React, { useState } from 'react';
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
    } catch (err: any) {
      alert(`Scheduling error: ${err.message}`);
    } finally {
      setSchedulingId(null);
    }
  };

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

  const getConfidenceLevel = (score: number) => {
    if (score >= 0.9) return { label: 'High Confidence', color: 'text-emerald-400', bg: 'bg-emerald-500/20 border-emerald-500/30' };
    if (score >= 0.75) return { label: 'Moderate Confidence', color: 'text-amber-400', bg: 'bg-amber-500/20 border-amber-500/30' };
    return { label: 'Review Suggested', color: 'text-rose-400', bg: 'bg-rose-500/20 border-rose-500/30' };
  };

  const conf = getConfidenceLevel(analysis.confidence_score);

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
          {analysis.sentiment && (
            <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono">
              {analysis.sentiment === 'NEGATIVE' ? '⚠️ Negative' : analysis.sentiment === 'POSITIVE' ? '✅ Positive' : '⚖️ Neutral'}
            </span>
          )}
        </div>

        {/* Visual Confidence Gauge Pill */}
        <div className="flex items-center gap-2 text-xs">
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${conf.bg}`}>
            <span className={`w-2 h-2 rounded-full ${analysis.confidence_score >= 0.9 ? 'bg-emerald-400' : analysis.confidence_score >= 0.75 ? 'bg-amber-400' : 'bg-rose-400'} animate-pulse`} />
            <span className={`font-semibold ${conf.color}`}>
              {(analysis.confidence_score * 100).toFixed(0)}%
            </span>
            <span className="text-slate-400 text-[10px]">({conf.label})</span>
          </div>
          <button
            onClick={() => setShowExplainability(!showExplainability)}
            className="text-[11px] text-indigo-400 hover:text-indigo-300 underline transition ml-1"
          >
            {showExplainability ? 'Hide Explainability' : 'Explainability'}
          </button>
        </div>
      </div>

      {/* AI Explainability & Verification Drawer */}
      {showExplainability && (
        <div className="bg-slate-950 p-3.5 rounded-lg border border-indigo-500/30 space-y-2 text-xs animate-fadeIn">
          <div className="flex items-center justify-between text-indigo-300 font-semibold border-b border-slate-800 pb-1.5">
            <span>Model Explainability Breakdown</span>
            <code className="text-[10px] text-slate-400 font-mono">{analysis.model_name} (v{analysis.prompt_version})</code>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-slate-300 pt-1">
            <div>
              <strong className="text-slate-400 block mb-0.5">Intent Reasoning:</strong>
              <span>Classified as <code>{analysis.intent}</code> based on explicit operational requests in text.</span>
            </div>
            <div>
              <strong className="text-slate-400 block mb-0.5">Priority Calculation:</strong>
              <span>Weighted as <code>{analysis.priority}</code> based on detected deadlines and SLA commitments.</span>
            </div>
          </div>
        </div>
      )}

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
                <div className="flex items-center gap-1.5 shrink-0">
                  {/* Google Calendar 1-Click Sync Button */}
                  {scheduledLinks[item.id] ? (
                    <a
                      href={scheduledLinks[item.id]}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] px-2 py-1 rounded bg-sky-600/20 text-sky-300 border border-sky-500/40 font-medium hover:bg-sky-600/30 transition flex items-center gap-1"
                      title="Open in Google Calendar"
                    >
                      <span>📅</span> View GCal
                    </a>
                  ) : (
                    <button
                      onClick={() => handleScheduleAction(item)}
                      disabled={schedulingId === item.id}
                      className="text-[11px] px-2 py-1 rounded bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/40 font-medium transition flex items-center gap-1 disabled:opacity-50"
                      title="Schedule Deadline into Google Calendar"
                    >
                      <span>📅</span> {schedulingId === item.id ? 'Syncing...' : 'Sync GCal'}
                    </button>
                  )}

                  {item.status === 'PENDING' ? (
                    <>
                      <button
                        onClick={() => onActionStatusChange && onActionStatusChange(item.id, 'CONFIRMED')}
                        className="text-[11px] px-2.5 py-1 rounded bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 border border-emerald-500/40 font-medium transition"
                      >
                        Confirm
                      </button>
                      <button
                        onClick={() => onActionStatusChange && onActionStatusChange(item.id, 'COMPLETED')}
                        className="text-[11px] px-2.5 py-1 rounded bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 border border-blue-500/40 font-medium transition"
                        title="Mark Complete"
                      >
                        Complete
                      </button>
                      <button
                        onClick={() => onActionStatusChange && onActionStatusChange(item.id, 'DISMISSED')}
                        className="text-[11px] px-2.5 py-1 rounded bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700 font-medium transition"
                      >
                        Dismiss
                      </button>
                    </>
                  ) : (
                    <span className="text-[11px] px-2 py-0.5 rounded font-mono font-medium border bg-slate-800 text-slate-300 border-slate-700">
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
        <div className="border-t border-slate-800 pt-3">
          <button
            onClick={() => setShowEvidence(!showEvidence)}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 transition"
          >
            <span>{showEvidence ? '▼ Hide' : '▶ Show'} Grounding Evidence Snippets</span>
          </button>
          {showEvidence && (
            <div className="mt-2 space-y-2 bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
              {analysis.extracted_items.map((item: ExtractedActionItem) =>
                item.evidence_snippet ? (
                  <div key={`ev-${item.id}`} className="space-y-0.5 border-b border-slate-900 pb-1.5 last:border-b-0">
                    <span className="text-[11px] font-semibold text-slate-300">{item.description}:</span>
                    <blockquote className="text-slate-400 italic border-l-2 border-indigo-500/50 pl-2">
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
