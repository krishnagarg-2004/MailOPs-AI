import React, { useEffect, useState } from 'react';
import { EmailAnalysisCard } from '../components/EmailAnalysisCard';
import { ReplyDraftWidget } from '../components/ReplyDraftWidget';
import { EmailMessageSummary, EmailThreadSummary, api } from '../services/api';
import { AIAnalysisResult, ActionStatusEnum } from '../types/ai';
import { ReplyDraftResult, ToneEnum } from '../types/reply_draft';

export const InboxDashboardView: React.FC = () => {
  const [threads, setThreads] = useState<EmailThreadSummary[]>([]);
  const [selectedThread, setSelectedThread] = useState<EmailThreadSummary | null>(null);
  const [selectedMessage, setSelectedMessage] = useState<EmailMessageSummary | null>(null);
  const [analysis, setAnalysis] = useState<AIAnalysisResult | null>(null);
  const [draft, setDraft] = useState<ReplyDraftResult | null>(null);

  const [isLoadingThreads, setIsLoadingThreads] = useState<boolean>(true);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isDrafting, setIsDrafting] = useState<boolean>(false);
  const [requiresComposeConsent, setRequiresComposeConsent] = useState<boolean>(false);

  // 3-Pane Filter & View States
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterMode, setFilterMode] = useState<'ALL' | 'UNREAD' | 'URGENT' | 'ACTIONS'>('ALL');
  const [isInspectorOpen, setIsInspectorOpen] = useState<boolean>(true);
  const [activeInspectorTab, setActiveInspectorTab] = useState<'INTELLIGENCE' | 'COPILOT'>('INTELLIGENCE');
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [digestSummary, setDigestSummary] = useState<any>(null);
  const [showDigestModal, setShowDigestModal] = useState<boolean>(false);
  const [showShortcutsModal, setShowShortcutsModal] = useState<boolean>(false);

  const fetchThreads = async () => {
    try {
      setIsLoadingThreads(true);
      const data = await api.getGmailThreads();
      setThreads(data);
      if (data.length > 0) {
        setSelectedThread(data[0]);
        if (data[0].messages.length > 0) {
          handleSelectMessage(data[0].messages[0]);
        }
      }
    } catch {
      // Ignore background errors
    } finally {
      setIsLoadingThreads(false);
    }
  };

  useEffect(() => {
    fetchThreads();
  }, []);

  const handleSelectMessage = async (msg: EmailMessageSummary) => {
    setSelectedMessage(msg);
    setAnalysis(null);
    setDraft(null);

    // Try fetching existing analysis and reply draft
    try {
      const existingAnalysis = await api.getMessageAnalysis(msg.id);
      setAnalysis(existingAnalysis);
    } catch {
      // Not analyzed yet
    }

    try {
      const drafts = await api.getReplyDraftsForMessage(msg.id);
      if (drafts.length > 0) {
        setDraft(drafts[0]);
      }
    } catch {
      // No draft yet
    }
  };

  const handleTriggerAnalysis = async () => {
    if (!selectedMessage) return;
    try {
      setIsAnalyzing(true);
      const result = await api.analyzeMessage(selectedMessage.id);
      setAnalysis(result);
      setActiveInspectorTab('INTELLIGENCE');
      if (!isInspectorOpen) setIsInspectorOpen(true);
    } catch (err: any) {
      alert(`AI Extraction Error: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleActionStatusChange = async (actionId: string, newStatus: ActionStatusEnum) => {
    try {
      await api.updateActionStatus(actionId, newStatus);
      if (selectedMessage) {
        const updatedAnalysis = await api.getMessageAnalysis(selectedMessage.id);
        setAnalysis(updatedAnalysis);
      }
    } catch (err: any) {
      alert(`Action Status Update Failed: ${err.message}`);
    }
  };

  const handleGenerateReply = async (tone: ToneEnum) => {
    if (!selectedMessage) return;
    try {
      setIsDrafting(true);
      const result = await api.generateReplyDraft(selectedMessage.id, tone);
      setDraft(result);
      setActiveInspectorTab('COPILOT');
      if (!isInspectorOpen) setIsInspectorOpen(true);
    } catch (err: any) {
      alert(`Reply Generation Error: ${err.message}`);
    } finally {
      setIsDrafting(false);
    }
  };

  const handleSaveDraftEdits = async (subject: string, bodyText: string, tone: ToneEnum) => {
    if (!draft) return;
    try {
      const updated = await api.updateReplyDraft(draft.id, { subject, body_text: bodyText, tone });
      setDraft(updated);
    } catch (err: any) {
      alert(`Draft Save Error: ${err.message}`);
    }
  };

  const handleSyncGmailDraft = async () => {
    if (!draft) return;
    try {
      setRequiresComposeConsent(false);
      const synced = await api.syncGmailDraft(draft.id);
      setDraft(synced);
      alert('Successfully synced draft to Gmail!');
    } catch (err: any) {
      if (err.status === 403) {
        setRequiresComposeConsent(true);
      } else {
        alert(`Gmail Sync Error: ${err.message}`);
      }
    }
  };

  const handleSendReplyEmail = async () => {
    if (!draft) return;
    if (!confirm('Are you sure you want to approve and send this email via Gmail?')) return;
    try {
      setRequiresComposeConsent(false);
      const sent = await api.sendReplyEmail(draft.id);
      setDraft(sent);
      alert('Email successfully sent!');
    } catch (err: any) {
      if (err.status === 403) {
        setRequiresComposeConsent(true);
      } else {
        alert(`Email Send Error: ${err.message}`);
      }
    }
  };

  const handleDiscardDraft = async () => {
    if (!draft) return;
    try {
      await api.discardReplyDraft(draft.id);
      setDraft(null);
    } catch (err: any) {
      alert(`Discard Error: ${err.message}`);
    }
  };

  const handleOpenDigest = async () => {
    try {
      setIsExporting(true);
      const summary = await api.getExecutiveDigest();
      setDigestSummary(summary);
      setShowDigestModal(true);
    } catch (err: any) {
      alert(`Executive Digest Error: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  const handleDownloadExport = async (format: 'csv' | 'markdown' | 'json') => {
    try {
      await api.downloadDigestExport(format);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    }
  };

  // Filter threads by search query and filter badge
  const filteredThreads = threads.filter((t) => {
    const firstMsg = t.messages[0];
    const matchSearch =
      !searchQuery ||
      t.snippet?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      firstMsg?.subject?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      firstMsg?.sender?.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchSearch) return false;

    if (filterMode === 'URGENT') {
      const subj = firstMsg?.subject?.toLowerCase() || '';
      return subj.includes('urgent') || subj.includes('asap') || subj.includes('deadline');
    }
    if (filterMode === 'ACTIONS') {
      return (t.messages.length > 1) || (firstMsg?.has_attachments);
    }
    return true;
  });

  // Superhuman-Style Keyboard Shortcuts Listener (j/k, r, a, x, ?)
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is currently typing in an input or textarea
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      if (e.key === '?' || (e.shiftKey && e.key === '/')) {
        e.preventDefault();
        setShowShortcutsModal((prev) => !prev);
      } else if (e.key === 'j' || e.key === 'ArrowDown') {
        e.preventDefault();
        if (filteredThreads.length === 0) return;
        const currentIndex = filteredThreads.findIndex((t) => t.id === selectedThread?.id);
        const nextIndex = currentIndex < filteredThreads.length - 1 ? currentIndex + 1 : 0;
        const nextThread = filteredThreads[nextIndex];
        setSelectedThread(nextThread);
        if (nextThread.messages.length > 0) handleSelectMessage(nextThread.messages[0]);
      } else if (e.key === 'k' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (filteredThreads.length === 0) return;
        const currentIndex = filteredThreads.findIndex((t) => t.id === selectedThread?.id);
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : filteredThreads.length - 1;
        const prevThread = filteredThreads[prevIndex];
        setSelectedThread(prevThread);
        if (prevThread.messages.length > 0) handleSelectMessage(prevThread.messages[0]);
      } else if (e.key.toLowerCase() === 'a') {
        e.preventDefault();
        handleTriggerAnalysis();
      } else if (e.key.toLowerCase() === 'r') {
        e.preventDefault();
        setActiveInspectorTab('COPILOT');
        if (!isInspectorOpen) setIsInspectorOpen(true);
      } else if (e.key.toLowerCase() === 'x') {
        e.preventDefault();
        setIsInspectorOpen((prev) => !prev);
      }
    };

    const handleCustomOpenShortcuts = () => setShowShortcutsModal(true);

    window.addEventListener('keydown', handleGlobalKeyDown);
    window.addEventListener('open-keyboard-shortcuts', handleCustomOpenShortcuts);
    return () => {
      window.removeEventListener('keydown', handleGlobalKeyDown);
      window.removeEventListener('open-keyboard-shortcuts', handleCustomOpenShortcuts);
    };
  }, [filteredThreads, selectedThread, isInspectorOpen]);

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)]">
      {/* Top Bar with View Controls, Hotkeys & Export */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3 shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-100">3-Pane Work Intelligence & AI Workspace</h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/30">
              Superhuman View
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Streamlined thread navigator, full conversation reader, and integrated AI copilot inspector.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowShortcutsModal(true)}
            className="text-xs bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 px-2.5 py-1.5 rounded-lg transition font-mono flex items-center gap-1"
            title="View keyboard hotkeys (?)"
          >
            <span>⌨️</span>
            <span>Hotkeys</span>
            <kbd className="text-[10px] bg-slate-800 px-1 rounded text-slate-500">?</kbd>
          </button>

          <button
            onClick={handleOpenDigest}
            disabled={isExporting}
            className="flex items-center gap-1.5 text-xs bg-slate-900 hover:bg-slate-800 text-indigo-300 border border-indigo-500/30 px-3 py-1.5 rounded-lg transition font-medium"
          >
            <span>📊 Executive Digest</span>
          </button>

          <button
            onClick={() => setIsInspectorOpen(!isInspectorOpen)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition font-medium ${
              isInspectorOpen
                ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/40'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            {isInspectorOpen ? 'Hide AI Inspector (x)' : 'Show AI Inspector (x)'}
          </button>
        </div>
      </div>

      {/* 3-Pane Split Layout Grid */}
      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0 overflow-hidden">
        {/* Pane 1: Left Thread Navigator (3 cols) */}
        <div className="col-span-12 md:col-span-4 lg:col-span-3 flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden min-h-0 min-w-0">
          {/* Search & Filter Header */}
          <div className="p-3 border-b border-slate-800 space-y-2 bg-slate-950/40">
            <input
              type="text"
              placeholder="Search threads (sender, subject)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg text-xs px-3 py-1.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <div className="flex items-center gap-1 text-[10px]">
              {(['ALL', 'URGENT', 'ACTIONS'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setFilterMode(mode)}
                  className={`px-2 py-0.5 rounded font-medium transition ${
                    filterMode === mode
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-800/80 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {mode}
                </button>
              ))}
              <span className="ml-auto text-slate-500 font-mono">
                {filteredThreads.length}
              </span>
            </div>
          </div>

          {/* Thread List */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60 p-1">
            {isLoadingThreads ? (
              <div className="text-xs text-slate-500 py-12 text-center">Loading mailbox threads...</div>
            ) : filteredThreads.length === 0 ? (
              <div className="text-xs text-slate-500 py-12 text-center space-y-2">
                <p>No matching email threads.</p>
                <button
                  onClick={async () => {
                    try {
                      await api.seedDemoData();
                      fetchThreads();
                    } catch {}
                  }}
                  className="text-[11px] text-emerald-400 underline hover:text-emerald-300"
                >
                  ⚡ Load Demo Mailbox
                </button>
              </div>
            ) : (
              filteredThreads.map((t) => {
                const isSelected = selectedThread?.id === t.id;
                const firstMsg = t.messages[0];
                return (
                  <div
                    key={t.id}
                    onClick={() => {
                      setSelectedThread(t);
                      if (t.messages.length > 0) handleSelectMessage(t.messages[0]);
                    }}
                    className={`p-3 rounded-lg cursor-pointer transition text-left ${
                      isSelected
                        ? 'bg-indigo-950/40 border border-indigo-500/40 shadow-xs'
                        : 'hover:bg-slate-800/50 border border-transparent'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-200 truncate max-w-[140px]">
                        {firstMsg?.sender?.split('<')[0]?.trim() || 'Unknown'}
                      </span>
                      <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.2 rounded font-mono">
                        {t.messages.length} msg{t.messages.length > 1 ? 's' : ''}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 font-medium truncate">
                      {firstMsg?.subject || 'No Subject'}
                    </p>
                    <p className="text-[11px] text-slate-500 truncate mt-1">
                      {t.snippet}
                    </p>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Pane 2: Center Message Thread Reader (5 cols or 9 cols if inspector closed) */}
        <div
          className={`${
            isInspectorOpen ? 'col-span-12 md:col-span-8 lg:col-span-5' : 'col-span-12 md:col-span-8 lg:col-span-9'
          } flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden min-h-0 min-w-0`}
        >
          {selectedMessage ? (
            <div className="flex flex-col h-full min-h-0">
              {/* Message Header & Action Toolbar */}
              <div className="p-4 border-b border-slate-800 bg-slate-950/30 flex flex-wrap items-center justify-between gap-3 shrink-0">
                <div className="min-w-0">
                  <h3 className="text-sm font-bold text-slate-100 truncate">
                    {selectedMessage.subject || 'No Subject'}
                  </h3>
                  <div className="flex items-center gap-2 mt-1 text-xs text-slate-400">
                    <div className="w-5 h-5 rounded-full bg-indigo-600/30 text-indigo-300 flex items-center justify-center font-bold text-[10px]">
                      {selectedMessage.sender?.[0]?.toUpperCase() || 'U'}
                    </div>
                    <span className="truncate">{selectedMessage.sender}</span>
                    {selectedMessage.has_attachments && (
                      <span className="text-[10px] bg-slate-800 text-amber-300 px-1.5 py-0.5 rounded border border-amber-500/30">
                        📎 Attachment
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={handleTriggerAnalysis}
                    disabled={isAnalyzing}
                    className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-3 py-1.5 rounded-lg transition disabled:opacity-50 shadow-sm"
                    title="Run Gemini analysis (Hot-key: a)"
                  >
                    {isAnalyzing ? 'Extracting...' : '✨ Analyze (a)'}
                  </button>

                  <button
                    onClick={() => {
                      if (!draft) {
                        handleGenerateReply('PROFESSIONAL');
                      } else {
                        setActiveInspectorTab('COPILOT');
                        if (!isInspectorOpen) setIsInspectorOpen(true);
                      }
                    }}
                    disabled={isDrafting}
                    className="text-xs bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 px-3 py-1.5 rounded-lg transition font-medium"
                    title="Open AI Copilot (Hot-key: r)"
                  >
                    {isDrafting ? 'Drafting...' : '✍️ Reply (r)'}
                  </button>
                </div>
              </div>

              {/* Message Body Reader */}
              <div className="flex-1 p-5 overflow-y-auto space-y-4">
                {selectedMessage.attachments && selectedMessage.attachments.length > 0 && (
                  <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800 space-y-1.5">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                      Attachments ({selectedMessage.attachments.length})
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {selectedMessage.attachments.map((att) => (
                        <div
                          key={att.id}
                          className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-2.5 py-1.5 rounded text-xs text-slate-300"
                        >
                          <span>📄</span>
                          <span className="font-mono">{att.filename}</span>
                          <span className="text-[10px] text-slate-500">
                            ({Math.round(att.size_bytes / 1024)} KB)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 text-xs text-slate-200 leading-relaxed font-sans whitespace-pre-wrap break-words break-all overflow-x-hidden">
                  {selectedMessage.body_plain || 'No body text.'}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-xs text-slate-500 p-8 text-center space-y-3">
              <p>Select an email thread from the left or press <code>j</code> / <code>k</code> to navigate.</p>
              <button
                onClick={async () => {
                  try {
                    await api.seedDemoData();
                    fetchThreads();
                  } catch {}
                }}
                className="text-xs bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 px-3 py-1.5 rounded-lg transition"
              >
                ⚡ Load Sample Enterprise Mailbox
              </button>
            </div>
          )}
        </div>

        {/* Pane 3: Right Collapsible AI Work Intelligence Inspector & Copilot (4 cols) */}
        {isInspectorOpen && (
          <div className="col-span-12 lg:col-span-4 flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden min-h-0 min-w-0">
            {/* Inspector Tab Selector */}
            <div className="p-2 border-b border-slate-800 flex items-center justify-between bg-slate-950/40 shrink-0">
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setActiveInspectorTab('INTELLIGENCE')}
                  className={`text-xs px-3 py-1 rounded-md font-medium transition ${
                    activeInspectorTab === 'INTELLIGENCE'
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  ⚡ Intelligence
                </button>
                <button
                  onClick={() => setActiveInspectorTab('COPILOT')}
                  className={`text-xs px-3 py-1 rounded-md font-medium transition ${
                    activeInspectorTab === 'COPILOT'
                      ? 'bg-emerald-600/20 text-emerald-300 border border-emerald-500/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  🤖 Copilot Reply
                </button>
              </div>

              <button
                onClick={() => setIsInspectorOpen(false)}
                title="Collapse Inspector (x)"
                className="text-slate-400 hover:text-slate-200 text-xs px-2 py-1 rounded hover:bg-slate-800 transition font-mono"
              >
                ✕ (x)
              </button>
            </div>

            {/* Inspector Tab Content */}
            <div className="flex-1 p-4 overflow-y-auto space-y-4">
              {activeInspectorTab === 'INTELLIGENCE' ? (
                analysis ? (
                  <EmailAnalysisCard
                    analysis={analysis}
                    onActionStatusChange={handleActionStatusChange}
                  />
                ) : (
                  <div className="text-center py-16 text-slate-500 text-xs space-y-3">
                    <p>No AI intelligence extraction generated for this email yet.</p>
                    <button
                      onClick={handleTriggerAnalysis}
                      disabled={isAnalyzing}
                      className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-4 py-2 rounded-lg transition disabled:opacity-50"
                    >
                      {isAnalyzing ? 'Extracting...' : '✨ Analyze with Gemini (a)'}
                    </button>
                  </div>
                )
              ) : (
                <ReplyDraftWidget
                  draft={draft}
                  onGenerateDraft={handleGenerateReply}
                  onSaveEdits={handleSaveDraftEdits}
                  onSyncGmail={handleSyncGmailDraft}
                  onSendEmail={handleSendReplyEmail}
                  onDiscardDraft={handleDiscardDraft}
                  isLoading={isDrafting}
                  requiresComposeConsent={requiresComposeConsent}
                />
              )}
            </div>
          </div>
        )}
      </div>

      {/* Keyboard Shortcuts Cheat Sheet Modal */}
      {showShortcutsModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-5 shadow-2xl space-y-4 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <span className="text-base">⌨️</span>
                <h3 className="text-sm font-bold text-slate-100">Superhuman Keyboard Shortcuts</h3>
              </div>
              <button
                onClick={() => setShowShortcutsModal(false)}
                className="text-slate-400 hover:text-slate-200 text-xs px-2 py-1 rounded hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                <span className="text-slate-300">Navigate down threads</span>
                <kbd className="bg-slate-800 text-slate-200 font-mono px-2 py-0.5 rounded border border-slate-700">j</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                <span className="text-slate-300">Navigate up threads</span>
                <kbd className="bg-slate-800 text-slate-200 font-mono px-2 py-0.5 rounded border border-slate-700">k</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                <span className="text-slate-300">Run Gemini AI analysis</span>
                <kbd className="bg-slate-800 text-slate-200 font-mono px-2 py-0.5 rounded border border-slate-700">a</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                <span className="text-slate-300">Focus AI Copilot Reply</span>
                <kbd className="bg-slate-800 text-slate-200 font-mono px-2 py-0.5 rounded border border-slate-700">r</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                <span className="text-slate-300">Toggle AI Inspector pane</span>
                <kbd className="bg-slate-800 text-slate-200 font-mono px-2 py-0.5 rounded border border-slate-700">x</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                <span className="text-slate-300">Open Command Palette</span>
                <kbd className="bg-slate-800 text-slate-200 font-mono px-2 py-0.5 rounded border border-slate-700">Ctrl+K</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                <span className="text-slate-300">Accept ghost autocomplete</span>
                <kbd className="bg-slate-800 text-slate-200 font-mono px-2 py-0.5 rounded border border-slate-700">Tab</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                <span className="text-slate-300">Show keyboard shortcuts</span>
                <kbd className="bg-slate-800 text-slate-200 font-mono px-2 py-0.5 rounded border border-slate-700">?</kbd>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Executive Digest Modal */}
      {showDigestModal && digestSummary && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-fadeIn">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
              <div>
                <h3 className="text-base font-bold text-slate-100">MailOps Executive Intelligence Digest</h3>
                <p className="text-xs text-slate-400">
                  Aggregated cross-mailbox KPIs, action item tracking, and strategic risk registry.
                </p>
              </div>
              <button
                onClick={() => setShowDigestModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm px-2 py-1 rounded hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-5 text-xs text-slate-300">
              {/* Metric KPI Tiles */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold">Analyzed Emails</span>
                  <p className="text-lg font-bold text-slate-100 mt-1">{digestSummary.total_emails_analyzed}</p>
                </div>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold">Pending Actions</span>
                  <p className="text-lg font-bold text-amber-400 mt-1">{digestSummary.pending_actions}</p>
                </div>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold">High Risks</span>
                  <p className="text-lg font-bold text-rose-400 mt-1">{digestSummary.high_severity_risks}</p>
                </div>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold">Financial Total</span>
                  <p className="text-lg font-bold text-emerald-400 mt-1">
                    ${digestSummary.total_financial_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </p>
                </div>
              </div>

              {/* Top Pending Actions List */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Priority Action Items</h4>
                {digestSummary.top_actions?.length > 0 ? (
                  <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                    {digestSummary.top_actions.map((act: any) => (
                      <div key={act.id} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                        <div className="truncate max-w-[70%]">
                          <span className="font-semibold text-slate-200 block truncate">{act.description}</span>
                          <span className="text-[10px] text-slate-500">
                            {act.assignee ? `Assigned to: ${act.assignee}` : 'Unassigned'}
                            {act.due_date ? ` • Due: ${act.due_date.split('T')[0]}` : ''}
                          </span>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                          {act.status}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 italic">No pending action items.</p>
                )}
              </div>

              {/* Active Risks List */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Active Business Risks</h4>
                {digestSummary.active_risks?.length > 0 ? (
                  <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                    {digestSummary.active_risks.map((risk: any) => (
                      <div key={risk.id} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                        <span className="font-medium text-slate-200 truncate max-w-[75%]">{risk.description}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                          {risk.severity_or_priority}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 italic">No active business risks recorded.</p>
                )}
              </div>
            </div>

            {/* Export Format Action Buttons */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between">
              <span className="text-xs text-slate-400">Download formatted export:</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownloadExport('csv')}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 transition font-medium"
                >
                  📥 Export CSV
                </button>
                <button
                  onClick={() => handleDownloadExport('markdown')}
                  className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg transition font-medium shadow-xs"
                >
                  📝 Export Markdown
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
