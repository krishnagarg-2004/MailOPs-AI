import React, { useEffect, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
    try {
      setIsSyncing(true);
      await fetch(`${API_BASE_URL}/api/v1/gmail/sync`, {
        method: 'POST',
        credentials: 'include',
      });
      fetchStatus();
    } catch {
      setIsSyncing(false);
    }
  };

  if (isLoading) {
    return <div style={{ color: '#94a3b8' }}>Loading Gmail status...</div>;
  }

  if (!statusData?.connected) {
    return (
      <div style={{ padding: '1rem', backgroundColor: '#1e293b', borderRadius: '0.5rem', color: '#f8fafc' }}>
        <h3 style={{ margin: '0 0 0.5rem 0', color: '#f1f5f9' }}>Gmail Connection</h3>
        <p style={{ margin: 0, color: '#94a3b8' }}>No Gmail account connected. Please sign in with Google to enable email sync.</p>
      </div>
    );
  }

  const syncState = statusData.sync_state;

  return (
    <div style={{ padding: '1.25rem', backgroundColor: '#1e293b', borderRadius: '0.5rem', color: '#f8fafc', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#38bdf8' }}>Gmail Synchronization</h3>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#94a3b8' }}>Connected as: {statusData.email}</p>
        </div>
        <button
          onClick={triggerSync}
          disabled={isSyncing}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: isSyncing ? '#475569' : '#2563eb',
            color: '#ffffff',
            fontWeight: '600',
            borderRadius: '0.375rem',
            border: 'none',
            cursor: isSyncing ? 'not-allowed' : 'pointer',
          }}
        >
          {isSyncing ? 'Syncing...' : 'Sync Inbox'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', backgroundColor: '#0f172a', padding: '0.75rem', borderRadius: '0.375rem' }}>
        <div>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Status</span>
          <div style={{ fontWeight: '600', color: syncState?.sync_status === 'COMPLETED' ? '#4ade80' : syncState?.sync_status === 'FAILED' ? '#f87171' : '#facc15' }}>
            {syncState?.sync_status || 'IDLE'}
          </div>
        </div>
        <div>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Synced Messages</span>
          <div style={{ fontWeight: '600', color: '#f8fafc' }}>{syncState?.synced_message_count || 0}</div>
        </div>
        <div>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Last Synced</span>
          <div style={{ fontSize: '0.875rem', color: '#cbd5e1' }}>
            {syncState?.last_synced_at ? new Date(syncState.last_synced_at).toLocaleTimeString() : 'Never'}
          </div>
        </div>
      </div>

      {syncState?.error_message && (
        <div style={{ marginTop: '0.75rem', padding: '0.5rem', backgroundColor: '#450a0a', color: '#fca5a5', borderRadius: '0.25rem', fontSize: '0.875rem' }}>
          Error: {syncState.error_message}
        </div>
      )}
    </div>
  );
};
