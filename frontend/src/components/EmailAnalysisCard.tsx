import React, { useState } from 'react';
import {
  Calendar,
  Check,
  CheckCircle,
  X,
  ChevronDown,
  ChevronRight,
  Info,
  AlertTriangle,
  ExternalLink,
  Sparkles,
} from 'lucide-react';
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
        return 'bg-red-950/40 text-rose-400 border-red-500/30 font-semibold';
      case 'MEDIUM':
        return 'bg-white/[0.04] text-zinc-300 border-white/[0.08]';
      case 'LOW':
        return 'bg-white/[0.02] text-zinc-400 border-white/[0.05]';
      default:
        return 'bg-white/[0.04] text-zinc-400 border-white/[0.06]';
    }
  };

  const getIntentBadge = (intent: string) => {
    switch (intent) {
      case 'WORK_REQUEST':
      case 'URGENT_ACTION':
        return 'bg-red-950/50 text-red-400 border-red-500/30 font-semibold';
      case 'FINANCIAL_INVOICE':
      case 'CONTRACT_LEGAL':
        return 'bg-white/[0.04] text-zinc-200 border-white/[0.1] font-medium';
      default:
        return 'bg-white/[0.03] text-zinc-400 border-white/[0.06]';
    }
  };

  const getConfidenceLevel = (score: number) => {
    if (score >= 0.9) return { label: 'High Confidence', color: 'text-red-400', bg: 'bg-red-950/40 border-red-500/30' };
    if (score >= 0.75) return { label: 'Moderate', color: 'text-zinc-300', bg: 'bg-white/[0.04] border-white/[0.08]' };
    return { label: 'Needs Review', color: 'text-zinc-400', bg: 'bg-white/[0.03] border-white/[0.06]' };
  };

  const conf = getConfidenceLevel(analysis.confidence_score);

  return (
    <div className="bg-[#0e0e12] border border-white/[0.07] rounded-xl p-4 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)] space-y-3.5 font-sans text-[#ededed] overflow-hidden break-words">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/[0.06] pb-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <div className="flex items-center gap-1 mr-1 text-zinc-500 text-[10px] uppercase tracking-wider font-semibold">
            <Sparkles className="w-3 h-3 text-red-400" />
            <span>AI Intelligence</span>
          </div>

          <span className={`text-[11px] px-2.5 py-0.5 rounded-full border ${getIntentBadge(analysis.intent)}`}>
            {analysis.intent.replace('_', ' ')}
          </span>
          <span className={`text-[11px] px-2.5 py-0.5 rounded-full border ${getPriorityBadge(analysis.priority)}`}>
            {analysis.priority}
          </span>
          {analysis.sentiment && (
            <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-white/[0.03] text-zinc-400 border border-white/[0.06] font-medium">
              {analysis.sentiment === 'NEGATIVE' ? 'Negative Risk' : analysis.sentiment === 'POSITIVE' ? 'Positive' : 'Neutral'}
            </span>
          )}
        </div>

        {/* Visual Confidence Gauge */}
        <div className="flex items-center gap-2 text-xs shrink-0">
          <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border ${conf.bg}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${analysis.confidence_score >= 0.9 ? 'bg-red-400' : 'bg-zinc-500'} animate-pulse`} />
            <span className={`font-semibold text-xs ${conf.color} font-mono tabular-nums`}>
              {(analysis.confidence_score * 100).toFixed(0)}%
            </span>
            <span className="text-zinc-500 text-[10px]">({conf.label})</span>
          </div>
          <button
            onClick={() => setShowExplainability(!showExplainability)}
            className="text-[11px] text-zinc-400 hover:text-white transition font-medium flex items-center gap-1"
          >
            <Info className="w-3 h-3 text-zinc-500" />
            {showExplainability ? 'Hide' : 'Details'}
          </button>
        </div>
      </div>

      {/* AI Explainability & Verification Drawer */}
      {showExplainability && (
        <div className="bg-[#121216] p-3 rounded-lg border border-white/[0.08] space-y-2 text-xs animate-fadeIn">
          <div className="flex items-center justify-between text-zinc-300 font-medium border-b border-white/[0.06] pb-1.5">
            <span className="text-xs">Model Explainability Breakdown</span>
            <code className="text-[10px] text-zinc-400 font-mono">{analysis.model_name} (v{analysis.prompt_version})</code>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-zinc-400 pt-1">
            <div>
              <strong className="text-zinc-300 block mb-0.5">Intent Reasoning:</strong>
              <span>Classified as <code className="text-zinc-200 font-mono">{analysis.intent}</code> based on explicit operational requests in text.</span>
            </div>
            <div>
              <strong className="text-zinc-300 block mb-0.5">Priority Calculation:</strong>
              <span>Weighted as <code className="text-zinc-200 font-mono">{analysis.priority}</code> based on detected deadlines and SLA commitments.</span>
            </div>
          </div>
        </div>
      )}

      {/* Executive Summary */}
      <div>
        <h4 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
          Executive Summary
        </h4>
        <p className="text-xs text-zinc-200 leading-relaxed bg-[#0a0a0d] border-l-2 border-l-red-500 p-3 rounded-r-lg border-y border-r border-white/[0.05]">
          {analysis.summary}
        </p>
      </div>

      {/* Evidence-Grounded Rationale */}
      <div>
        <h4 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-1">Rationale</h4>
        <p className="text-xs text-zinc-400 italic">"{analysis.rationale}"</p>
      </div>

      {/* Extracted Actions & Intelligence Items */}
      {analysis.extracted_items && analysis.extracted_items.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
            Extracted Action Items ({analysis.extracted_items.length})
          </h4>
          <div className="space-y-1.5">
            {analysis.extracted_items.map((item: ExtractedActionItem) => (
              <div
                key={item.id}
                className="flex items-start justify-between gap-3 bg-[#0a0a0d] p-3 rounded-lg border border-white/[0.06] hover:border-white/[0.12] transition"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono tracking-wider px-1.5 py-0.5 rounded bg-white/[0.04] text-red-400 border border-white/[0.06]">
                      {item.item_type}
                    </span>
                    <span className="text-xs font-medium text-white truncate">{item.description}</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-zinc-400">
                    {item.assignee && <span>Assignee: <strong className="text-zinc-200">{item.assignee}</strong></span>}
                    {item.due_date && <span>Due: <strong className="text-red-400 font-mono tabular-nums">{new Date(item.due_date).toLocaleDateString()}</strong></span>}
                    {!item.is_evidence_valid && (
                      <span className="text-rose-400 bg-red-950/40 px-1.5 py-0.5 rounded border border-red-500/20 text-[10px] flex items-center gap-1" title="Evidence snippet not found verbatim in email text">
                        <AlertTriangle className="w-2.5 h-2.5" /> Invalid Evidence
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
                      className="text-[11px] px-2.5 py-1 rounded-md bg-white/[0.04] text-red-400 border border-white/[0.08] font-medium hover:bg-white/[0.08] transition flex items-center gap-1"
                      title="Open in Google Calendar"
                    >
                      <Calendar className="w-3 h-3" />
                      <span>GCal</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  ) : (
                    <button
                      onClick={() => handleScheduleAction(item)}
                      disabled={schedulingId === item.id}
                      className="text-[11px] px-2.5 py-1 rounded-md bg-white/[0.03] text-zinc-300 hover:text-white hover:bg-white/[0.07] border border-white/[0.08] font-medium transition flex items-center gap-1 disabled:opacity-50 active:scale-95"
                      title="Schedule Deadline into Google Calendar"
                    >
                      <Calendar className="w-3 h-3 text-red-400" />
                      <span>{schedulingId === item.id ? 'Syncing...' : 'GCal'}</span>
                    </button>
                  )}

                  {item.status === 'PENDING' ? (
                    <>
                      <button
                        onClick={() => onActionStatusChange && onActionStatusChange(item.id, 'CONFIRMED')}
                        className="text-[11px] px-2.5 py-1 rounded-md bg-white/[0.04] text-zinc-300 hover:text-white hover:bg-white/[0.08] border border-white/[0.08] font-medium transition active:scale-95 flex items-center gap-1"
                      >
                        <Check className="w-3 h-3" />
                        <span>Confirm</span>
                      </button>
                      <button
                        onClick={() => onActionStatusChange && onActionStatusChange(item.id, 'COMPLETED')}
                        className="text-[11px] px-2.5 py-1 rounded-md bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-medium shadow-sm transition active:scale-95 flex items-center gap-1"
                        title="Mark Complete"
                      >
                        <CheckCircle className="w-3 h-3" />
                        <span>Complete</span>
                      </button>
                      <button
                        onClick={() => onActionStatusChange && onActionStatusChange(item.id, 'DISMISSED')}
                        className="text-[11px] px-2 py-1 rounded-md bg-white/[0.02] text-zinc-500 hover:text-zinc-300 border border-white/[0.05] font-medium transition active:scale-95"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </>
                  ) : (
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-medium border bg-white/[0.03] text-zinc-400 border-white/[0.07]">
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
        <div className="border-t border-white/[0.06] pt-2.5">
          <button
            onClick={() => setShowEvidence(!showEvidence)}
            className="text-xs text-zinc-400 hover:text-white font-medium flex items-center gap-1.5 transition"
          >
            {showEvidence ? <ChevronDown className="w-3.5 h-3.5 text-zinc-500" /> : <ChevronRight className="w-3.5 h-3.5 text-zinc-500" />}
            <span>Grounding Evidence Snippets</span>
          </button>
          {showEvidence && (
            <div className="mt-2 space-y-2 bg-[#0a0a0d] p-3 rounded-lg border border-white/[0.06] text-xs animate-fadeIn">
              {analysis.extracted_items.map((item: ExtractedActionItem) =>
                item.evidence_snippet ? (
                  <div key={`ev-${item.id}`} className="space-y-1 border-b border-white/[0.04] pb-2 last:border-b-0 last:pb-0">
                    <span className="text-[11px] font-medium text-zinc-300">{item.description}:</span>
                    <blockquote className="text-zinc-400 italic border-l border-red-500/70 pl-2.5 text-xs">
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
