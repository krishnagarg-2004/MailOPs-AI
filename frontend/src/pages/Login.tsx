import React from 'react';
import { Navigate } from 'react-router-dom';
import { Sparkles, Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Login: React.FC = () => {
  const { login, loginDemo, isAuthenticated, isLoading } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#08080a] text-[#ededed] font-sans p-4 relative overflow-hidden">
      {/* Subtle ambient lighting */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-red-600/[0.07] rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-md w-full p-8 sm:p-10 bg-[#0e0e12] border border-white/[0.08] rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.06)] backdrop-blur-2xl space-y-6 text-center relative z-10">
        <div>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-b from-zinc-800 to-zinc-950 flex items-center justify-center text-red-500 shadow-sm border border-white/[0.1] mx-auto mb-3.5 select-none">
            <Sparkles className="w-5 h-5" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-white flex items-center justify-center gap-2">
            <span>MailOps</span>
            <span className="text-red-400 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-red-950/40 border border-red-500/20 tracking-wider">
              AI
            </span>
          </h1>
          <p className="text-xs text-zinc-500 mt-1">
            Enterprise Communication & Work Intelligence Platform
          </p>
        </div>

        <div className="bg-[#0a0a0d] p-3.5 rounded-xl border border-white/[0.05] text-left text-xs space-y-1.5 text-zinc-300">
          <div className="flex items-center gap-1.5 text-zinc-300 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
            <span>Single Sign-On Ready</span>
          </div>
          <p className="text-zinc-500 leading-relaxed text-[11px]">
            Connect your Google Workspace mailbox to unlock AI intelligence, document OCR, grounded RAG search, and human-reviewed reply drafting.
          </p>
        </div>

        <button
          onClick={() => login()}
          className="w-full flex items-center justify-center gap-2.5 py-2.5 px-4 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-medium text-xs sm:text-sm rounded-lg shadow-sm transition duration-150 active:scale-[0.98]"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path
              fill="currentColor"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="currentColor"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="currentColor"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="currentColor"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          Sign in with Google
        </button>

        <div className="relative flex py-1 items-center">
          <div className="flex-grow border-t border-white/[0.06]"></div>
          <span className="flex-shrink mx-3 text-[10px] uppercase tracking-wider text-zinc-500 font-mono">Or</span>
          <div className="flex-grow border-t border-white/[0.06]"></div>
        </div>

        <button
          onClick={() => loginDemo()}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] hover:border-white/[0.14] text-zinc-300 hover:text-white font-medium text-xs sm:text-sm rounded-lg transition duration-150 shadow-sm active:scale-[0.98]"
        >
          <Zap className="w-3.5 h-3.5 text-red-400" />
          <span>Launch Interactive Demo Showcase</span>
        </button>
      </div>
    </div>
  );
};
