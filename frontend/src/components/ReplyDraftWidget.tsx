import React, { useEffect, useRef, useState } from 'react';
import { ReplyDraftResult, ToneEnum } from '../types/reply_draft';

interface ReplyDraftWidgetProps {
  draft?: ReplyDraftResult | null;
  onGenerateDraft?: (tone: ToneEnum) => void;
  onSaveEdits?: (
    subject: string,
    bodyText: string,
    tone: ToneEnum
  ) => void;
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
  const [tone, setTone] = useState<ToneEnum>(
    draft?.tone || 'PROFESSIONAL'
  );
  const [subject, setSubject] = useState<string>(
    draft?.subject || ''
  );
  const [bodyText, setBodyText] = useState<string>(
    draft?.body_text || ''
  );
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [ghostSuggestion, setGhostSuggestion] = useState<string | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  /*
   * Synchronize local form state whenever a new AI draft
   * is received from the backend.
   */
  useEffect(() => {
    if (draft) {
      setTone(draft.tone || 'PROFESSIONAL');
      setSubject(draft.subject || '');
      setBodyText(draft.body_text || '');
      setIsEditing(false);
      setGhostSuggestion(null);
    } else {
      setSubject('');
      setBodyText('');
      setIsEditing(false);
      setGhostSuggestion(null);
    }
  }, [draft]);

  // Provide dynamic ghost-text autocomplete when user types or pauses
  useEffect(() => {
    if (!draft || !bodyText) {
      setGhostSuggestion(null);
      return;
    }

    const trimmed = bodyText.trim();
    if (trimmed.endsWith('.') || trimmed.endsWith('?') || trimmed.endsWith('!')) {
      const candidates = [
        ' Please let me know if you need any additional clarification.',
        ' Looking forward to receiving the confirmed timeline from your team.',
        ' We appreciate your continued partnership and prompt attention to this matter.',
        ' I will follow up as soon as the deliverables are verified.',
      ];
      const selected = candidates[trimmed.length % candidates.length];
      setGhostSuggestion(selected);
    } else {
      setGhostSuggestion(null);
    }
  }, [bodyText, draft]);

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

  // Insert formatting tag (e.g. bold, italic, list) into textarea at current selection
  const applyFormat = (prefix: string, suffix: string = '') => {
    const el = textareaRef.current;
    if (!el) return;

    const start = el.selectionStart;
    const end = el.selectionEnd;
    const selected = bodyText.substring(start, end);

    const replacement = `${prefix}${selected || 'text'}${suffix}`;
    const newBody = bodyText.substring(0, start) + replacement + bodyText.substring(end);

    setBodyText(newBody);
    setIsEditing(true);

    setTimeout(() => {
      el.focus();
      el.setSelectionRange(start + prefix.length, start + prefix.length + (selected ? selected.length : 4));
    }, 0);
  };

  // Quick insertion of context-tailored phrases
  const insertQuickSnippet = (snippet: string) => {
    const el = textareaRef.current;
    const prefix = bodyText.length > 0 && !bodyText.endsWith('\n') ? '\n\n' : '';
    const newText = bodyText + prefix + snippet;
    setBodyText(newText);
    setIsEditing(true);
    setGhostSuggestion(null);
    if (el) {
      setTimeout(() => {
        el.focus();
        el.setSelectionRange(newText.length, newText.length);
      }, 0);
    }
  };

  // Accept inline ghost suggestion
  const acceptGhostSuggestion = () => {
    if (!ghostSuggestion) return;
    const newText = bodyText + ghostSuggestion;
    setBodyText(newText);
    setGhostSuggestion(null);
    setIsEditing(true);
    if (textareaRef.current) {
      setTimeout(() => {
        textareaRef.current?.focus();
        textareaRef.current?.setSelectionRange(newText.length, newText.length);
      }, 0);
    }
  };

