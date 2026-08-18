import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { GmailSyncWidget } from './GmailSyncWidget';

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();

  const navItems = [
    { path: '/dashboard', label: 'Inbox & AI Reply', icon: '📬' },
    { path: '/documents', label: 'Document OCR', icon: '📄' },
    { path: '/search', label: 'Search & RAG Chat', icon: '🔍' },
    { path: '/graph', label: 'Action Graph', icon: '🕸️' },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col">
      {/* Top Header Bar */}
      <header className="h-16 bg-slate-900 border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-40 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-sky-400 to-indigo-600 flex items-center justify-center font-black text-slate-950 text-sm shadow-md">
            M
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-indigo-300">
              MailOps AI
            </h1>
            <span className="text-[10px] text-slate-400 uppercase tracking-widest block font-semibold">
              Work Intelligence Engine
            </span>
          </div>
        </div>

        {/* Header Right Controls */}
        <div className="flex items-center gap-4">
          <div className="hidden lg:block w-96">
            <GmailSyncWidget />
          </div>

          <div className="flex items-center gap-3 border-l border-slate-800 pl-4">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-semibold text-slate-200">{user?.full_name || 'User Account'}</div>
              <div className="text-[11px] text-slate-400">{user?.email}</div>
            </div>

            <button
              onClick={() => logout()}
              className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 font-medium transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace Grid */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Navigation */}
        <aside className="w-64 bg-slate-900/60 border-r border-slate-800 p-4 space-y-2 shrink-0 hidden md:block">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-3 mb-2">
            Navigation
          </div>

          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`
              }
            >
              <span className="text-base">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
