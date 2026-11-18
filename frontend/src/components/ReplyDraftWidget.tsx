import React, { useEffect, useRef, useState } from 'react';
import {
  Sparkles,
  Send,
  Save,
  Trash2,
  RefreshCw,
  Bold,
  Italic,
  List,
  Quote,
  Code,
  Mail,
  Zap,
} from 'lucide-react';
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

  // Dynamic ghost-text autocomplete when user types or pauses
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab' && ghostSuggestion) {
      e.preventDefault();
      acceptGhostSuggestion();
    }
  };

  return (
    <div className="bg-[#0e0e12] border border-white/[0.07] rounded-xl p-4 sm:p-5 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)] space-y-4 text-[#ededed] font-sans">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-semibold tracking-tight text-white flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-red-400" />
              AI Copilot & Reply Workspace
            </h3>
            <span className="text-[10px] bg-red-950/40 text-red-400 font-mono px-2 py-0.5 rounded-full border border-red-500/20">
              Copilot 2.0
            </span>
          </div>
          <p className="text-xs text-zinc-500 mt-0.5">
            Rich-text drafting with tab autocomplete and human-in-the-loop consent.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Tone Selector Pills */}
          <div className="flex items-center gap-1 bg-[#121216] p-1 rounded-lg border border-white/[0.06]">
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
                    ? 'bg-white/[0.08] text-white border border-white/[0.12] font-semibold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)]'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                {t.charAt(0) + t.slice(1).toLowerCase()}
              </button>
            ))}
          </div>

          <button
            onClick={handleGenerate}
            disabled={isLoading}
            className="text-xs bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white px-3 py-1.5 rounded-lg transition font-medium disabled:opacity-50 shadow-sm flex items-center gap-1.5 active:scale-95"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-3 h-3 animate-spin" />
                <span>Drafting...</span>
              </>
            ) : (
              <>
                <Zap className="w-3 h-3" />
                <span>Regenerate</span>
              </>
            )}
          </button>
        </div>
      </div>

      {requiresComposeConsent && (
        <div className="bg-red-950/30 border border-red-500/20 p-3 rounded-lg text-xs text-red-300 flex items-center justify-between">
          <span>Gmail compose scope is required to sync or send emails.</span>
          <a
            href={`${import.meta.env.VITE_API_BASE_URL ?? ''}/api/v1/auth/google/authorize-compose`}
            className="bg-red-600 hover:bg-red-500 text-white font-medium px-3 py-1 rounded-md transition ml-2 shadow-sm text-xs"
          >
            Authorize Scope
          </a>
        </div>
      )}

      {draft ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-zinc-400 bg-[#0a0a0d] px-3 py-2 rounded-lg border border-white/[0.05]">
            <span>
              Status:{' '}
              <strong className="text-red-400 uppercase font-mono tracking-wider">
                {draft.status}
              </strong>
            </span>
            <span>
              Recipient:{' '}
              <strong className="text-zinc-200 font-mono">
                {draft.recipient_email}
              </strong>
            </span>
          </div>

          <div className="space-y-2">
            <div>
              <label className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500 block mb-1">
                Subject Line
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => {
                  setSubject(e.target.value);
                  setIsEditing(true);
                }}
                className="w-full bg-[#0a0a0d] border border-white/[0.07] rounded-lg text-xs p-2.5 text-white focus:outline-none focus:border-red-500/60 transition"
              />
            </div>

            {/* Rich-Text Formatting Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-1.5 bg-[#121216] p-2 rounded-t-lg border border-white/[0.06] border-b-0">
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => applyFormat('**', '**')}
                  title="Bold"
                  className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
                >
                  <Bold className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('*', '*')}
                  title="Italic"
                  className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
                >
                  <Italic className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('\n- ')}
                  title="Bullet List"
                  className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
                >
                  <List className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('\n> ')}
                  title="Quote"
                  className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
                >
                  <Quote className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('`', '`')}
                  title="Code snippet"
                  className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-white/[0.06] transition font-mono"
                >
                  <Code className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Quick AI Suggestions Chips */}
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => insertQuickSnippet("Thank you for the update. I have confirmed receipt and reviewed the details.")}
                  className="text-[10px] bg-white/[0.04] hover:bg-white/[0.08] text-zinc-300 border border-white/[0.06] px-2.5 py-1 rounded-md transition"
                >
                  + Confirm Receipt
                </button>
                <button
                  type="button"
                  onClick={() => insertQuickSnippet("Could you please provide the estimated timeline for delivery?")}
                  className="text-[10px] bg-white/[0.04] hover:bg-white/[0.08] text-zinc-300 border border-white/[0.06] px-2.5 py-1 rounded-md transition"
                >
                  + Request Timeline
                </button>
                <button
                  type="button"
                  onClick={() => insertQuickSnippet("The proposed invoice items have been reviewed and approved for processing.")}
                  className="text-[10px] bg-red-950/40 hover:bg-red-900/40 text-red-300 border border-red-500/20 px-2.5 py-1 rounded-md transition"
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
                className="w-full bg-[#0a0a0d] border border-white/[0.07] rounded-b-lg text-xs p-3 text-white focus:outline-none focus:border-red-500/60 font-mono leading-relaxed"
                placeholder="Draft body content with AI copilot assistance..."
              />

              {/* Ghost-Text Autocomplete Floating Badge */}
              {ghostSuggestion && (
                <div className="mt-1.5 flex items-center justify-between bg-red-950/40 border border-red-500/20 px-3 py-1.5 rounded-lg text-xs text-red-200 animate-fadeIn">
                  <div className="flex items-center gap-2 truncate max-w-[80%]">
                    <span className="text-[10px] uppercase font-mono font-bold text-red-400 bg-red-950/80 px-1.5 py-0.5 rounded border border-red-800/60">
                      Tab Auto
                    </span>
                    <span className="italic text-red-300 truncate">
                      "{ghostSuggestion.trim()}"
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={acceptGhostSuggestion}
                    className="text-[11px] bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-medium px-2.5 py-1 rounded-md transition shrink-0 ml-2 shadow-sm active:scale-95 flex items-center gap-1"
                  >
                    <span>Accept</span>
                    <kbd className="text-[9px] bg-white/[0.2] px-1 py-0.2 rounded font-mono">Tab</kbd>
                  </button>
                </div>
              )}
            </div>
          </div>

          {draft.rationale_and_provenance && draft.rationale_and_provenance.length > 0 && (
            <div className="bg-[#0a0a0d] border border-white/[0.05] rounded-lg p-3 space-y-1 text-xs">
              <span className="font-medium text-zinc-300 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                AI Context Rationale & Provenance:
              </span>
              <ul className="list-disc list-inside text-zinc-400 space-y-0.5">
                {draft.rationale_and_provenance.map((item, idx) => (
                  <li key={idx}>
                    <strong className="text-zinc-200">[{item.source_type}]</strong>{' '}
                    {item.description}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-white/[0.06] pt-3">
            <button
              onClick={onDiscardDraft}
              className="text-xs text-zinc-400 hover:text-red-400 border border-white/[0.06] hover:border-red-500/30 px-3 py-1.5 rounded-lg transition flex items-center gap-1.5"
            >
              <Trash2 className="w-3 h-3" />
              <span>Discard</span>
            </button>

            <div className="flex items-center gap-2">
              {isEditing && (
                <button
                  onClick={handleSave}
                  className="text-xs bg-white/[0.04] text-zinc-200 border border-white/[0.08] px-3 py-1.5 rounded-lg hover:bg-white/[0.08] transition flex items-center gap-1.5"
                >
                  <Save className="w-3 h-3" />
                  <span>Save Edits</span>
                </button>
              )}

              <button
                onClick={onSyncGmail}
                disabled={requiresComposeConsent}
                className="text-xs bg-[#121216] text-zinc-300 border border-white/[0.08] hover:border-white/[0.14] hover:text-white px-3 py-1.5 rounded-lg transition font-medium disabled:opacity-50 flex items-center gap-1.5"
              >
                <Mail className="w-3 h-3 text-zinc-400" />
                <span>Sync to Gmail</span>
              </button>

              <button
                onClick={onSendEmail}
                disabled={requiresComposeConsent}
                className="text-xs bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white px-4 py-1.5 rounded-lg transition font-medium disabled:opacity-50 shadow-sm flex items-center gap-1.5 active:scale-95"
              >
                <Send className="w-3 h-3" />
                <span>Approve & Send</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-10 text-zinc-500 text-xs space-y-1.5">
          <p>No AI reply draft generated yet.</p>
          <p>Click <strong className="text-red-400">Regenerate</strong> to generate a context-aware response.</p>
        </div>
      )}
    </div>
  );
};
