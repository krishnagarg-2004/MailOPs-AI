import React, { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  Inbox,
  FileText,
  Search,
  Network,
  Menu,
  ChevronLeft,
  Sparkles,
  Command,
  LogOut,
  Zap,
} from 'lucide-react';
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
    { path: '/dashboard', label: 'Inbox & AI Reply', icon: Inbox },
    { path: '/documents', label: 'Document OCR', icon: FileText },
    { path: '/search', label: 'Search & RAG Chat', icon: Search },
    { path: '/graph', label: 'Action Graph', icon: Network },
  ];

  return (
    <div className="min-h-screen bg-[#08080a] text-[#ededed] font-sans flex flex-col selection:bg-red-500/20 selection:text-white">
      {/* Fey Glassmorphic Navigation Header */}
      <header className="h-14 fey-glass border-b border-white/[0.06] px-4 md:px-6 flex items-center justify-between shrink-0 sticky top-0 z-40 transition-all">
        {/* Brand & Sidebar Toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.05] border border-transparent hover:border-white/[0.08] transition active:scale-95"
            title={isSidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            aria-label="Toggle Navigation Sidebar"
          >
            {isSidebarCollapsed ? (
              <Menu className="w-4 h-4 text-zinc-400" />
            ) : (
              <ChevronLeft className="w-4 h-4 text-zinc-400" />
            )}
          </button>

          {/* Fey Brand Capsule */}
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-b from-zinc-800 to-zinc-950 flex items-center justify-center text-red-500 shadow-sm border border-white/[0.09] select-none">
              <Sparkles className="w-3.5 h-3.5" />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold tracking-tight text-white">MailOps</span>
              <span className="text-[10px] font-medium tracking-wide text-red-400 px-1.5 py-0.5 rounded-full bg-red-950/60 border border-red-500/30">
                AI
              </span>
            </div>
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
            className="flex items-center gap-1.5 bg-white/[0.03] hover:bg-red-950/40 text-zinc-300 hover:text-red-300 border border-white/[0.08] hover:border-red-500/40 text-xs px-2.5 py-1.5 rounded-lg transition font-medium active:scale-95 shadow-sm"
            title="Populate account with sample enterprise data"
          >
            <Zap className="w-3 h-3 text-red-400" />
            <span className="hidden sm:inline">Seed Demo</span>
          </button>

          {/* Fey Search / Quick Jump Pill */}
          <button
            onClick={() => setIsCommandPaletteOpen(true)}
            className="flex items-center gap-2 bg-[#101014] hover:bg-[#15151c] text-zinc-400 hover:text-zinc-200 border border-white/[0.08] hover:border-white/[0.14] text-xs px-2.5 py-1.5 rounded-lg transition font-medium active:scale-95 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)]"
          >
            <Command className="w-3.5 h-3.5 text-zinc-400" />
            <span className="hidden sm:inline text-xs">Jump to</span>
            <kbd className="text-[10px] bg-white/[0.06] text-zinc-400 px-1.5 py-0.5 rounded font-mono border border-white/[0.06]">
              ⌘K
            </kbd>
          </button>

          {/* User Account Capsule */}
          <div className="hidden md:flex items-center gap-2.5 pl-3 border-l border-white/[0.06]">
            <div className="w-6 h-6 rounded-full bg-gradient-to-b from-zinc-800 to-zinc-900 border border-white/[0.1] flex items-center justify-center font-bold text-zinc-200 text-[11px] select-none">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : user?.email ? user.email.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="text-right">
              <div className="text-xs font-medium text-zinc-300 leading-tight">
                {user?.full_name || 'User Account'}
              </div>
              <div className="text-[10px] text-zinc-500 font-mono leading-tight">
                {user?.email}
              </div>
            </div>
          </div>

          <button
            onClick={() => logout()}
            className="p-1.5 text-zinc-400 hover:text-red-400 hover:bg-red-950/30 rounded-lg border border-transparent hover:border-red-900/40 transition active:scale-95"
            title="Logout"
            aria-label="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Application Main Layout */}
      <div className="flex flex-1 min-h-0">
        {/* Left Rail Sidebar */}
        <aside
          className={`${
            isSidebarCollapsed ? 'w-16' : 'w-60'
          } shrink-0 bg-[#0b0b0e] border-r border-white/[0.06] flex flex-col overflow-y-auto transition-all duration-200 z-30`}
        >
          {/* Gmail Synchronization Widget Container */}
          <div className="p-3 border-b border-white/[0.06]">
            {isSidebarCollapsed ? (
              <div className="flex justify-center p-2 text-red-400" title="Gmail Sync Active">
                <Inbox className="w-4 h-4" />
              </div>
            ) : (
              <GmailSyncWidget />
            )}
          </div>

          {/* Navigation Links */}
          <nav className="p-2 space-y-0.5">
            {!isSidebarCollapsed && (
              <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500 px-3 py-2">
                Workspaces
              </div>
            )}

            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  title={isSidebarCollapsed ? item.label : undefined}
                  className={({ isActive }) =>
                    `flex items-center ${
                      isSidebarCollapsed ? 'justify-center px-2 py-2.5' : 'gap-2.5 px-3 py-2'
                    } rounded-lg text-xs font-medium transition-all duration-150 ${
                      isActive
                        ? 'bg-[#18181f] text-white border border-white/[0.12] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] font-semibold'
                        : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03] border border-transparent'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0 text-zinc-400 group-hover:text-zinc-200" />
                  {!isSidebarCollapsed && <span>{item.label}</span>}
                </NavLink>
              );
            })}
          </nav>
        </aside>

        {/* Main Workspace Area */}
        <main className="flex-1 min-w-0 overflow-y-auto p-4 md:p-6 bg-[#08080a]">
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
