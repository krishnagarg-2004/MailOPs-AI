import React, { useEffect, useRef, useState } from 'react';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
  const [statusData, setStatusData] = useState<GmailStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
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

    const interval = setInterval(fetchStatus, 5000);

    return () => clearInterval(interval);
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
        let msg = `Sync rejected (HTTP ${resp.status}).`;
        try {
          const detail = await resp.json();
          msg = detail.detail || detail.message || msg;
        } catch {
          try {
            msg = await resp.text();
          } catch { /* keep default */ }
        }
        alert(msg);
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
      alert(`Sync attempt failed: ${err?.message || 'Network error'}`);
    } finally {
      // Only unset isSyncing if this is still the latest controller.
      if (syncAbortControllerRef.current === controller) {
        setIsSyncing(false);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="text-xs text-slate-400">
        Loading Gmail status...
      </div>
    );
  }

  if (!statusData?.connected) {
    return (
      <div className="w-full rounded-xl border border-slate-800 bg-slate-900 p-3 text-slate-100 shadow-sm">
        <h3 className="text-sm font-bold text-sky-400">
          Gmail Connection
        </h3>

        <p className="mt-2 text-[11px] leading-relaxed text-slate-400">
          No Gmail account connected. Please sign in with Google to enable
          email sync.
        </p>
      </div>
    );
  }

  const syncState = statusData.sync_state;

  return (
    <div className="w-full rounded-xl border border-slate-800 bg-slate-900 p-3 text-slate-100 shadow-sm">

      {/* Header */}
      <div className="mb-3">
        <h3 className="text-sm font-bold text-sky-400">
          Gmail Synchronization
        </h3>

        <p
          className="mt-1 truncate text-[11px] text-slate-400"
          title={statusData.email || ''}
        >
          {statusData.email || 'Gmail account'}
        </p>
      </div>

      {/* Sync Information */}
      <div className="grid grid-cols-2 gap-2 rounded-lg bg-slate-950 p-2.5">

        {/* Status */}
        <div className="min-w-0">
          <span className="block text-[9px] font-semibold uppercase tracking-wider text-slate-500">
            Status
          </span>

          <div
            className={`mt-1 truncate text-[11px] font-bold ${syncState?.sync_status === 'COMPLETED'
                ? 'text-green-400'
                : syncState?.sync_status === 'FAILED'
                  ? 'text-red-400'
                  : 'text-yellow-400'
              }`}
          >
            {syncState?.sync_status || 'IDLE'}
          </div>
        </div>

        {/* Messages */}
        <div className="min-w-0">
          <span className="block text-[9px] font-semibold uppercase tracking-wider text-slate-500">
            Messages
          </span>

          <div className="mt-1 text-sm font-bold text-slate-100">
            {syncState?.synced_message_count || 0}
          </div>
        </div>

        {/* Last Synced */}
        <div className="col-span-2 border-t border-slate-800 pt-2">
          <span className="block text-[9px] font-semibold uppercase tracking-wider text-slate-500">
            Last Synced
          </span>

          <div className="mt-1 truncate text-[11px] text-slate-300">
            {syncState?.last_synced_at
              ? new Date(syncState.last_synced_at).toLocaleTimeString()
              : 'Never'}
          </div>
        </div>
      </div>

      {/* Sync Button */}
      <button
        onClick={triggerSync}
        disabled={isSyncing}
        className={`mt-3 w-full rounded-lg px-3 py-2 text-xs font-semibold text-white transition ${isSyncing
            ? 'cursor-not-allowed bg-slate-700'
            : 'bg-indigo-600 hover:bg-indigo-500'
          }`}
      >
        {isSyncing ? 'Syncing...' : 'Sync Inbox'}
      </button>

      {/* Error */}
      {syncState?.error_message && (
        <div className="mt-2 rounded-lg border border-red-900/50 bg-red-950/40 p-2 text-[10px] leading-relaxed text-red-300">
          {syncState.error_message}
        </div>
      )}
    </div>
  );
};