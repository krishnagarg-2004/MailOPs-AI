import React, { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { GmailSyncWidget } from './GmailSyncWidget';
import { CommandPalette } from './CommandPalette';

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();
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
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col">

      {/* Top Header */}
      <header className="h-16 bg-slate-900 border-b border-slate-800 px-4 md:px-6 flex items-center justify-between shrink-0 z-40 shadow-lg">

        {/* Brand & Sidebar Toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition"
            title={isSidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            <span className="text-base">{isSidebarCollapsed ? '☰' : '◀'}</span>
          </button>

          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-sky-400 to-indigo-600 flex items-center justify-center font-black text-slate-950 text-sm shadow-md">
            M
          </div>

          <div>
            <h1 className="text-base font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-indigo-300">
              MailOps AI
            </h1>

            <span className="text-[10px] text-slate-400 uppercase tracking-widest block font-semibold hidden sm:block">
              Work Intelligence Engine
            </span>
          </div>
        </div>

        {/* User Controls */}
        <div className="flex items-center gap-2 md:gap-3">
          <button
            onClick={async () => {
              if (confirm('Load realistic enterprise demo threads, invoices, and graph dependencies?')) {
                try {
                  const res = await api.seedDemoData();
                  alert(res.message || 'Demo data successfully loaded!');
                  window.location.reload();
                } catch (e: any) {
                  alert(`Demo seed failed: ${e.message}`);
                }
              }
            }}
            className="flex items-center gap-1.5 bg-gradient-to-r from-emerald-600/30 to-teal-600/30 hover:from-emerald-600/50 hover:to-teal-600/50 text-emerald-300 border border-emerald-500/40 text-xs px-2.5 py-1.5 rounded-lg transition font-medium"
            title="Populate account with sample enterprise data"
          >
            <span>⚡ Seed Demo</span>
          </button>

          <button
            onClick={() => setIsCommandPaletteOpen(true)}
            className="hidden sm:flex items-center gap-2 bg-slate-950 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 text-xs px-3 py-1.5 rounded-lg transition"
          >
            <span>Quick Jump</span>
            <kbd className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded font-mono text-slate-400">Ctrl+K</kbd>
          </button>

          <div className="text-right hidden md:block">
            <div className="text-xs font-semibold text-slate-200">
              {user?.full_name || 'User Account'}
            </div>

            <div className="text-[11px] text-slate-400">
              {user?.email}
            </div>
          </div>

          <button
            onClick={() => logout()}
            className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 font-medium transition"
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
          } shrink-0 bg-slate-900/60 border-r border-slate-800 flex flex-col overflow-y-auto transition-all duration-200`}
        >
          {/* Gmail Synchronization */}
          <div className="p-2 border-b border-slate-800">
            {isSidebarCollapsed ? (
              <div className="flex justify-center p-1 text-base" title="Gmail Sync Active">
                📬
              </div>
            ) : (
              <GmailSyncWidget />
            )}
          </div>

          {/* Navigation */}
          <nav className="p-2 md:p-3 space-y-1.5">
            {!isSidebarCollapsed && (
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-3 mb-2">
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
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
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
        <main className="flex-1 min-w-0 overflow-y-auto p-3 md:p-5">
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