  // Handle Tab key to accept ghost autocomplete
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab' && ghostSuggestion) {
      e.preventDefault();
      acceptGhostSuggestion();
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4 text-slate-100 font-sans">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-emerald-400">
              AI Copilot & Reply Workspace
            </h3>
            <span className="text-[10px] bg-emerald-500/20 text-emerald-300 font-mono px-1.5 py-0.5 rounded border border-emerald-500/30">
              Copilot 2.0
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Rich-text editing with tab-to-accept ghost completions and human-in-the-loop consent
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <label className="text-xs font-medium text-slate-400">
            Tone Preset:
          </label>

          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
            {(['PROFESSIONAL', 'CONCISE', 'URGENT', 'EMPATHETIC'] as ToneEnum[]).map((t) => (
              <button
                key={t}
                onClick={() => {
                  setTone(t);
                  if (onGenerateDraft) {
                    onGenerateDraft(t);
                  }
                }}
                disabled={isLoading}
                className={`text-[11px] px-2.5 py-1 rounded-md font-medium transition ${
                  tone === t
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-xs'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                {t.charAt(0) + t.slice(1).toLowerCase()}
              </button>
            ))}
          </div>

          <button
            onClick={handleGenerate}
            disabled={isLoading}
            className="text-xs bg-emerald-600 hover:bg-emerald-500 text-white px-3.5 py-1.5 rounded-lg transition font-medium disabled:opacity-50 shadow-sm ml-1"
          >
            {isLoading ? 'Drafting...' : '⚡ Regenerate'}
          </button>
        </div>
      </div>

      {requiresComposeConsent && (
        <div className="bg-amber-500/10 border border-amber-500/40 p-3 rounded-lg text-xs text-amber-300 flex items-center justify-between">
          <span>
            Gmail compose scope is required to sync or send email.
          </span>
          <a
            href={`${import.meta.env.VITE_API_BASE_URL ?? ''}/api/v1/auth/google/authorize-compose`}
            className="bg-amber-600 text-slate-950 font-semibold px-3 py-1 rounded hover:bg-amber-500 transition ml-2"
          >
            Authorize Compose Scope
          </a>
        </div>
      )}

      {draft ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>
              Status:{' '}
              <strong className="text-emerald-400 uppercase">
                {draft.status}
              </strong>
            </span>
            <span>
              Recipient:{' '}
              <strong className="text-slate-200">
                {draft.recipient_email}
              </strong>
            </span>
          </div>

          <div className="space-y-2">
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Subject
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => {
                  setSubject(e.target.value);
                  setIsEditing(true);
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded text-xs p-2 text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>

            {/* Rich-Text Formatting Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-1 bg-slate-950 p-1.5 rounded-t-lg border border-slate-800 border-b-0">
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => applyFormat('**', '**')}
                  title="Bold (**text**)"
                  className="px-2 py-0.5 rounded text-xs font-bold text-slate-300 hover:text-white hover:bg-slate-800 transition border border-transparent hover:border-slate-700"
                >
                  B
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('*', '*')}
                  title="Italic (*text*)"
                  className="px-2 py-0.5 rounded text-xs italic text-slate-300 hover:text-white hover:bg-slate-800 transition border border-transparent hover:border-slate-700"
                >
                  I
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('\n- ')}
                  title="Bullet List (- item)"
                  className="px-2 py-0.5 rounded text-xs text-slate-300 hover:text-white hover:bg-slate-800 transition border border-transparent hover:border-slate-700"
                >
                  • List
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('\n> ')}
                  title="Quote (> quote)"
                  className="px-2 py-0.5 rounded text-xs text-slate-300 hover:text-white hover:bg-slate-800 transition border border-transparent hover:border-slate-700"
                >
                  " Quote
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('`', '`')}
                  title="Code snippet"
                  className="px-2 py-0.5 rounded text-xs font-mono text-slate-300 hover:text-white hover:bg-slate-800 transition border border-transparent hover:border-slate-700"
                >
                  &lt;/&gt;
                </button>
              </div>

              {/* Quick AI Suggestions Chips */}
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => insertQuickSnippet("Thank you for the update. I have confirmed receipt and reviewed the details.")}
                  className="text-[10px] bg-slate-800/80 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded transition"
                >
                  + Confirm Receipt
                </button>
                <button
                  type="button"
                  onClick={() => insertQuickSnippet("Could you please provide the estimated timeline for delivery?")}
                  className="text-[10px] bg-slate-800/80 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded transition"
                >
                  + Request Timeline
                </button>
                <button
                  type="button"
                  onClick={() => insertQuickSnippet("The proposed invoice items have been reviewed and approved for processing.")}
                  className="text-[10px] bg-slate-800/80 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded transition"
                >
                  + Approve
                </button>
              </div>
            </div>

            {/* Editor Area with Ghost Text */}
            <div className="relative">
              <textarea
                ref={textareaRef}
                rows={7}
                value={bodyText}
                onKeyDown={handleKeyDown}
                onChange={(e) => {
                  setBodyText(e.target.value);
                  setIsEditing(true);
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-b-lg text-xs p-3 text-slate-100 focus:outline-none focus:border-emerald-500 font-mono leading-relaxed"
                placeholder="Draft body content with AI assistance..."
              />

              {/* Ghost-Text Autocomplete Floating Badge */}
              {ghostSuggestion && (
                <div className="mt-1 flex items-center justify-between bg-indigo-950/50 border border-indigo-500/40 px-3 py-1.5 rounded-lg text-xs text-indigo-200 animate-fadeIn">
                  <div className="flex items-center gap-1.5 truncate max-w-[80%]">
                    <span className="text-[10px] uppercase font-bold text-indigo-400 bg-indigo-500/20 px-1 py-0.5 rounded">
                      Tab Suggestion
                    </span>
                    <span className="italic text-indigo-300 truncate">
                      "{ghostSuggestion.trim()}"
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={acceptGhostSuggestion}
                    className="text-[11px] bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-2 py-0.5 rounded transition shrink-0 ml-2 shadow-xs"
                  >
                    ⚡ Accept (Tab)
                  </button>
                </div>
              )}
            </div>
          </div>

          {draft.rationale_and_provenance && draft.rationale_and_provenance.length > 0 && (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 space-y-1 text-xs">
              <span className="font-semibold text-slate-300">
                AI Context Rationale & Provenance:
              </span>
              <ul className="list-disc list-inside text-slate-400 space-y-1">
                {draft.rationale_and_provenance.map((item, idx) => (
                  <li key={idx}>
                    <strong className="text-slate-300">[{item.source_type}]</strong>{' '}
                    {item.description}
                  </li>
                ))}
              </ul>
            </div>
          )}

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
          No AI reply draft generated yet. Click{' '}
          <strong>⚡ Regenerate</strong> to generate a context-aware response.
        </div>
      )}
    </div>
  );
};
