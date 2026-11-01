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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100">Inbox & AI Reply Workspace</h2>
          <p className="text-xs text-slate-400">
            Browser synced email threads, trigger Gemini intelligence extractions, review action items, and draft replies.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Email Thread Browser */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Email Threads ({threads.length})
          </h3>

          {isLoadingThreads ? (
            <div className="text-xs text-slate-500 py-8 text-center">Loading mailbox threads...</div>
          ) : threads.length === 0 ? (
            <div className="text-xs text-slate-500 py-8 text-center">No email threads synced yet. Click <strong>Sync Inbox</strong> above.</div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {threads.map((t) => (
                <div
                  key={t.id}
                  onClick={() => {
                    setSelectedThread(t);
                    if (t.messages.length > 0) handleSelectMessage(t.messages[0]);
                  }}
                  className={`p-3 rounded-lg border cursor-pointer transition ${selectedThread?.id === t.id
                    ? 'bg-slate-800 border-indigo-500/50'
                    : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                    }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-200 truncate max-w-[180px]">
                      {t.messages[0]?.sender || 'Unknown Sender'}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {t.messages.length} msg{t.messages.length > 1 ? 's' : ''}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 font-medium truncate">
                    {t.messages[0]?.subject || 'No Subject'}
                  </p>
                  <p className="text-[11px] text-slate-500 truncate mt-0.5">
                    {t.snippet}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column (2 Spans): Message Inspection & AI Workspace */}
        <div className="lg:col-span-2 space-y-6">
          {selectedMessage ? (
            <>
              {/* Selected Email Message Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-base font-bold text-slate-100">{selectedMessage.subject}</h3>
                    <p className="text-xs text-slate-400 mt-0.5">From: {selectedMessage.sender}</p>
                  </div>
                  <button
                    onClick={handleTriggerAnalysis}
                    disabled={isAnalyzing}
                    className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-3 py-1.5 rounded-lg transition disabled:opacity-50"
                  >
                    {isAnalyzing ? 'Extracting...' : 'Analyze with Gemini'}
                  </button>
                </div>

                <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
                  {selectedMessage.body_plain || 'No body text.'}
                </div>
              </div>

              {/* AI Extraction Analysis Component */}
              {analysis && (
                <EmailAnalysisCard
                  analysis={analysis}
                  onActionStatusChange={handleActionStatusChange}
                />
              )}

              {/* Human-in-the-Loop Reply Draft Component */}
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
            </>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-xs text-slate-500">
              Select an email message from the inbox list to inspect content and run AI intelligence.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
