import React, { useEffect, useRef, useState } from 'react';
import { useToast } from '../context/ToastContext';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? '';

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
  // AbortController so two rapid clicks don't both fire the background sync.
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
      // EventSource not supported or blocked
    }

    // Fallback polling interval every 15 seconds (reduced from 5s since SSE is active)
    const interval = setInterval(fetchStatus, 15000);

    return () => {
      clearInterval(interval);
      if (eventSource) {
        eventSource.close();
      }
    };
  }, []);

  const triggerSync = async () => {
    // Abort previous in-flight sync so two rapid clicks don't both fire.
    const controller = new AbortController();
    syncAbortControllerRef.current = controller;

    try {
      setIsSyncing(true);

      const resp = await fetch(`${API_BASE_URL}/api/v1/gmail/sync`, {
        method: 'POST',
        credentials: 'include',
        signal: controller.signal,
      });

      // Surface non-success responses so the user knows WHY the sync was rejected
      // (e.g. no OAuth account, another sync already running, server error).
      // Note: fetch() only rejects on network failure, NOT on HTTP error status.
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
      // Network-level failure (offline, DNS, aborted)
      setIsSyncing(false);
      if (err?.name === 'AbortError') {
        // A newer sync superseded this one — ignore silently.
        return;
      }
      toast.error(`Sync attempt failed: ${err?.message || 'Network error'}`);
    } finally {
      // Only unset isSyncing if this is still the latest controller.
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
          msg = 'Backend is finishing deployment on Render. Please try again in 10-20 seconds.';
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
      <div className="text-xs text-zinc-400">
        Loading Gmail status...
      </div>
    );
  }

  if (!statusData?.connected) {
    return (
      <div className="w-full rounded-xl border border-zinc-800 bg-zinc-950 p-3 text-zinc-100 shadow-sm">
        <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-zinc-600"></span>
          Gmail Connection
        </h3>

        <p className="mt-2 text-[11px] leading-relaxed text-zinc-400">
          No Gmail account connected. Please sign in with Google to enable
          email sync.
        </p>
      </div>
    );
  }

  const syncState = statusData.sync_state;

  return (
    <div className="w-full rounded-xl border border-zinc-800 bg-zinc-950 p-3 text-zinc-100 shadow-sm">

      {/* Header */}
      <div className="mb-3">
        <h3 className="text-xs font-bold text-white flex items-center justify-between">
          <span>Gmail Synchronization</span>
          <span className={`w-2 h-2 rounded-full ${syncState?.sync_status === 'COMPLETED' ? 'bg-red-500 shadow-sm shadow-red-500/80' : 'bg-zinc-600'}`}></span>
        </h3>

        <p
          className="mt-1 truncate text-[11px] text-zinc-400 font-mono"
          title={statusData.email || ''}
        >
          {statusData.email || 'Gmail account'}
        </p>
      </div>

      {/* Sync Information */}
      <div className="grid grid-cols-2 gap-2 rounded-lg bg-zinc-900 border border-zinc-800/60 p-2.5">

        {/* Live SSE Notification Toast */}
        {liveEventMessage && (
          <div className="col-span-2 mb-1 flex items-center gap-1.5 rounded bg-red-950/60 border border-red-800/80 px-2 py-1 text-[10px] text-red-300">
            <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-ping"></span>
            <span className="truncate">{liveEventMessage}</span>
          </div>
        )}

        {/* Status */}
        <div className="min-w-0">
          <span className="block text-[9px] font-semibold uppercase tracking-wider text-zinc-500">
            Status
          </span>

          <div
            className={`mt-1 truncate text-[11px] font-bold ${syncState?.sync_status === 'COMPLETED'
                ? 'text-red-400'
                : syncState?.sync_status === 'FAILED'
                  ? 'text-red-500 font-extrabold'
                  : 'text-zinc-400'
              }`}
          >
            {syncState?.sync_status || 'IDLE'}
          </div>
        </div>

        {/* Messages */}
        <div className="min-w-0">
          <span className="block text-[9px] font-semibold uppercase tracking-wider text-zinc-500">
            Messages
          </span>

          <div className="mt-1 text-sm font-bold text-white">
            {syncState?.synced_message_count || 0}
          </div>
        </div>

        {/* Last Synced */}
        <div className="col-span-2 border-t border-zinc-800 pt-2">
          <span className="block text-[9px] font-semibold uppercase tracking-wider text-zinc-500">
            Last Synced
          </span>

          <div className="mt-1 truncate text-[11px] text-zinc-300">
            {syncState?.last_synced_at
              ? new Date(syncState.last_synced_at).toLocaleTimeString()
              : 'Never'}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-3 flex flex-col gap-1.5">
        <button
          onClick={triggerSync}
          disabled={isSyncing || isLoadingOlder}
          className={`w-full rounded-lg px-3 py-2 text-xs font-semibold text-white transition ${
            isSyncing
              ? 'cursor-not-allowed bg-zinc-800 text-zinc-500'
              : 'bg-red-600 hover:bg-red-500 shadow-md shadow-red-950/50 active:scale-[0.98]'
          }`}
        >
          {isSyncing ? 'Syncing Inbox...' : 'Sync Inbox'}
        </button>

        <button
          onClick={triggerSyncOlder}
          disabled={isSyncing || isLoadingOlder}
          className={`w-full rounded-lg px-3 py-1.5 text-xs font-medium border border-zinc-800 bg-zinc-900/90 hover:bg-zinc-800 text-zinc-300 hover:text-white transition flex items-center justify-center gap-1.5 ${
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
            <>
              <span>↓ Load Older Emails (+50)</span>
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {syncState?.error_message && syncState?.sync_status === 'FAILED' && (
        <div className="mt-2 rounded-lg border border-red-900/50 bg-red-950/40 p-2 text-[10px] leading-relaxed text-red-300">
          {syncState.error_message}
        </div>
      )}
    </div>
  );
};