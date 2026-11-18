import React, { useEffect, useRef, useState } from 'react';
import { useToast } from '../context/ToastContext';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

interface SyncState {
  sync_status: string;
  last_synced_at: string | null;
  synced_message_count: number;
  error_message: string | null;
}

interface GmailStatus {
  connected: boolean;
  email: string | null;
  sync_state: SyncState | null;
}

export const GmailSyncWidget: React.FC = () => {
  const { toast } = useToast();
  const [statusData, setStatusData] = useState<GmailStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [isLoadingOlder, setIsLoadingOlder] = useState<boolean>(false);
  const [liveEventMessage, setLiveEventMessage] = useState<string | null>(null);
  const syncAbortControllerRef = useRef<AbortController | null>(null);

  const fetchStatus = async () => {
    try {
      const resp = await fetch(`${API_BASE_URL}/api/v1/gmail/status`, {
        credentials: 'include',
      });

      if (resp.ok) {
        const data: GmailStatus = await resp.json();
        setStatusData(data);

        if (data.sync_state?.sync_status === 'SYNCING') {
          setIsSyncing(true);
        } else {
          setIsSyncing(false);
        }
      }
    } catch {
      // Ignore background errors
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();

    // Connect to live Server-Sent Events (SSE) stream
    let eventSource: EventSource | null = null;
    try {
      eventSource = new EventSource(`${API_BASE_URL}/api/v1/events/stream`, {
        withCredentials: true,
      });

      eventSource.addEventListener('sync_started', () => {
        setIsSyncing(true);
        setLiveEventMessage('Sync started...');
      });

      eventSource.addEventListener('sync_progress', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          setLiveEventMessage(`Syncing email ${data.processed}/${data.limit}...`);
        } catch {
          // ignore parse errors
        }
      });

      eventSource.addEventListener('sync_completed', () => {
        setIsSyncing(false);
        setLiveEventMessage('Sync completed successfully.');
        fetchStatus();
        setTimeout(() => setLiveEventMessage(null), 4000);
      });

      eventSource.onerror = () => {
        // SSE disconnected or closed
      };
    } catch {
      // EventSource not supported
    }

    const interval = setInterval(fetchStatus, 15000);

    return () => {
      clearInterval(interval);
      if (eventSource) {
        eventSource.close();
      }
    };
  }, []);

  const triggerSync = async () => {
    const controller = new AbortController();
    syncAbortControllerRef.current = controller;

    try {
      setIsSyncing(true);

      const resp = await fetch(`${API_BASE_URL}/api/v1/gmail/sync`, {
        method: 'POST',
        credentials: 'include',
        signal: controller.signal,
      });

      if (!resp.ok) {
        if (resp.status === 409) {
          setIsSyncing(true);
          return;
        }
        let msg = `Sync rejected (HTTP ${resp.status}).`;
        try {
          const detail = await resp.json();
          msg = detail.detail || detail.message || msg;
        } catch {
          try {
            msg = await resp.text();
          } catch { /* keep default */ }
        }
        toast.error(msg);
        return;
      }

      fetchStatus();
    } catch (err: any) {
      setIsSyncing(false);
      if (err?.name === 'AbortError') return;
      toast.error(`Sync attempt failed: ${err?.message || 'Network error'}`);
    } finally {
      if (syncAbortControllerRef.current === controller) {
        setIsSyncing(false);
      }
    }
  };

  const triggerSyncOlder = async () => {
    try {
      setIsLoadingOlder(true);
      const resp = await fetch(`${API_BASE_URL}/api/v1/gmail/sync-older?count=50`, {
        method: 'POST',
        credentials: 'include',
      });

      if (!resp.ok) {
        if (resp.status === 409) {
          setIsSyncing(true);
          return;
        }
        let msg = `Request failed (HTTP ${resp.status}).`;
        if (resp.status === 404) {
          msg = 'Backend is updating. Please try again in a few moments.';
        } else {
          try {
            const detail = await resp.json();
            msg = detail.detail || detail.message || msg;
          } catch { /* ignore */ }
        }
        toast.error(msg);
        return;
      }
      fetchStatus();
    } catch (err: any) {
      toast.error(`Failed to load older emails: ${err?.message || 'Network error'}`);
    } finally {
      setIsLoadingOlder(false);
    }
  };

  if (isLoading) {
    return (
      <div className="w-full rounded-xl border border-zinc-800/80 bg-zinc-950 p-3.5 text-xs text-zinc-400 animate-pulse">
        <div className="h-3.5 bg-zinc-800 rounded w-2/3 mb-2"></div>
        <div className="h-2.5 bg-zinc-800/60 rounded w-1/2"></div>
      </div>
    );
  }

  if (!statusData?.connected) {
    return (
      <div className="w-full rounded-xl border border-zinc-800/80 bg-zinc-950 p-3.5 text-zinc-100 shadow-sm">
        <h3 className="text-xs font-bold text-white flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-zinc-600"></span>
          Gmail Connection
        </h3>
        <p className="mt-2 text-[11px] leading-relaxed text-zinc-400">
          No Gmail account connected. Sign in with Google to enable mailbox synchronization.
        </p>
      </div>
    );
  }

  const syncState = statusData.sync_state;
  const isFailed = syncState?.sync_status === 'FAILED';
  const isSuccess = syncState?.sync_status === 'COMPLETED';

  return (
    <div className="w-full rounded-xl border border-zinc-800/80 bg-gradient-to-b from-zinc-900/40 to-zinc-950/80 p-3.5 text-zinc-100 shadow-sm backdrop-blur-sm">
      {/* Header */}
      <div className="mb-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-white flex items-center gap-1.5 tracking-tight">
            <span>Gmail Synchronization</span>
          </h3>
          <span
            className={`w-2 h-2 rounded-full transition-all duration-300 ${
              isSyncing || isLoadingOlder
                ? 'bg-amber-400 animate-pulse'
                : isSuccess
                ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]'
                : isFailed
                ? 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]'
                : 'bg-zinc-600'
            }`}
            title={`Status: ${syncState?.sync_status || 'IDLE'}`}
          />
        </div>

        <p
          className="mt-1 truncate text-[11px] text-zinc-400 font-mono"
          title={statusData.email || ''}
        >
          {statusData.email || 'Gmail account'}
        </p>
      </div>

      {/* Sync Information Card */}
      <div className="rounded-lg bg-black/60 border border-zinc-800/80 p-2.5 space-y-2">
        {/* Live SSE Notification Toast */}
        {liveEventMessage && (
          <div className="flex items-center gap-2 rounded bg-red-950/70 border border-red-800/80 px-2 py-1 text-[10px] text-red-200">
            <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-ping shrink-0" />
            <span className="truncate">{liveEventMessage}</span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-2">
          {/* Status */}
          <div className="min-w-0">
            <span className="block text-[9px] font-semibold uppercase tracking-wider text-zinc-400">
              Status
            </span>
            <div
              className={`mt-0.5 truncate text-[11px] font-bold ${
                isSuccess
                  ? 'text-emerald-400'
                  : isFailed
                  ? 'text-rose-400'
                  : isSyncing
                  ? 'text-amber-400'
                  : 'text-zinc-300'
              }`}
            >
              {isSyncing ? 'SYNCING' : syncState?.sync_status || 'IDLE'}
            </div>
          </div>

          {/* Messages */}
          <div className="min-w-0 text-right">
            <span className="block text-[9px] font-semibold uppercase tracking-wider text-zinc-400">
              Messages
            </span>
            <div className="mt-0.5 text-xs font-bold text-white font-mono">
              {syncState?.synced_message_count || 0}
            </div>
          </div>

          {/* Last Synced */}
          <div className="col-span-2 border-t border-zinc-800/80 pt-1.5 flex items-center justify-between">
            <span className="text-[9px] font-semibold uppercase tracking-wider text-zinc-400">
              Last Synced
            </span>
            <span className="text-[10px] font-mono text-zinc-300">
              {syncState?.last_synced_at
                ? new Date(syncState.last_synced_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                : 'Never'}
            </span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-3 flex flex-col gap-1.5">
        <button
          onClick={triggerSync}
          disabled={isSyncing || isLoadingOlder}
          className={`w-full rounded-lg px-3 py-2 text-xs font-semibold text-white transition duration-150 flex items-center justify-center gap-1.5 shadow-md ${
            isSyncing
              ? 'cursor-not-allowed bg-zinc-800 text-zinc-500'
              : 'bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 shadow-red-950/60 active:scale-[0.98]'
          }`}
        >
          {isSyncing ? (
            <>
              <span className="w-3 h-3 border-2 border-zinc-400 border-t-transparent rounded-full animate-spin"></span>
              <span>Syncing Inbox...</span>
            </>
          ) : (
            <span>Sync Inbox</span>
          )}
        </button>

        <button
          onClick={triggerSyncOlder}
          disabled={isSyncing || isLoadingOlder}
          className={`w-full rounded-lg px-3 py-1.5 text-xs font-medium border border-zinc-800 bg-zinc-900/90 hover:bg-zinc-800 text-zinc-300 hover:text-white transition duration-150 flex items-center justify-center gap-1.5 ${
            isLoadingOlder ? 'cursor-not-allowed text-zinc-500' : 'active:scale-[0.98]'
          }`}
          title="Fetch the next batch of 50 older emails from your Gmail archive"
        >
          {isLoadingOlder ? (
            <>
              <span className="w-2.5 h-2.5 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></span>
              <span>Loading Older...</span>
            </>
          ) : (
            <span>↓ Load Older Emails (+50)</span>
          )}
        </button>
      </div>

      {/* Error Message Pill */}
      {syncState?.error_message && isFailed && (
        <div className="mt-2.5 rounded-lg border border-red-900/60 bg-red-950/40 p-2 text-[10px] leading-relaxed text-red-300">
          {syncState.error_message}
        </div>
      )}
    </div>
  );
};
