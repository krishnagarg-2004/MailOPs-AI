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
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-5 shadow-lg space-y-4 text-zinc-100 font-sans">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-red-400 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
              AI Copilot & Reply Workspace
            </h3>
            <span className="text-[10px] bg-red-950/60 text-red-400 font-mono px-1.5 py-0.5 rounded border border-red-800/60">
              Copilot 2.0
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Rich-text editing with tab-to-accept ghost completions and human-in-the-loop consent
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <label className="text-xs font-medium text-zinc-400">
            Tone Preset:
          </label>

          <div className="flex items-center gap-1 bg-zinc-900 p-1 rounded-lg border border-zinc-800">
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
                    ? 'bg-red-950/70 text-red-400 border border-red-800/80 shadow-xs font-semibold'
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
                }`}
              >
                {t.charAt(0) + t.slice(1).toLowerCase()}
              </button>
            ))}
          </div>

          <button
            onClick={handleGenerate}
            disabled={isLoading}
            className="text-xs bg-red-600 hover:bg-red-500 text-white px-3.5 py-1.5 rounded-lg transition font-medium disabled:opacity-50 shadow-md shadow-red-950/50 ml-1"
          >
            {isLoading ? 'Drafting...' : '⚡ Regenerate'}
          </button>
        </div>
      </div>

      {requiresComposeConsent && (
        <div className="bg-red-950/30 border border-red-800/60 p-3 rounded-lg text-xs text-red-300 flex items-center justify-between">
          <span>
            Gmail compose scope is required to sync or send email.
          </span>
          <a
            href={`${import.meta.env.VITE_API_BASE_URL ?? ''}/api/v1/auth/google/authorize-compose`}
            className="bg-red-600 text-white font-semibold px-3 py-1 rounded hover:bg-red-500 transition ml-2 shadow-sm"
          >
            Authorize Compose Scope
          </a>
        </div>
      )}

      {draft ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-zinc-400">
            <span>
              Status:{' '}
              <strong className="text-red-400 uppercase">
                {draft.status}
              </strong>
            </span>
            <span>
              Recipient:{' '}
              <strong className="text-white">
                {draft.recipient_email}
              </strong>
            </span>
          </div>

          <div className="space-y-2">
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
                Subject
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => {
                  setSubject(e.target.value);
                  setIsEditing(true);
                }}
                className="w-full bg-zinc-900 border border-zinc-800 rounded text-xs p-2 text-white focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/30"
              />
            </div>

            {/* Rich-Text Formatting Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-1 bg-zinc-900 p-1.5 rounded-t-lg border border-zinc-800 border-b-0">
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => applyFormat('**', '**')}
                  title="Bold (**text**)"
                  className="px-2 py-0.5 rounded text-xs font-bold text-zinc-300 hover:text-white hover:bg-zinc-800 transition border border-transparent hover:border-zinc-700"
                >
                  B
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('*', '*')}
                  title="Italic (*text*)"
                  className="px-2 py-0.5 rounded text-xs italic text-zinc-300 hover:text-white hover:bg-zinc-800 transition border border-transparent hover:border-zinc-700"
                >
                  I
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('\n- ')}
                  title="Bullet List (- item)"
                  className="px-2 py-0.5 rounded text-xs text-zinc-300 hover:text-white hover:bg-zinc-800 transition border border-transparent hover:border-zinc-700"
                >
                  • List
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('\n> ')}
                  title="Quote (> quote)"
                  className="px-2 py-0.5 rounded text-xs text-zinc-300 hover:text-white hover:bg-zinc-800 transition border border-transparent hover:border-zinc-700"
                >
                  " Quote
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('`', '`')}
                  title="Code snippet"
                  className="px-2 py-0.5 rounded text-xs font-mono text-zinc-300 hover:text-white hover:bg-zinc-800 transition border border-transparent hover:border-zinc-700"
                >
                  &lt;/&gt;
                </button>
              </div>

              {/* Quick AI Suggestions Chips */}
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => insertQuickSnippet("Thank you for the update. I have confirmed receipt and reviewed the details.")}
                  className="text-[10px] bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 px-2 py-0.5 rounded transition"
                >
                  + Confirm Receipt
                </button>
                <button
                  type="button"
                  onClick={() => insertQuickSnippet("Could you please provide the estimated timeline for delivery?")}
                  className="text-[10px] bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 px-2 py-0.5 rounded transition"
                >
                  + Request Timeline
                </button>
                <button
                  type="button"
                  onClick={() => insertQuickSnippet("The proposed invoice items have been reviewed and approved for processing.")}
                  className="text-[10px] bg-red-950/60 hover:bg-red-900/60 text-red-300 border border-red-800/60 px-2 py-0.5 rounded transition"
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
                className="w-full bg-zinc-900 border border-zinc-800 rounded-b-lg text-xs p-3 text-white focus:outline-none focus:border-red-500 font-mono leading-relaxed"
                placeholder="Draft body content with AI assistance..."
              />

              {/* Ghost-Text Autocomplete Floating Badge */}
              {ghostSuggestion && (
                <div className="mt-1 flex items-center justify-between bg-red-950/50 border border-red-800/50 px-3 py-1.5 rounded-lg text-xs text-red-200 animate-fadeIn">
                  <div className="flex items-center gap-1.5 truncate max-w-[80%]">
                    <span className="text-[10px] uppercase font-bold text-red-400 bg-red-950 px-1 py-0.5 rounded border border-red-800/60">
                      Tab Suggestion
                    </span>
                    <span className="italic text-red-300 truncate">
                      "{ghostSuggestion.trim()}"
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={acceptGhostSuggestion}
                    className="text-[11px] bg-red-600 hover:bg-red-500 text-white font-medium px-2 py-0.5 rounded transition shrink-0 ml-2 shadow-xs"
                  >
                    ⚡ Accept (Tab)
                  </button>
                </div>
              )}
            </div>
          </div>

          {draft.rationale_and_provenance && draft.rationale_and_provenance.length > 0 && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 space-y-1 text-xs">
              <span className="font-semibold text-zinc-300 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                AI Context Rationale & Provenance:
              </span>
              <ul className="list-disc list-inside text-zinc-400 space-y-1">
                {draft.rationale_and_provenance.map((item, idx) => (
                  <li key={idx}>
                    <strong className="text-white">[{item.source_type}]</strong>{' '}
                    {item.description}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-zinc-800 pt-3">
            <button
              onClick={onDiscardDraft}
              className="text-xs text-zinc-400 hover:text-red-400 border border-zinc-800 hover:border-red-900/60 px-3 py-1.5 rounded transition"
            >
              Discard Draft
            </button>

            <div className="flex items-center gap-2">
              {isEditing && (
                <button
                  onClick={handleSave}
                  className="text-xs bg-zinc-800 text-zinc-200 border border-zinc-700 px-3 py-1.5 rounded hover:bg-zinc-700 transition"
                >
                  Save Edits
                </button>
              )}

              <button
                onClick={onSyncGmail}
                disabled={requiresComposeConsent}
                className="text-xs bg-zinc-900 text-zinc-200 border border-zinc-800 hover:border-zinc-700 hover:text-red-400 px-3 py-1.5 rounded transition font-medium disabled:opacity-50"
              >
                Sync to Gmail Drafts
              </button>

              <button
                onClick={onSendEmail}
                disabled={requiresComposeConsent}
                className="text-xs bg-red-600 text-white px-4 py-1.5 rounded hover:bg-red-500 transition font-semibold disabled:opacity-50 shadow-md shadow-red-950/50"
              >
                Approve & Send Email
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-zinc-500 text-xs">
          No AI reply draft generated yet. Click{' '}
          <strong className="text-red-400">⚡ Regenerate</strong> to generate a context-aware response.
        </div>
      )}
    </div>
  );
};
