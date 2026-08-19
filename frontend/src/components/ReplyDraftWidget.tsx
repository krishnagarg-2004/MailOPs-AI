import React, { useEffect, useState } from 'react';
import { ReplyDraftResult, ToneEnum } from '../types/reply_draft';

interface ReplyDraftWidgetProps {
  draft?: ReplyDraftResult | null;
  onGenerateDraft?: (tone: ToneEnum) => void;
  onSaveEdits?: (subject: string, bodyText: string, tone: ToneEnum) => void;
  onSyncGmail?: () => void;
  onSendEmail?: () => void;
  onDiscardDraft?: () => void;
  isLoading?: boolean;
  requiresComposeConsent?: boolean;
}

export const ReplyDraftWidget: React.FC<ReplyDraftWidgetProps> = ({
  draft,
  onGenerateDraft,
  onSaveEdits,
  onSyncGmail,
  onSendEmail,
  onDiscardDraft,
  isLoading = false,
  requiresComposeConsent = false,
}) => {
  const [tone, setTone] = useState<ToneEnum>(draft?.tone || 'PROFESSIONAL');
  const [subject, setSubject] = useState<string>(draft?.subject || '');
  const [bodyText, setBodyText] = useState<string>(draft?.body_text || '');
  const [isEditing, setIsEditing] = useState<boolean>(false);

  const handleGenerate = () => {
    if (onGenerateDraft) {
      onGenerateDraft(tone);
    }
  };

  const handleSave = () => {
    if (onSaveEdits) {
      onSaveEdits(subject, bodyText, tone);
      setIsEditing(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4 text-slate-100 font-sans">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-emerald-400">
            Human-in-the-Loop Reply Draft Workspace
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Local-by-default AI reply drafting with explicit human review & consent
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-400">Tone:</label>
          <select
            value={tone}
            onChange={(e) => setTone(e.target.value as ToneEnum)}
            className="bg-slate-950 border border-slate-800 rounded text-xs px-2.5 py-1 text-slate-200 focus:outline-none"
          >
            <option value="PROFESSIONAL">Professional</option>
            <option value="CONCISE">Concise</option>
            <option value="URGENT">Urgent</option>
            <option value="EMPATHETIC">Empathetic</option>
          </select>

          <button
            onClick={handleGenerate}
            disabled={isLoading}
            className="text-xs bg-emerald-600 text-white px-3 py-1 rounded hover:bg-emerald-500 transition font-medium disabled:opacity-50"
          >
            {isLoading ? 'Drafting...' : 'Generate AI Draft'}
          </button>
        </div>
      </div>

      {requiresComposeConsent && (
        <div className="bg-amber-500/10 border border-amber-500/40 p-3 rounded-lg text-xs text-amber-300 flex items-center justify-between">
          <span>
            Gmail compose scope is required to sync or send email.
          </span>
          <a
            href="/api/v1/auth/google/authorize-compose"
            className="bg-amber-600 text-slate-950 font-semibold px-3 py-1 rounded hover:bg-amber-500 transition ml-2"
          >
            Authorize Compose Scope
          </a>
        </div>
      )}

      {draft ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Status: <strong className="text-emerald-400 uppercase">{draft.status}</strong></span>
            <span>Recipient: <strong className="text-slate-200">{draft.recipient_email}</strong></span>
          </div>

          <div className="space-y-2">
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Subject</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => { setSubject(e.target.value); setIsEditing(true); }}
                className="w-full bg-slate-950 border border-slate-800 rounded text-xs p-2 text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Draft Body Text</label>
              <textarea
                rows={6}
                value={bodyText}
                onChange={(e) => { setBodyText(e.target.value); setIsEditing(true); }}
                className="w-full bg-slate-950 border border-slate-800 rounded text-xs p-2 text-slate-100 focus:outline-none focus:border-emerald-500 font-mono leading-relaxed"
              />
            </div>
          </div>

          {/* Rationale & Provenance Accordion */}
          {draft.rationale_and_provenance && draft.rationale_and_provenance.length > 0 && (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 space-y-1 text-xs">
              <span className="font-semibold text-slate-300">AI Context Rationale & Provenance:</span>
              <ul className="list-disc list-inside text-slate-400 space-y-1">
                {draft.rationale_and_provenance.map((item, idx) => (
                  <li key={idx}>
                    <strong className="text-slate-300">[{item.source_type}]</strong> {item.description}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-800 pt-3">
            <button
              onClick={onDiscardDraft}
              className="text-xs text-rose-400 hover:text-rose-300 border border-rose-500/30 px-3 py-1.5 rounded transition"
            >
              Discard Draft
            </button>

            <div className="flex items-center gap-2">
              {isEditing && (
                <button
                  onClick={handleSave}
                  className="text-xs bg-slate-800 text-slate-200 border border-slate-700 px-3 py-1.5 rounded hover:bg-slate-700 transition"
                >
                  Save Edits
                </button>
              )}

              <button
                onClick={onSyncGmail}
                disabled={requiresComposeConsent}
                className="text-xs bg-cyan-600/20 text-cyan-300 border border-cyan-500/40 px-3 py-1.5 rounded hover:bg-cyan-600/30 transition font-medium disabled:opacity-50"
              >
                Sync to Gmail Drafts
              </button>

              <button
                onClick={onSendEmail}
                disabled={requiresComposeConsent}
                className="text-xs bg-emerald-600 text-white px-4 py-1.5 rounded hover:bg-emerald-500 transition font-semibold disabled:opacity-50"
              >
                Approve & Send Email
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-slate-500 text-xs">
          No AI reply draft generated yet. Click <strong>Generate AI Draft</strong> to generate a context-aware response.
        </div>
      )}
    </div>
  );
};
