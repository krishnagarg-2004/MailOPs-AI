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

      {/* Top Header */}
      <header className="h-16 bg-zinc-950 border-b border-zinc-800 px-4 md:px-6 flex items-center justify-between shrink-0 z-40 shadow-xl">

        {/* Brand & Sidebar Toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-900 transition"
            title={isSidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            <span className="text-base">{isSidebarCollapsed ? '☰' : '◀'}</span>
          </button>

          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-red-600 to-rose-700 flex items-center justify-center font-black text-white text-sm shadow-md shadow-red-950/60 border border-red-500/40">
            M
          </div>

          <div>
            <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
              <span>MailOps</span>
              <span className="text-red-500 text-xs font-semibold px-1.5 py-0.5 rounded bg-red-950/80 border border-red-800/60 uppercase tracking-wider">AI</span>
            </h1>

            <span className="text-[10px] text-zinc-400 uppercase tracking-widest block font-semibold hidden sm:block">
              Work Intelligence Engine
            </span>
          </div>
        </div>

        {/* User Controls */}
        <div className="flex items-center gap-2 md:gap-3">
          <button
            onClick={() => {
              requestConfirmation({
                title: 'Seed Enterprise Demo Data',
                message: 'Load realistic enterprise demo threads, invoices, and graph dependencies?',
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
            className="flex items-center gap-1.5 bg-red-950/40 hover:bg-red-900/60 text-red-300 border border-red-800/60 hover:border-red-600 text-xs px-2.5 py-1.5 rounded-lg transition font-medium shadow-sm"
            title="Populate account with sample enterprise data"
          >
            <span>⚡ Seed Demo</span>
          </button>

          <button
            onClick={() => setIsCommandPaletteOpen(true)}
            className="hidden sm:flex items-center gap-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-800 text-xs px-3 py-1.5 rounded-lg transition"
          >
            <span>Quick Jump</span>
            <kbd className="text-[10px] bg-zinc-800 px-1.5 py-0.5 rounded font-mono text-zinc-400">Ctrl+K</kbd>
          </button>

          <div className="text-right hidden md:block">
            <div className="text-xs font-semibold text-zinc-200">
              {user?.full_name || 'User Account'}
            </div>

            <div className="text-[11px] text-zinc-400">
              {user?.email}
            </div>
          </div>

          <button
            onClick={() => logout()}
            className="text-xs bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-red-400 hover:border-red-900/60 px-3 py-1.5 rounded-lg border border-zinc-800 font-medium transition"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Application Body */}
      <div className="flex flex-1 min-h-0">

        {/* Left Rail */}
        <aside
          className={`${
            isSidebarCollapsed ? 'w-16' : 'w-60'
          } shrink-0 bg-zinc-950 border-r border-zinc-800/80 flex flex-col overflow-y-auto transition-all duration-200`}
        >
          {/* Gmail Synchronization */}
          <div className="p-2 border-b border-zinc-800/80">
            {isSidebarCollapsed ? (
              <div className="flex justify-center p-1 text-base text-red-400" title="Gmail Sync Active">
                📬
              </div>
            ) : (
              <GmailSyncWidget />
            )}
          </div>

          {/* Navigation */}
          <nav className="p-2 md:p-3 space-y-1.5">
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
                  } rounded-xl text-xs font-semibold transition ${
                    isActive
                      ? 'bg-red-950/50 text-red-400 border border-red-800/70 shadow-sm shadow-red-950/40'
                      : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900/80'
                  }`
                }
              >
                <span className="text-base">{item.icon}</span>
                {!isSidebarCollapsed && <span>{item.label}</span>}
              </NavLink>
            ))}
          </nav>
        </aside>

        {/* Main Workspace */}
        <main className="flex-1 min-w-0 overflow-y-auto p-3 md:p-5 bg-black">
          <div className="max-w-[1600px] mx-auto w-full">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Global Command Palette (Cmd+K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
      />
    </div>
  );
};