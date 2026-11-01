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
    { path: '/graph', label: 'Action Graph', icon: '⚙️' },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col">

      {/* Top Header */}
      <header className="h-16 bg-slate-900 border-b border-slate-800 px-6 flex items-center justify-between shrink-0 z-40 shadow-lg">

        {/* Brand */}
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

        {/* User Controls */}
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
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
        <aside className="w-64 shrink-0 bg-slate-900/60 border-r border-slate-800 flex flex-col overflow-y-auto">

          {/* Gmail Synchronization */}
          <div className="p-2 border-b border-slate-800">
            <GmailSyncWidget />
          </div>

          {/* Navigation */}
          <nav className="p-4 space-y-2">

            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-3 mb-3">
              Navigation
            </div>

            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition ${isActive
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`
                }
              >
                <span className="text-base">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}

          </nav>
        </aside>

        {/* Main Workspace */}
        <main className="flex-1 min-w-0 overflow-y-auto p-6">

          <div className="max-w-7xl mx-auto w-full">
            <Outlet />
          </div>

        </main>
      </div>
    </div>
  );
};