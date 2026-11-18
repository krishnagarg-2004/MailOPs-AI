import React, { useEffect, useRef, useState } from 'react';
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
        selectedThreadIdRef.current = null;
        setSelectedMessage(null);
        selectedMessageIdRef.current = null;
      }
    } catch {
      // Ignore background errors
    } finally {
      setIsLoadingThreads(false);
    }
  };

  const fetchThreadsRef = useRef(fetchThreads);
  fetchThreadsRef.current = fetchThreads;
  useEffect(() => {
    fetchThreadsRef.current = fetchThreads;
  });

  useEffect(() => {
    fetchThreads(threadLimitRef.current);

    // Check initial Gmail sync status
    api.getGmailStatus().then((status) => {
      if (status?.sync_state?.sync_status === 'SYNCING') {
        setIsSyncing(true);
      }
    }).catch(() => {});

    // Periodic safety polling so UI never stays stuck
    const pollInterval = setInterval(async () => {
      try {
        const status = await api.getGmailStatus();
        if (status?.sync_state?.sync_status === 'COMPLETED' || status?.sync_state?.sync_status === 'FAILED') {
          setIsSyncing(false);
          setIsLoadingOlder(false);
          setSyncProgressMsg(null);
        }
      } catch {}
    }, 10000);

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';
    let eventSource: EventSource | null = null;
    try {
      eventSource = new EventSource(`${API_BASE_URL}/api/v1/events/stream`, {
        withCredentials: true,
      });

      eventSource.addEventListener('sync_started', () => {
        setIsSyncing(true);
        setSyncProgressMsg('Syncing mailbox...');
      });

      eventSource.addEventListener('sync_progress', (e: MessageEvent) => {
        setIsSyncing(true);
        try {
          const data = JSON.parse(e.data);
          setSyncProgressMsg(`Syncing email ${data.processed}/${data.limit}...`);
        } catch {}
      });

      eventSource.addEventListener('sync_completed', () => {
        setIsSyncing(false);
        setIsLoadingOlder(false);
        setSyncProgressMsg(null);
        fetchThreadsRef.current(threadLimitRef.current);
      });

      eventSource.onerror = () => {
        setIsSyncing(false);
        setIsLoadingOlder(false);
      };
    } catch {
      // ignore
    }

    return () => {
      clearInterval(pollInterval);
      if (eventSource) eventSource.close();
    };
  }, []);

  const handleLoadOlderEmails = async () => {
    if (isSyncing || isLoadingOlder) return;

    const newLimit = (threadLimitRef.current || threadLimit) + 50;
    setThreadLimit(newLimit);
    threadLimitRef.current = newLimit;

    setIsLoadingOlder(true);
    setIsSyncing(true);
    setSyncProgressMsg('Loading older emails...');

    const safetyTimer = setTimeout(() => {
      setIsLoadingOlder(false);
      setIsSyncing(false);
      setSyncProgressMsg(null);
      fetchThreadsRef.current(threadLimitRef.current);
    }, 7000);

    try {
      const res = await api.syncOlderEmails(50);
      await fetchThreadsRef.current(threadLimitRef.current);
      if (res?.status === 'IN_PROGRESS') {
        return;
      }
    } catch (err: any) {
      clearTimeout(safetyTimer);
      if (err?.status === 409 || err?.message?.includes('already in progress')) {
        setIsSyncing(true);
      } else if (err?.status === 404 || err?.message === 'Not Found') {
        toast.warning('Backend is updating. Please wait a moment and try again.');
        setIsLoadingOlder(false);
        setIsSyncing(false);
        setSyncProgressMsg(null);
      } else {
        toast.error(`Could not load older emails: ${err?.message || err}`);
        setIsLoadingOlder(false);
        setIsSyncing(false);
        setSyncProgressMsg(null);
      }
    }
  };

  const handleSelectMessage = async (msg: EmailMessageSummary, preserveDraftState: boolean = false) => {
    setSelectedMessage(msg);
    selectedMessageIdRef.current = msg.id;
    if (!preserveDraftState) {
      setAnalysis(null);
      setDraft(null);
      draftRef.current = null;
    }

    try {
      const existingAnalysis = await api.getMessageAnalysis(msg.id);
      setAnalysis(existingAnalysis);
    } catch {
      // Not analyzed yet
    }

    if (!preserveDraftState) {
      try {
        const drafts = await api.getReplyDraftsForMessage(msg.id);
        if (drafts.length > 0) {
          setDraft(drafts[0]);
          draftRef.current = drafts[0];
        }
      } catch {
        // No draft yet
      }
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
      toast.success('AI extractions completed!');
    } catch (err: any) {
      toast.error(`AI Extraction Error: ${err.message}`);
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
      toast.success(`Action status updated to ${newStatus}`);
    } catch (err: any) {
      toast.error(`Action Status Update Failed: ${err.message}`);
    }
  };

  const handleGenerateReply = async (tone: ToneEnum) => {
    if (!selectedMessage) return;
    try {
      setIsDrafting(true);
      const result = await api.generateReplyDraft(selectedMessage.id, tone);
      setDraft(result);
      draftRef.current = result;
      setActiveInspectorTab('COPILOT');
      if (!isInspectorOpen) setIsInspectorOpen(true);
      toast.success('AI reply draft generated!');
    } catch (err: any) {
      toast.error(`Reply Generation Error: ${err.message}`);
    } finally {
      setIsDrafting(false);
    }
  };

  const handleSaveDraftEdits = async (subject: string, bodyText: string, tone: ToneEnum) => {
    if (!draft) return;
    try {
      const updated = await api.updateReplyDraft(draft.id, { subject, body_text: bodyText, tone });
      setDraft(updated);
      draftRef.current = updated;
      toast.success('Draft changes saved!');
    } catch (err: any) {
      toast.error(`Draft Save Error: ${err.message}`);
    }
  };

  const handleSyncGmailDraft = async () => {
    if (!draft) return;
    try {
      setRequiresComposeConsent(false);
      const synced = await api.syncGmailDraft(draft.id);
      setDraft(synced);
      draftRef.current = synced;
      toast.success('Successfully synced draft to Gmail!');
    } catch (err: any) {
      if (err.status === 403) {
        setRequiresComposeConsent(true);
      } else {
        toast.error(`Gmail Sync Error: ${err.message}`);
      }
    }
  };

  const executeSendReplyEmail = async () => {
    if (!draft) return;
    try {
      setRequiresComposeConsent(false);
      const sent = await api.sendReplyEmail(draft.id);
      setDraft(sent);
      draftRef.current = sent;
      toast.success('Email successfully sent!');
    } catch (err: any) {
      if (err.status === 403) {
        setRequiresComposeConsent(true);
      } else {
        toast.error(`Email Send Error: ${err.message}`);
      }
    }
  };

  const handleSendReplyEmail = async () => {
    if (!draft) return;
    requestConfirmation({
      title: 'Approve & Send Email',
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

  // Superhuman-Style Keyboard Shortcuts Listener (j/k, r, a, x, ?)
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
    <div className="flex flex-col h-[calc(100vh-6.5rem)] font-sans">
      {/* Top Bar with View Controls, Hotkeys & Export */}
      <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3 mb-3.5 shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-white tracking-tight">
              Work Intelligence & AI Workspace
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-red-950/70 text-red-400 border border-red-800/70 uppercase tracking-wider font-semibold">
              Superhuman View
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Real-time thread navigator, distraction-free conversation reader, and Gemini AI copilot inspector.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowShortcutsModal(true)}
            className="text-xs bg-zinc-900/90 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-800 px-2.5 py-1.5 rounded-lg transition font-mono flex items-center gap-1.5 active:scale-95 shadow-sm"
            title="View keyboard hotkeys (?)"
          >
            <span>⌨️</span>
            <span className="hidden sm:inline">Hotkeys</span>
            <kbd className="text-[10px] bg-zinc-800 text-zinc-400 px-1 rounded border border-zinc-700/60">?</kbd>
          </button>

          <button
            onClick={handleOpenDigest}
            disabled={isExporting}
            className="flex items-center gap-1.5 text-xs bg-zinc-900/90 hover:bg-zinc-800 text-zinc-200 hover:text-red-400 border border-zinc-800 hover:border-red-900/60 px-3 py-1.5 rounded-lg transition font-medium active:scale-95 shadow-sm"
          >
            <span>📊</span>
            <span className="hidden sm:inline">Executive Digest</span>
          </button>

          <button
            onClick={() => setIsInspectorOpen(!isInspectorOpen)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition font-medium active:scale-95 shadow-sm ${
              isInspectorOpen
                ? 'bg-red-950/50 text-red-400 border-red-800/80'
                : 'bg-zinc-900/90 text-zinc-400 border-zinc-800 hover:text-white'
            }`}
          >
            {isInspectorOpen ? 'Hide AI Inspector (x)' : 'Show AI Inspector (x)'}
          </button>
        </div>
      </div>

      {/* 3-Pane Split Layout Grid */}
      <div className="flex-1 grid grid-cols-12 gap-3.5 min-h-0 overflow-hidden">
        {/* Pane 1: Left Thread Navigator (3 cols) */}
        <div className="col-span-12 md:col-span-4 lg:col-span-3 flex flex-col bg-zinc-950/90 border border-zinc-800/80 rounded-2xl overflow-hidden min-h-0 min-w-0 shadow-xl">
          {/* Search & Filter Header */}
          <div className="p-3 border-b border-zinc-800/80 space-y-2 bg-zinc-900/30">
            <div className="relative">
              <input
                type="text"
                placeholder="Search threads (sender, subject)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-zinc-900/90 border border-zinc-800 rounded-xl text-xs px-3 py-2 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500/80 focus:ring-1 focus:ring-red-500/30 transition"
              />
            </div>
            <div className="flex items-center gap-1 text-[10px]">
              {(['ALL', 'URGENT', 'ACTIONS'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setFilterMode(mode)}
                  className={`px-2.5 py-1 rounded-lg font-medium transition ${
                    filterMode === mode
                      ? 'bg-gradient-to-r from-red-600 to-rose-600 text-white font-semibold shadow-sm shadow-red-950/60'
                      : 'bg-zinc-900/80 text-zinc-400 hover:text-zinc-200 border border-zinc-800/80'
                  }`}
                >
                  {mode}
                </button>
              ))}
              <span className="ml-auto text-zinc-400 font-mono text-[11px] px-1.5 py-0.5 rounded bg-zinc-900/80 border border-zinc-800/60">
                {filteredThreads.length}
              </span>
            </div>
          </div>

          {/* Thread List */}
          <div className="flex-1 overflow-y-auto divide-y divide-zinc-800/40 p-1.5 space-y-1">
            {isLoadingThreads ? (
              <div className="text-xs text-zinc-500 py-16 text-center space-y-2">
                <span className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin inline-block"></span>
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
                      setSelectedThreadId(t.id);
                      selectedThreadIdRef.current = t.id;
                      if (t.messages.length > 0) handleSelectMessage(t.messages[0]);
                    }}
                    className={`thread-item-contain p-3 rounded-xl cursor-pointer transition-all duration-150 text-left border ${
                      isSelected
                        ? 'bg-zinc-900/90 border-l-[3px] border-l-red-500 border-t-zinc-800 border-r-zinc-800 border-b-zinc-800 shadow-md'
                        : 'bg-transparent border-transparent hover:bg-zinc-900/50 hover:border-zinc-800/80'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-zinc-200 truncate max-w-[150px]">
                        {firstMsg?.sender?.split('<')[0]?.trim() || 'Unknown'}
                      </span>
                      <span className="text-[10px] bg-zinc-800/80 text-zinc-400 px-1.5 py-0.5 rounded font-mono border border-zinc-700/50">
                        {t.messages.length} msg{t.messages.length > 1 ? 's' : ''}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-300 font-medium truncate">
                      {firstMsg?.subject || 'No Subject'}
                    </p>
                    <p className="text-[11px] text-zinc-400 truncate mt-1">
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
                  className={`w-full py-2 px-3 text-xs font-semibold rounded-xl border transition-all duration-150 flex items-center justify-center gap-2 shadow-sm ${
                    isSyncing || isLoadingOlder
                      ? 'border-zinc-800 bg-zinc-900/60 text-zinc-500 cursor-not-allowed'
                      : 'border-zinc-800 bg-zinc-900/90 hover:bg-zinc-800 text-zinc-300 hover:text-white active:scale-[0.98]'
                  }`}
                  title={isSyncing ? 'Mailbox synchronization in progress...' : 'Fetch older emails from your Gmail archive'}
                >
                  {isSyncing || isLoadingOlder ? (
                    <>
                      <span className="w-3 h-3 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></span>
                      <span>{syncProgressMsg || 'Syncing Mailbox...'}</span>
                    </>
                  ) : (
                    <span>↓ Load Older Emails (+50)</span>
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
          } flex flex-col bg-zinc-950/90 border border-zinc-800/80 rounded-2xl overflow-hidden min-h-0 min-w-0 shadow-xl`}
        >
          {selectedMessage ? (
            <div className="flex flex-col h-full min-h-0">
              {/* Message Header & Action Toolbar */}
              <div className="p-4 border-b border-zinc-800/80 bg-zinc-900/30 flex flex-wrap items-center justify-between gap-3 shrink-0">
                <div className="min-w-0">
                  <h3 className="text-sm font-bold text-white truncate tracking-tight">
                    {selectedMessage.subject || 'No Subject'}
                  </h3>
                  <div className="flex items-center gap-2 mt-1 text-xs text-zinc-400">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-red-600 to-rose-700 text-white border border-red-500/40 flex items-center justify-center font-bold text-[10px] shadow-sm select-none">
                      {selectedMessage.sender?.[0]?.toUpperCase() || 'U'}
                    </div>
                    <span className="truncate text-zinc-300 font-medium">{selectedMessage.sender}</span>
                    {selectedMessage.has_attachments && (
                      <span className="text-[10px] bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded-full border border-zinc-700/60 flex items-center gap-1">
                        <span>📎</span> Attachment
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={handleTriggerAnalysis}
                    disabled={isAnalyzing}
                    className="text-xs bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-semibold px-3 py-1.5 rounded-lg transition duration-150 disabled:opacity-50 shadow-md shadow-red-950/60 active:scale-95 flex items-center gap-1.5"
                    title="Run Gemini analysis (Hot-key: a)"
                  >
                    <span>✨</span>
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
                    className="text-xs bg-zinc-900 hover:bg-zinc-800 text-red-400 border border-red-900/50 hover:border-red-600 px-3 py-1.5 rounded-lg transition font-medium active:scale-95 flex items-center gap-1.5"
                    title="Open AI Copilot (Hot-key: r)"
                  >
                    <span>✍️</span>
                    <span>{isDrafting ? 'Drafting...' : 'Reply (r)'}</span>
                  </button>
                </div>
              </div>

              {/* Message Body Reader */}
              <div className="flex-1 p-5 overflow-y-auto space-y-4">
                {selectedMessage.attachments && selectedMessage.attachments.length > 0 && (
                  <div className="bg-zinc-900/60 p-3.5 rounded-xl border border-zinc-800/80 space-y-2">
                    <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider block">
                      Attachments ({selectedMessage.attachments.length})
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {selectedMessage.attachments.map((att) => (
                        <div
                          key={att.id}
                          className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-lg text-xs text-zinc-200"
                        >
                          <span>📄</span>
                          <span className="font-mono text-xs">{att.filename}</span>
                          <span className="text-[10px] text-zinc-400">
                            ({Math.round(att.size_bytes / 1024)} KB)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="bg-zinc-900/40 p-5 rounded-xl border border-zinc-800/80 text-xs text-zinc-200 leading-relaxed font-sans whitespace-pre-wrap break-words overflow-x-hidden shadow-inner">
                  {selectedMessage.body_plain || 'No body text.'}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-xs text-zinc-500 p-8 text-center space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-2xl text-zinc-600">
                📬
              </div>
              <p className="text-zinc-400">Select an email thread from the left or press <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono">j</kbd> / <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono">k</kbd> to navigate.</p>
              <button
                onClick={async () => {
                  try {
                    await api.seedDemoData();
                    fetchThreads(threadLimitRef.current);
                  } catch {}
                }}
                className="text-xs bg-red-950/40 hover:bg-red-900/60 text-red-400 border border-red-800/60 px-3.5 py-1.5 rounded-lg transition"
              >
                ⚡ Load Sample Enterprise Mailbox
              </button>
            </div>
          )}
        </div>

        {/* Pane 3: Right Collapsible AI Work Intelligence Inspector & Copilot */}
        {isInspectorOpen && (
          <div className="col-span-12 lg:col-span-4 flex flex-col bg-zinc-950/90 border border-zinc-800/80 rounded-2xl overflow-hidden min-h-0 min-w-0 shadow-xl">
            {/* Inspector Tab Selector */}
            <div className="p-2.5 border-b border-zinc-800/80 flex items-center justify-between bg-zinc-900/30 shrink-0">
              <div className="flex items-center gap-1 bg-zinc-900/90 p-1 rounded-xl border border-zinc-800/80">
                <button
                  onClick={() => setActiveInspectorTab('INTELLIGENCE')}
                  className={`text-xs px-3 py-1.5 rounded-lg font-medium transition ${
                    activeInspectorTab === 'INTELLIGENCE'
                      ? 'bg-red-950/70 text-red-400 border border-red-800/80 shadow-sm font-semibold'
                      : 'text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  ⚡ Intelligence
                </button>
                <button
                  onClick={() => setActiveInspectorTab('COPILOT')}
                  className={`text-xs px-3 py-1.5 rounded-lg font-medium transition ${
                    activeInspectorTab === 'COPILOT'
                      ? 'bg-red-950/70 text-red-400 border border-red-800/80 shadow-sm font-semibold'
                      : 'text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  🤖 Copilot Reply
                </button>
              </div>

              <button
                onClick={() => setIsInspectorOpen(false)}
                title="Collapse Inspector (x)"
                className="text-zinc-400 hover:text-white text-xs px-2.5 py-1.5 rounded-lg hover:bg-zinc-900 border border-transparent hover:border-zinc-800 transition font-mono"
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
                  <div className="text-center py-16 text-zinc-500 text-xs space-y-4">
                    <div className="w-12 h-12 rounded-2xl bg-zinc-900/80 border border-zinc-800/80 flex items-center justify-center text-2xl mx-auto text-zinc-600">
                      ⚡
                    </div>
                    <p className="text-zinc-400">No AI intelligence extraction generated for this email yet.</p>
                    <button
                      onClick={handleTriggerAnalysis}
                      disabled={isAnalyzing}
                      className="text-xs bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-medium px-4 py-2 rounded-xl transition disabled:opacity-50 shadow-lg shadow-red-950/60 active:scale-95"
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

      {/* Keyboard Shortcuts Modal */}
      {showShortcutsModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-950 border border-zinc-800 rounded-2xl max-w-md w-full p-5 shadow-2xl space-y-4 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
              <div className="flex items-center gap-2">
                <span className="text-base text-red-400">⌨️</span>
                <h3 className="text-sm font-bold text-white tracking-tight">Superhuman Keyboard Shortcuts</h3>
              </div>
              <button
                onClick={() => setShowShortcutsModal(false)}
                className="text-zinc-400 hover:text-white text-xs px-2 py-1 rounded-lg hover:bg-zinc-900 transition"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-300">Navigate down threads</span>
                <kbd className="bg-zinc-800 text-red-400 font-mono px-2 py-0.5 rounded border border-zinc-700">j</kbd>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-300">Navigate up threads</span>
                <kbd className="bg-zinc-800 text-red-400 font-mono px-2 py-0.5 rounded border border-zinc-700">k</kbd>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-300">Run Gemini AI analysis</span>
                <kbd className="bg-zinc-800 text-red-400 font-mono px-2 py-0.5 rounded border border-zinc-700">a</kbd>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-300">Focus AI Copilot Reply</span>
                <kbd className="bg-zinc-800 text-red-400 font-mono px-2 py-0.5 rounded border border-zinc-700">r</kbd>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-300">Toggle AI Inspector pane</span>
                <kbd className="bg-zinc-800 text-red-400 font-mono px-2 py-0.5 rounded border border-zinc-700">x</kbd>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-300">Open Command Palette</span>
                <kbd className="bg-zinc-800 text-red-400 font-mono px-2 py-0.5 rounded border border-zinc-700">Ctrl+K</kbd>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-300">Accept ghost autocomplete</span>
                <kbd className="bg-zinc-800 text-red-400 font-mono px-2 py-0.5 rounded border border-zinc-700">Tab</kbd>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-300">Show keyboard shortcuts</span>
                <kbd className="bg-zinc-800 text-red-400 font-mono px-2 py-0.5 rounded border border-zinc-700">?</kbd>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Executive Digest Modal */}
      {showDigestModal && digestSummary && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-950 border border-zinc-800/90 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-fadeIn">
            <div className="p-4 border-b border-zinc-800/80 flex items-center justify-between bg-zinc-900/30">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>Executive Intelligence Digest</span>
                  <span className="text-[10px] bg-red-950/70 text-red-400 border border-red-800/70 px-2 py-0.5 rounded font-mono font-semibold">
                    REPORT
                  </span>
                </h3>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Aggregated cross-mailbox KPIs, action item tracking, and strategic risk registry.
                </p>
              </div>
              <button
                onClick={() => setShowDigestModal(false)}
                className="text-zinc-400 hover:text-white text-sm px-2 py-1 rounded-lg hover:bg-zinc-900 transition"
              >
                ✕
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-5 text-xs text-zinc-300">
              {/* Metric KPI Tiles */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-zinc-900/70 p-3.5 rounded-xl border border-zinc-800/80">
                  <span className="text-[10px] text-zinc-400 uppercase font-semibold">Analyzed Emails</span>
                  <p className="text-lg font-bold text-white mt-1 font-mono">{digestSummary.total_emails_analyzed}</p>
                </div>
                <div className="bg-zinc-900/70 p-3.5 rounded-xl border border-zinc-800/80">
                  <span className="text-[10px] text-zinc-400 uppercase font-semibold">Pending Actions</span>
                  <p className="text-lg font-bold text-red-400 mt-1 font-mono">{digestSummary.pending_actions}</p>
                </div>
                <div className="bg-zinc-900/70 p-3.5 rounded-xl border border-zinc-800/80">
                  <span className="text-[10px] text-zinc-400 uppercase font-semibold">High Risks</span>
                  <p className="text-lg font-bold text-rose-500 mt-1 font-mono">{digestSummary.high_severity_risks}</p>
                </div>
                <div className="bg-zinc-900/70 p-3.5 rounded-xl border border-zinc-800/80">
                  <span className="text-[10px] text-zinc-400 uppercase font-semibold">Financial Total</span>
                  <p className="text-lg font-bold text-white mt-1 font-mono">
                    ${digestSummary.total_financial_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </p>
                </div>
              </div>

              {/* Priority Actions */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-zinc-200 uppercase tracking-wider">Priority Action Items</h4>
                {digestSummary.top_actions?.length > 0 ? (
                  <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                    {digestSummary.top_actions.map((act: any) => (
                      <div key={act.id} className="p-2.5 rounded-xl bg-zinc-900/70 border border-zinc-800/80 flex items-center justify-between">
                        <div className="truncate max-w-[70%]">
                          <span className="font-semibold text-white block truncate">{act.description}</span>
                          <span className="text-[10px] text-zinc-400">
                            {act.assignee ? `Assigned to: ${act.assignee}` : 'Unassigned'}
                            {act.due_date ? ` • Due: ${act.due_date.split('T')[0]}` : ''}
                          </span>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-red-950/60 text-red-400 border border-red-800/60">
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
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-zinc-200 uppercase tracking-wider">Active Business Risks</h4>
                {digestSummary.active_risks?.length > 0 ? (
                  <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                    {digestSummary.active_risks.map((risk: any) => (
                      <div key={risk.id} className="p-2.5 rounded-xl bg-zinc-900/70 border border-zinc-800/80 flex items-center justify-between">
                        <span className="font-medium text-white truncate max-w-[75%]">{risk.description}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-red-950/80 text-rose-400 border border-red-800/80">
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
            <div className="p-4 border-t border-zinc-800/80 bg-zinc-900/30 flex items-center justify-between">
              <span className="text-xs text-zinc-400">Download formatted export:</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownloadExport('csv')}
                  className="text-xs bg-zinc-900 hover:bg-zinc-850 text-zinc-200 px-3 py-1.5 rounded-lg border border-zinc-800 transition font-medium"
                >
                  📥 Export CSV
                </button>
                <button
                  onClick={() => handleDownloadExport('markdown')}
                  className="text-xs bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white px-3.5 py-1.5 rounded-lg transition font-medium shadow-md shadow-red-950/50"
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
