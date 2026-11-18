import React, { useEffect, useRef, useState } from 'react';
import {
  Keyboard,
  BarChart3,
  Sparkles,
  Reply,
  Paperclip,
  Search,
  ArrowDown,
  Bot,
  X,
  Download,
  Mail,
} from 'lucide-react';
import { EmailAnalysisCard } from '../components/EmailAnalysisCard';
import { ReplyDraftWidget } from '../components/ReplyDraftWidget';
import { useToast } from '../context/ToastContext';
import { EmailMessageSummary, EmailThreadSummary, api } from '../services/api';
import { AIAnalysisResult, ActionStatusEnum } from '../types/ai';
import { ReplyDraftResult, ToneEnum } from '../types/reply_draft';

export const InboxDashboardView: React.FC = () => {
  const { toast, requestConfirmation } = useToast();
  const [threads, setThreads] = useState<EmailThreadSummary[]>([]);
  const [selectedThread, setSelectedThread] = useState<EmailThreadSummary | null>(null);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [selectedMessage, setSelectedMessage] = useState<EmailMessageSummary | null>(null);
  const [analysis, setAnalysis] = useState<AIAnalysisResult | null>(null);
  const [draft, setDraft] = useState<ReplyDraftResult | null>(null);

  const [isLoadingThreads, setIsLoadingThreads] = useState<boolean>(true);
  const [isLoadingOlder, setIsLoadingOlder] = useState<boolean>(false);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncProgressMsg, setSyncProgressMsg] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isDrafting, setIsDrafting] = useState<boolean>(false);
  const [requiresComposeConsent, setRequiresComposeConsent] = useState<boolean>(false);
  const [threadLimit, setThreadLimit] = useState<number>(100);

  const threadLimitRef = useRef<number>(threadLimit);
  threadLimitRef.current = threadLimit;

  const selectedThreadIdRef = useRef<string | null>(null);
  const selectedMessageIdRef = useRef<string | null>(null);
  const draftRef = useRef<ReplyDraftResult | null>(null);

  useEffect(() => {
    threadLimitRef.current = threadLimit;
  }, [threadLimit]);

  useEffect(() => {
    selectedThreadIdRef.current = selectedThreadId;
  }, [selectedThreadId]);

  useEffect(() => {
    selectedMessageIdRef.current = selectedMessage?.id ?? null;
  }, [selectedMessage]);

  useEffect(() => {
    draftRef.current = draft;
  }, [draft]);

  // 3-Pane Filter & View States
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterMode, setFilterMode] = useState<'ALL' | 'UNREAD' | 'URGENT' | 'ACTIONS'>('ALL');
  const [isInspectorOpen, setIsInspectorOpen] = useState<boolean>(true);
  const [activeInspectorTab, setActiveInspectorTab] = useState<'INTELLIGENCE' | 'COPILOT'>('INTELLIGENCE');
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [digestSummary, setDigestSummary] = useState<any>(null);
  const [showDigestModal, setShowDigestModal] = useState<boolean>(false);
  const [showShortcutsModal, setShowShortcutsModal] = useState<boolean>(false);

  const fetchThreads = async (customLimit?: number) => {
    try {
      setIsLoadingThreads(true);
      const limit = customLimit ?? threadLimitRef.current;
      const data = await api.getGmailThreads({ limit });
      setThreads(data);

      const targetThreadId = selectedThreadIdRef.current || selectedThreadId || selectedThread?.id;
      const targetMsgId = selectedMessageIdRef.current || selectedMessage?.id;

      if (targetThreadId) {
        const existingThread = data.find((t) => t.id === targetThreadId);
        if (existingThread) {
          setSelectedThread(existingThread);
          setSelectedThreadId(existingThread.id);
          selectedThreadIdRef.current = existingThread.id;
          if (targetMsgId) {
            const existingMsg = existingThread.messages.find((m) => m.id === targetMsgId);
            if (existingMsg) {
              setSelectedMessage(existingMsg);
              selectedMessageIdRef.current = existingMsg.id;
              return;
            }
          }
          if (existingThread.messages.length > 0) {
            handleSelectMessage(existingThread.messages[0], true);
          }
          return;
        } else if (selectedThreadIdRef.current) {
          return;
        }
      }

      if (data.length > 0 && !selectedThreadIdRef.current) {
        setSelectedThread(data[0]);
        setSelectedThreadId(data[0].id);
        selectedThreadIdRef.current = data[0].id;
        if (data[0].messages.length > 0) {
          handleSelectMessage(data[0].messages[0]);
        }
      } else if (!selectedThreadIdRef.current) {
        setSelectedThread(null);
        setSelectedThreadId(null);
        setSelectedMessage(null);
        setAnalysis(null);
        setDraft(null);
      }
    } catch {
      // Ignore background errors
    } finally {
      setIsLoadingThreads(false);
    }
  };

  const handleSelectMessage = async (msg: EmailMessageSummary, retainExistingDraft = false) => {
    setSelectedMessage(msg);
    selectedMessageIdRef.current = msg.id;

    if (!retainExistingDraft) {
      setDraft(null);
      draftRef.current = null;
    }

    try {
      const existingAnalysis = await api.getMessageAnalysis(msg.id);
      setAnalysis(existingAnalysis);
    } catch {
      setAnalysis(null);
    }

    try {
      const drafts = await api.getReplyDraftsForMessage(msg.id);
      if (drafts && drafts.length > 0) {
        setDraft(drafts[0]);
        draftRef.current = drafts[0];
      } else if (!retainExistingDraft) {
        setDraft(null);
        draftRef.current = null;
      }
    } catch {
      if (!retainExistingDraft) {
        setDraft(null);
        draftRef.current = null;
      }
    }
  };

  const handleLoadOlderEmails = async () => {
    try {
      setIsLoadingOlder(true);
      const res = await api.syncOlderEmails(50);
      toast.info(res.message || 'Fetching older emails from archive...');
      setThreadLimit((prev) => {
        const updated = prev + 50;
        threadLimitRef.current = updated;
        return updated;
      });
      setTimeout(() => fetchThreads(threadLimitRef.current), 1500);
    } catch (err: any) {
      toast.error(`Older emails sync error: ${err.message}`);
    } finally {
      setIsLoadingOlder(false);
    }
  };

  useEffect(() => {
    fetchThreads(100);

    let eventSource: EventSource | null = null;
    try {
      eventSource = new EventSource(`${import.meta.env.VITE_API_BASE_URL ?? ''}/api/v1/events/stream`, {
        withCredentials: true,
      });

      eventSource.addEventListener('sync_started', () => {
        setIsSyncing(true);
        setSyncProgressMsg('Synchronizing inbox...');
      });

      eventSource.addEventListener('sync_progress', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          setSyncProgressMsg(`Ingesting email ${data.processed}/${data.limit}...`);
        } catch {}
      });

      eventSource.addEventListener('sync_completed', () => {
        setIsSyncing(false);
        setSyncProgressMsg(null);
        fetchThreads(threadLimitRef.current);
      });
    } catch {}

    const interval = setInterval(() => fetchThreads(threadLimitRef.current), 20000);

    return () => {
      clearInterval(interval);
      if (eventSource) eventSource.close();
    };
  }, []);

  const handleTriggerAnalysis = async () => {
    if (!selectedMessage) return;
    try {
      setIsAnalyzing(true);
      const result = await api.analyzeMessage(selectedMessage.id);
      setAnalysis(result);
      toast.success('AI intelligence extraction completed!');
    } catch (err: any) {
      toast.error(`AI Extraction Error: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerateReply = async (tone: ToneEnum) => {
    if (!selectedMessage) return;
    try {
      setIsDrafting(true);
      const res = await api.generateReplyDraft(selectedMessage.id, tone);
      setDraft(res);
      draftRef.current = res;
      setActiveInspectorTab('COPILOT');
      if (!isInspectorOpen) setIsInspectorOpen(true);
      toast.success('AI reply drafted successfully!');
    } catch (err: any) {
      if (err.message?.includes('compose scope') || err.message?.includes('consent')) {
        setRequiresComposeConsent(true);
      }
      toast.error(`Drafting error: ${err.message}`);
    } finally {
      setIsDrafting(false);
    }
  };

  const handleSaveDraftEdits = async (subj: string, body: string, t: ToneEnum) => {
    if (!draft) return;
    try {
      const updated = await api.updateReplyDraft(draft.id, {
        subject: subj,
        body_text: body,
        tone: t,
      });
      setDraft(updated);
      draftRef.current = updated;
      toast.success('Draft edits saved successfully.');
    } catch (err: any) {
      toast.error(`Save Error: ${err.message}`);
    }
  };

  const handleActionStatusChange = async (actionId: string, newStatus: ActionStatusEnum) => {
    try {
      await api.updateActionStatus(actionId, newStatus);
      if (analysis) {
        setAnalysis({
          ...analysis,
          extracted_items: analysis.extracted_items.map((i) =>
            i.id === actionId ? { ...i, status: newStatus } : i
          ),
        });
      }
      toast.success(`Action updated to ${newStatus}`);
    } catch (err: any) {
      toast.error(`Status update error: ${err.message}`);
    }
  };

  const handleSyncGmailDraft = async () => {
    if (!draft) return;
    try {
      await api.syncGmailDraft(draft.id);
      toast.success('Synced to Gmail drafts folder!');
    } catch (err: any) {
      toast.error(`Gmail Sync Error: ${err.message}`);
    }
  };

  const executeSendReplyEmail = async () => {
    if (!draft) return;
    try {
      await api.sendReplyEmail(draft.id);
      toast.success('Email sent successfully via Gmail!');
      setDraft(null);
      draftRef.current = null;
    } catch (err: any) {
      toast.error(`Send Error: ${err.message}`);
    }
  };

  const handleSendReplyEmail = () => {
    if (!draft) return;
    requestConfirmation({
      title: 'Confirm Send Email',
      message: 'Are you sure you want to approve and send this email via Gmail?',
      confirmLabel: 'Send Email',
      isDanger: true,
      onConfirm: executeSendReplyEmail,
    });
  };

  const handleDiscardDraft = async () => {
    if (!draft) return;
    try {
      await api.discardReplyDraft(draft.id);
      setDraft(null);
      draftRef.current = null;
      toast.info('Draft discarded.');
    } catch (err: any) {
      toast.error(`Discard Error: ${err.message}`);
    }
  };

  const handleOpenDigest = async () => {
    try {
      setIsExporting(true);
      const summary = await api.getExecutiveDigest();
      setDigestSummary(summary);
      setShowDigestModal(true);
    } catch (err: any) {
      toast.error(`Executive Digest Error: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  const handleDownloadExport = async (format: 'csv' | 'markdown' | 'json') => {
    try {
      await api.downloadDigestExport(format);
      toast.success(`Executive digest ${format.toUpperCase()} downloaded successfully!`);
    } catch (err: any) {
      toast.error(`Export failed: ${err.message}`);
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

  // Keyboard Shortcuts Listener
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
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
        setSelectedThreadId(nextThread.id);
        selectedThreadIdRef.current = nextThread.id;
        if (nextThread.messages.length > 0) handleSelectMessage(nextThread.messages[0]);
      } else if (e.key === 'k' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (filteredThreads.length === 0) return;
        const currentIndex = filteredThreads.findIndex((t) => t.id === selectedThread?.id);
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : filteredThreads.length - 1;
        const prevThread = filteredThreads[prevIndex];
        setSelectedThread(prevThread);
        setSelectedThreadId(prevThread.id);
        selectedThreadIdRef.current = prevThread.id;
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
    <div className="flex flex-col h-[calc(100vh-5.5rem)] font-sans">
      {/* Top Bar with View Controls, Hotkeys & Export */}
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 mb-3.5 shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-white tracking-tight">
              Work Intelligence & Mailbox Workspace
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.04] text-zinc-400 border border-white/[0.08] tracking-wider">
              Superhuman Mode
            </span>
          </div>
          <p className="text-xs text-zinc-500 mt-0.5">
            Real-time thread navigator, distraction-free reader, and Gemini AI copilot inspector.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowShortcutsModal(true)}
            className="text-xs bg-[#121216] hover:bg-[#16161c] text-zinc-400 hover:text-white border border-white/[0.08] px-2.5 py-1.5 rounded-lg transition font-mono flex items-center gap-1.5 active:scale-95 shadow-sm"
            title="View keyboard hotkeys (?)"
          >
            <Keyboard className="w-3.5 h-3.5 text-zinc-400" />
            <span className="hidden sm:inline">Keys</span>
            <kbd className="text-[10px] bg-white/[0.06] text-zinc-400 px-1 rounded border border-white/[0.08]">?</kbd>
          </button>

          <button
            onClick={handleOpenDigest}
            disabled={isExporting}
            className="flex items-center gap-1.5 text-xs bg-[#121216] hover:bg-[#16161c] text-zinc-300 hover:text-red-400 border border-white/[0.08] px-3 py-1.5 rounded-lg transition font-medium active:scale-95 shadow-sm"
          >
            <BarChart3 className="w-3.5 h-3.5 text-zinc-400" />
            <span className="hidden sm:inline">Executive Digest</span>
          </button>

          <button
            onClick={() => setIsInspectorOpen(!isInspectorOpen)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition font-medium active:scale-95 shadow-sm ${
              isInspectorOpen
                ? 'bg-red-950/40 text-red-400 border-red-500/30'
                : 'bg-[#121216] text-zinc-400 border-white/[0.08] hover:text-white'
            }`}
          >
            {isInspectorOpen ? 'Hide Inspector (x)' : 'Show Inspector (x)'}
          </button>
        </div>
      </div>

      {/* 3-Pane Split Layout Grid */}
      <div className="flex-1 grid grid-cols-12 gap-3.5 min-h-0 overflow-hidden">
        {/* Pane 1: Left Thread Navigator (3 cols) */}
        <div className="col-span-12 md:col-span-4 lg:col-span-3 flex flex-col bg-[#0e0e12] border border-white/[0.07] rounded-xl overflow-hidden min-h-0 min-w-0 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]">
          {/* Search & Filter Header */}
          <div className="p-2.5 border-b border-white/[0.06] space-y-2 bg-[#0c0c0f]">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search threads..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#121216] border border-white/[0.07] rounded-lg text-xs pl-8 pr-3 py-1.5 text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-red-500/60 transition"
              />
            </div>
            <div className="flex items-center gap-1 text-[10px]">
              {(['ALL', 'URGENT', 'ACTIONS'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setFilterMode(mode)}
                  className={`px-2.5 py-1 rounded-md font-medium transition ${
                    filterMode === mode
                      ? 'bg-white/[0.08] text-white border border-white/[0.12] font-semibold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)]'
                      : 'bg-white/[0.02] text-zinc-400 hover:text-zinc-200 border border-white/[0.05]'
                  }`}
                >
                  {mode}
                </button>
              ))}
              <span className="ml-auto text-zinc-400 font-mono text-[10px] px-1.5 py-0.5 rounded bg-white/[0.03] border border-white/[0.06] tabular-nums">
                {filteredThreads.length}
              </span>
            </div>
          </div>

          {/* Thread List */}
          <div className="flex-1 overflow-y-auto divide-y divide-white/[0.03] p-1.5 space-y-0.5">
            {isLoadingThreads ? (
              <div className="text-xs text-zinc-500 py-16 text-center space-y-2">
                <span className="w-3.5 h-3.5 border-2 border-red-500 border-t-transparent rounded-full animate-spin inline-block"></span>
                <p>Loading mailbox threads...</p>
              </div>
            ) : filteredThreads.length === 0 ? (
              <div className="text-xs text-zinc-500 py-16 text-center space-y-3">
                <p>No matching email threads.</p>
                <button
                  onClick={async () => {
                    try {
                      await api.seedDemoData();
                      fetchThreads(threadLimitRef.current);
                    } catch {}
                  }}
                  className="text-xs text-red-400 underline hover:text-red-300 font-medium"
                >
                  Load Demo Mailbox
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
                      setSelectedThreadId(t.id);
                      selectedThreadIdRef.current = t.id;
                      if (t.messages.length > 0) handleSelectMessage(t.messages[0]);
                    }}
                    className={`thread-item-contain p-2.5 rounded-lg cursor-pointer transition-all duration-150 text-left border ${
                      isSelected
                        ? 'bg-[#15151b] border-l-2 border-l-red-500 border-t-white/[0.1] border-r-white/[0.1] border-b-white/[0.1] shadow-sm'
                        : 'bg-transparent border-transparent hover:bg-white/[0.03] hover:border-white/[0.06]'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-medium text-zinc-200 truncate max-w-[140px]">
                        {firstMsg?.sender?.split('<')[0]?.trim() || 'Unknown'}
                      </span>
                      <span className="text-[10px] bg-white/[0.04] text-zinc-400 px-1.5 py-0.5 rounded font-mono border border-white/[0.06] tabular-nums">
                        {t.messages.length} msg{t.messages.length > 1 ? 's' : ''}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-300 font-medium truncate">
                      {firstMsg?.subject || 'No Subject'}
                    </p>
                    <p className="text-[11px] text-zinc-500 truncate mt-0.5">
                      {t.snippet}
                    </p>
                  </div>
                );
              })
            )}

            {/* Load Older Emails Button */}
            {filteredThreads.length > 0 && (
              <div className="pt-2 pb-1 px-1">
                <button
                  onClick={handleLoadOlderEmails}
                  disabled={isSyncing || isLoadingOlder}
                  className={`w-full py-1.5 px-3 text-xs font-medium rounded-lg border transition-all duration-150 flex items-center justify-center gap-1.5 shadow-sm ${
                    isSyncing || isLoadingOlder
                      ? 'border-white/[0.05] bg-white/[0.02] text-zinc-600 cursor-not-allowed'
                      : 'border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.06] text-zinc-300 hover:text-white active:scale-[0.98]'
                  }`}
                  title={isSyncing ? 'Mailbox synchronization in progress...' : 'Fetch older emails from your Gmail archive'}
                >
                  {isSyncing || isLoadingOlder ? (
                    <>
                      <span className="w-3 h-3 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></span>
                      <span>{syncProgressMsg || 'Syncing Mailbox...'}</span>
                    </>
                  ) : (
                    <>
                      <ArrowDown className="w-3 h-3 text-zinc-400" />
                      <span>Load Older Emails (+50)</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Pane 2: Center Message Thread Reader */}
        <div
          className={`${
            isInspectorOpen ? 'col-span-12 md:col-span-8 lg:col-span-5' : 'col-span-12 md:col-span-8 lg:col-span-9'
          } flex flex-col bg-[#0e0e12] border border-white/[0.07] rounded-xl overflow-hidden min-h-0 min-w-0 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]`}
        >
          {selectedMessage ? (
            <div className="flex flex-col h-full min-h-0">
              {/* Message Header & Action Toolbar */}
              <div className="p-3.5 border-b border-white/[0.06] bg-[#0c0c0f] flex flex-wrap items-center justify-between gap-3 shrink-0">
                <div className="min-w-0">
                  <h3 className="text-sm font-semibold text-white truncate tracking-tight">
                    {selectedMessage.subject || 'No Subject'}
                  </h3>
                  <div className="flex items-center gap-2 mt-1 text-xs text-zinc-400">
                    <div className="w-5 h-5 rounded-full bg-gradient-to-b from-zinc-700 to-zinc-900 text-zinc-200 border border-white/[0.1] flex items-center justify-center font-bold text-[10px] select-none">
                      {selectedMessage.sender?.[0]?.toUpperCase() || 'U'}
                    </div>
                    <span className="truncate text-zinc-300">{selectedMessage.sender}</span>
                    {selectedMessage.has_attachments && (
                      <span className="text-[10px] bg-white/[0.04] text-zinc-300 px-2 py-0.5 rounded-full border border-white/[0.06] flex items-center gap-1">
                        <Paperclip className="w-2.5 h-2.5" />
                        <span>Attachment</span>
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={handleTriggerAnalysis}
                    disabled={isAnalyzing}
                    className="text-xs bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-medium px-3 py-1.5 rounded-lg transition duration-150 disabled:opacity-50 shadow-sm active:scale-95 flex items-center gap-1.5"
                    title="Run Gemini analysis (Hot-key: a)"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>{isAnalyzing ? 'Extracting...' : 'Analyze (a)'}</span>
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
                    className="text-xs bg-[#121216] hover:bg-[#16161c] text-zinc-300 hover:text-white border border-white/[0.08] hover:border-white/[0.14] px-3 py-1.5 rounded-lg transition font-medium active:scale-95 flex items-center gap-1.5"
                    title="Open AI Copilot (Hot-key: r)"
                  >
                    <Reply className="w-3 h-3 text-red-400" />
                    <span>{isDrafting ? 'Drafting...' : 'Reply (r)'}</span>
                  </button>
                </div>
              </div>

              {/* Message Body Reader */}
              <div className="flex-1 p-4 overflow-y-auto space-y-3.5">
                {selectedMessage.attachments && selectedMessage.attachments.length > 0 && (
                  <div className="bg-[#0a0a0d] p-3 rounded-lg border border-white/[0.05] space-y-1.5">
                    <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block">
                      Attachments ({selectedMessage.attachments.length})
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedMessage.attachments.map((att) => (
                        <div
                          key={att.id}
                          className="flex items-center gap-1.5 bg-[#121216] border border-white/[0.06] px-2.5 py-1 rounded-md text-xs text-zinc-300"
                        >
                          <Paperclip className="w-3 h-3 text-zinc-500" />
                          <span className="font-mono text-xs">{att.filename}</span>
                          <span className="text-[10px] text-zinc-500 tabular-nums">
                            ({Math.round(att.size_bytes / 1024)} KB)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="bg-[#0a0a0d] p-4 rounded-lg border border-white/[0.05] text-xs text-zinc-300 leading-relaxed font-sans whitespace-pre-wrap break-words overflow-x-hidden">
                  {selectedMessage.body_plain || 'No body text.'}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-xs text-zinc-500 p-8 text-center space-y-2.5">
              <div className="w-10 h-10 rounded-xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center text-zinc-500">
                <Mail className="w-5 h-5" />
              </div>
              <p className="text-zinc-400">Select an email thread from the left or press <kbd className="px-1 py-0.5 rounded bg-white/[0.05] border border-white/[0.08] text-zinc-300 font-mono">j</kbd> / <kbd className="px-1 py-0.5 rounded bg-white/[0.05] border border-white/[0.08] text-zinc-300 font-mono">k</kbd> to navigate.</p>
              <button
                onClick={async () => {
                  try {
                    await api.seedDemoData();
                    fetchThreads(threadLimitRef.current);
                  } catch {}
                }}
                className="text-xs bg-white/[0.03] hover:bg-white/[0.06] text-red-400 border border-white/[0.08] px-3 py-1.5 rounded-lg transition"
              >
                Load Sample Enterprise Mailbox
              </button>
            </div>
          )}
        </div>

        {/* Pane 3: Right Collapsible AI Work Intelligence Inspector & Copilot */}
        {isInspectorOpen && (
          <div className="col-span-12 lg:col-span-4 flex flex-col bg-[#0e0e12] border border-white/[0.07] rounded-xl overflow-hidden min-h-0 min-w-0 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]">
            {/* Inspector Tab Selector */}
            <div className="p-2 border-b border-white/[0.06] flex items-center justify-between bg-[#0c0c0f] shrink-0">
              <div className="flex items-center gap-1 bg-[#121216] p-1 rounded-lg border border-white/[0.06]">
                <button
                  onClick={() => setActiveInspectorTab('INTELLIGENCE')}
                  className={`text-xs px-2.5 py-1 rounded-md font-medium transition flex items-center gap-1.5 ${
                    activeInspectorTab === 'INTELLIGENCE'
                      ? 'bg-white/[0.08] text-white border border-white/[0.12] shadow-sm font-semibold'
                      : 'text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  <Sparkles className="w-3 h-3 text-red-400" />
                  <span>Intelligence</span>
                </button>
                <button
                  onClick={() => setActiveInspectorTab('COPILOT')}
                  className={`text-xs px-2.5 py-1 rounded-md font-medium transition flex items-center gap-1.5 ${
                    activeInspectorTab === 'COPILOT'
                      ? 'bg-white/[0.08] text-white border border-white/[0.12] shadow-sm font-semibold'
                      : 'text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  <Bot className="w-3 h-3 text-red-400" />
                  <span>Copilot Reply</span>
                </button>
              </div>

              <button
                onClick={() => setIsInspectorOpen(false)}
                title="Collapse Inspector (x)"
                className="text-zinc-500 hover:text-white text-xs p-1.5 rounded-lg hover:bg-white/[0.05] transition"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Inspector Tab Content */}
            <div className="flex-1 p-3.5 overflow-y-auto space-y-3.5">
              {activeInspectorTab === 'INTELLIGENCE' ? (
                analysis ? (
                  <EmailAnalysisCard
                    analysis={analysis}
                    onActionStatusChange={handleActionStatusChange}
                  />
                ) : (
                  <div className="text-center py-16 text-zinc-500 text-xs space-y-3">
                    <div className="w-10 h-10 rounded-xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center text-zinc-500 mx-auto">
                      <Sparkles className="w-5 h-5 text-red-400" />
                    </div>
                    <p className="text-zinc-400">No AI intelligence extraction generated for this email yet.</p>
                    <button
                      onClick={handleTriggerAnalysis}
                      disabled={isAnalyzing}
                      className="text-xs bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-medium px-3.5 py-1.5 rounded-lg transition disabled:opacity-50 shadow-sm active:scale-95 flex items-center gap-1.5 mx-auto"
                    >
                      <Sparkles className="w-3 h-3" />
                      <span>{isAnalyzing ? 'Extracting...' : 'Analyze with Gemini (a)'}</span>
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

      {/* Keyboard Shortcuts Modal */}
      {showShortcutsModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-[#0f0f12] border border-white/[0.08] rounded-xl max-w-md w-full p-4 shadow-2xl space-y-3 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-white/[0.06] pb-2.5">
              <div className="flex items-center gap-2">
                <Keyboard className="w-4 h-4 text-red-400" />
                <h3 className="text-xs font-semibold text-white tracking-tight">Keyboard Navigation Shortcuts</h3>
              </div>
              <button
                onClick={() => setShowShortcutsModal(false)}
                className="text-zinc-500 hover:text-white p-1 rounded-md transition"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="space-y-1.5 text-xs">
              <div className="flex items-center justify-between p-2 rounded-lg bg-[#0a0a0d] border border-white/[0.05]">
                <span className="text-zinc-300">Navigate down threads</span>
                <kbd className="bg-white/[0.06] text-red-400 font-mono px-2 py-0.5 rounded border border-white/[0.08]">j</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-[#0a0a0d] border border-white/[0.05]">
                <span className="text-zinc-300">Navigate up threads</span>
                <kbd className="bg-white/[0.06] text-red-400 font-mono px-2 py-0.5 rounded border border-white/[0.08]">k</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-[#0a0a0d] border border-white/[0.05]">
                <span className="text-zinc-300">Run Gemini AI analysis</span>
                <kbd className="bg-white/[0.06] text-red-400 font-mono px-2 py-0.5 rounded border border-white/[0.08]">a</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-[#0a0a0d] border border-white/[0.05]">
                <span className="text-zinc-300">Focus AI Copilot Reply</span>
                <kbd className="bg-white/[0.06] text-red-400 font-mono px-2 py-0.5 rounded border border-white/[0.08]">r</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-[#0a0a0d] border border-white/[0.05]">
                <span className="text-zinc-300">Toggle AI Inspector pane</span>
                <kbd className="bg-white/[0.06] text-red-400 font-mono px-2 py-0.5 rounded border border-white/[0.08]">x</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-[#0a0a0d] border border-white/[0.05]">
                <span className="text-zinc-300">Open Command Palette</span>
                <kbd className="bg-white/[0.06] text-red-400 font-mono px-2 py-0.5 rounded border border-white/[0.08]">⌘K</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-[#0a0a0d] border border-white/[0.05]">
                <span className="text-zinc-300">Accept ghost autocomplete</span>
                <kbd className="bg-white/[0.06] text-red-400 font-mono px-2 py-0.5 rounded border border-white/[0.08]">Tab</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-[#0a0a0d] border border-white/[0.05]">
                <span className="text-zinc-300">Show keyboard shortcuts</span>
                <kbd className="bg-white/[0.06] text-red-400 font-mono px-2 py-0.5 rounded border border-white/[0.08]">?</kbd>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Executive Digest Modal */}
      {showDigestModal && digestSummary && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-[#0f0f12] border border-white/[0.08] rounded-xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-fadeIn">
            <div className="p-3.5 border-b border-white/[0.06] flex items-center justify-between bg-[#0c0c0f]">
              <div>
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-red-400" />
                  <span>Executive Intelligence Digest</span>
                  <span className="text-[10px] bg-red-950/40 text-red-400 border border-red-500/30 px-2 py-0.5 rounded font-mono font-medium">
                    REPORT
                  </span>
                </h3>
                <p className="text-xs text-zinc-500 mt-0.5">
                  Aggregated cross-mailbox KPIs, action item tracking, and strategic risk registry.
                </p>
              </div>
              <button
                onClick={() => setShowDigestModal(false)}
                className="text-zinc-500 hover:text-white p-1 rounded-md transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 overflow-y-auto space-y-4 text-xs text-zinc-300">
              {/* Metric KPI Tiles */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="bg-[#0a0a0d] p-3 rounded-lg border border-white/[0.06]">
                  <span className="text-[10px] text-zinc-500 uppercase font-medium">Emails</span>
                  <p className="text-base font-semibold text-white mt-0.5 font-mono tabular-nums">{digestSummary.total_emails_analyzed}</p>
                </div>
                <div className="bg-[#0a0a0d] p-3 rounded-lg border border-white/[0.06]">
                  <span className="text-[10px] text-zinc-500 uppercase font-medium">Pending Actions</span>
                  <p className="text-base font-semibold text-red-400 mt-0.5 font-mono tabular-nums">{digestSummary.pending_actions}</p>
                </div>
                <div className="bg-[#0a0a0d] p-3 rounded-lg border border-white/[0.06]">
                  <span className="text-[10px] text-zinc-500 uppercase font-medium">High Risks</span>
                  <p className="text-base font-semibold text-rose-500 mt-0.5 font-mono tabular-nums">{digestSummary.high_severity_risks}</p>
                </div>
                <div className="bg-[#0a0a0d] p-3 rounded-lg border border-white/[0.06]">
                  <span className="text-[10px] text-zinc-500 uppercase font-medium">Financial Total</span>
                  <p className="text-base font-semibold text-white mt-0.5 font-mono tabular-nums">
                    ${digestSummary.total_financial_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </p>
                </div>
              </div>

              {/* Priority Actions */}
              <div className="space-y-1.5">
                <h4 className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">Priority Action Items</h4>
                {digestSummary.top_actions?.length > 0 ? (
                  <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
                    {digestSummary.top_actions.map((act: any) => (
                      <div key={act.id} className="p-2 rounded-lg bg-[#0a0a0d] border border-white/[0.05] flex items-center justify-between">
                        <div className="truncate max-w-[70%]">
                          <span className="font-medium text-white block truncate">{act.description}</span>
                          <span className="text-[10px] text-zinc-500 font-mono">
                            {act.assignee ? `Assigned to: ${act.assignee}` : 'Unassigned'}
                            {act.due_date ? ` • Due: ${act.due_date.split('T')[0]}` : ''}
                          </span>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 rounded font-mono font-medium bg-white/[0.04] text-zinc-300 border border-white/[0.08]">
                          {act.status}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-zinc-500 italic">No pending action items.</p>
                )}
              </div>

              {/* Active Risks */}
              <div className="space-y-1.5">
                <h4 className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">Active Business Risks</h4>
                {digestSummary.active_risks?.length > 0 ? (
                  <div className="space-y-1 max-h-36 overflow-y-auto pr-1">
                    {digestSummary.active_risks.map((risk: any) => (
                      <div key={risk.id} className="p-2 rounded-lg bg-[#0a0a0d] border border-white/[0.05] flex items-center justify-between">
                        <span className="font-medium text-white truncate max-w-[75%]">{risk.description}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded font-mono font-medium bg-red-950/40 text-rose-400 border border-red-500/20">
                          {risk.severity_or_priority}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-zinc-500 italic">No active business risks recorded.</p>
                )}
              </div>
            </div>

            {/* Export Format Action Buttons */}
            <div className="p-3 border-t border-white/[0.06] bg-[#0c0c0f] flex items-center justify-between">
              <span className="text-xs text-zinc-400">Download formatted export:</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownloadExport('csv')}
                  className="text-xs bg-white/[0.04] hover:bg-white/[0.08] text-zinc-200 px-3 py-1.5 rounded-lg border border-white/[0.08] transition font-medium flex items-center gap-1.5"
                >
                  <Download className="w-3 h-3 text-zinc-400" />
                  <span>CSV</span>
                </button>
                <button
                  onClick={() => handleDownloadExport('markdown')}
                  className="text-xs bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white px-3.5 py-1.5 rounded-lg transition font-medium shadow-sm flex items-center gap-1.5"
                >
                  <Download className="w-3 h-3" />
                  <span>Markdown</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
