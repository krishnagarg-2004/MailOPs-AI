import React, { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { api } from '../services/api';
import { GmailSyncWidget } from './GmailSyncWidget';
import { CommandPalette } from './CommandPalette';

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const { toast, requestConfirmation } = useToast();
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const navItems = [
    { path: '/dashboard', label: 'Inbox & AI Reply', icon: '📬' },
    { path: '/documents', label: 'Document OCR', icon: '📄' },
    { path: '/search', label: 'Search & RAG Chat', icon: '🔍' },
    { path: '/graph', label: 'Action Graph', icon: '⚙️' },
  ];

  return (
    <div className="min-h-screen bg-black text-zinc-100 font-sans flex flex-col">
      {/* Top Glassmorphic Navigation Header */}
      <header className="h-16 glass-header border-b border-zinc-800/80 px-4 md:px-6 flex items-center justify-between shrink-0 sticky top-0 z-40 transition-all">
        {/* Brand & Sidebar Toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-900 border border-transparent hover:border-zinc-800 transition active:scale-95"
            title={isSidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            aria-label="Toggle Navigation Sidebar"
          >
            <span className="text-base select-none">{isSidebarCollapsed ? '☰' : '◀'}</span>
          </button>

          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-red-600 via-rose-600 to-red-500 flex items-center justify-center font-extrabold text-white text-sm shadow-md shadow-red-950/60 border border-red-400/40 select-none">
            M
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-base font-bold tracking-tight text-white">MailOps</span>
              <span className="text-[10px] font-bold text-red-400 px-1.5 py-0.5 rounded bg-red-950/80 border border-red-800/70 tracking-wider">
                AI
              </span>
            </div>
            <span className="text-[10px] text-zinc-400 tracking-wider font-medium hidden sm:block">
              Work Intelligence Engine
            </span>
          </div>
        </div>

        {/* Global Controls & User Info */}
        <div className="flex items-center gap-2 md:gap-3">
          <button
            onClick={() => {
              requestConfirmation({
                title: 'Seed Enterprise Demo Data',
                message: 'Populate mailbox with simulated customer escalations, supplier invoices, and graph dependencies?',
                confirmLabel: 'Load Demo Data',
                onConfirm: async () => {
                  try {
                    const res = await api.seedDemoData();
                    toast.success(res.message || 'Demo data successfully loaded!');
                    setTimeout(() => window.location.reload(), 600);
                  } catch (e: any) {
                    toast.error(`Demo seed failed: ${e.message}`);
                  }
                },
              });
            }}
            className="flex items-center gap-1.5 bg-red-950/40 hover:bg-red-900/60 text-red-300 border border-red-800/60 hover:border-red-600 text-xs px-2.5 py-1.5 rounded-lg transition font-medium shadow-sm active:scale-95"
            title="Populate account with sample enterprise data"
          >
            <span className="text-red-400">⚡</span>
            <span className="hidden sm:inline">Seed Demo</span>
          </button>

          <button
            onClick={() => setIsCommandPaletteOpen(true)}
            className="flex items-center gap-2 bg-zinc-900/90 hover:bg-zinc-850 text-zinc-300 hover:text-white border border-zinc-800 text-xs px-3 py-1.5 rounded-lg transition font-medium active:scale-95 shadow-sm"
          >
            <span>Quick Jump</span>
            <kbd className="hidden sm:inline-block text-[10px] bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded font-mono border border-zinc-700/60">
              Ctrl+K
            </kbd>
          </button>

          {/* User Account Capsule */}
          <div className="hidden md:flex items-center gap-2.5 pl-2 border-l border-zinc-800/80">
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-zinc-800 to-zinc-700 border border-zinc-600/60 flex items-center justify-center font-bold text-white text-xs select-none">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : user?.email ? user.email.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="text-right">
              <div className="text-xs font-semibold text-zinc-200 leading-tight">
                {user?.full_name || 'User Account'}
              </div>
              <div className="text-[10px] text-zinc-400 font-mono leading-tight">
                {user?.email}
              </div>
            </div>
          </div>

          <button
            onClick={() => logout()}
            className="text-xs bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-red-400 hover:border-red-900/60 px-3 py-1.5 rounded-lg border border-zinc-800 font-medium transition active:scale-95"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Application Main Layout */}
      <div className="flex flex-1 min-h-0">
        {/* Left Rail Sidebar */}
        <aside
          className={`${
            isSidebarCollapsed ? 'w-16' : 'w-64'
          } shrink-0 bg-zinc-950/95 border-r border-zinc-800/80 flex flex-col overflow-y-auto transition-all duration-200 z-30`}
        >
          {/* Gmail Synchronization Widget Container */}
          <div className="p-3 border-b border-zinc-800/80">
            {isSidebarCollapsed ? (
              <div className="flex justify-center p-2 text-base text-red-400" title="Gmail Sync Active">
                📬
              </div>
            ) : (
              <GmailSyncWidget />
            )}
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {!isSidebarCollapsed && (
              <div className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 px-3 mb-2">
                Navigation
              </div>
            )}

            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                title={isSidebarCollapsed ? item.label : undefined}
                className={({ isActive }) =>
                  `flex items-center ${
                    isSidebarCollapsed ? 'justify-center px-2 py-3' : 'gap-3 px-3 py-2.5'
                  } rounded-xl text-xs font-medium transition duration-150 ${
                    isActive
                      ? 'bg-red-950/50 text-red-400 border border-red-800/70 shadow-sm shadow-red-950/40 font-semibold'
                      : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900/80 border border-transparent'
                  }`
                }
              >
                <span className="text-base select-none">{item.icon}</span>
                {!isSidebarCollapsed && <span>{item.label}</span>}
              </NavLink>
            ))}
          </nav>
        </aside>

        {/* Main Workspace Area */}
        <main className="flex-1 min-w-0 overflow-y-auto p-3 md:p-6 bg-black">
          <div className="max-w-[1600px] mx-auto w-full">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Global Command Palette (Cmd+K / Ctrl+K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
      />
    </div>
  );
};
