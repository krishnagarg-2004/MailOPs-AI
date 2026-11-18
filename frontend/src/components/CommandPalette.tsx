import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Inbox,
  FileText,
  Search,
  Network,
  RefreshCw,
  Zap,
  Download,
  Keyboard,
  ArrowRight,
} from 'lucide-react';
import { useToast } from '../context/ToastContext';
import { api } from '../services/api';

interface CommandItem {
  id: string;
  title: string;
  description: string;
  category: 'Navigation' | 'Actions' | 'Filters';
  icon: React.ComponentType<{ className?: string }>;
  action: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const { toast, requestConfirmation } = useToast();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const navigate = useNavigate();

  const commands: CommandItem[] = [
    {
      id: 'nav-inbox',
      title: 'Inbox & AI Reply',
      description: 'Review synchronized emails, AI analysis, and generate reply drafts',
      category: 'Navigation',
      icon: Inbox,
      action: () => {
        navigate('/dashboard');
        onClose();
      },
    },
    {
      id: 'nav-docs',
      title: 'Document OCR',
      description: 'Inspect extracted invoices, purchase orders, and PDF/DOCX contracts',
      category: 'Navigation',
      icon: FileText,
      action: () => {
        navigate('/documents');
        onClose();
      },
    },
    {
      id: 'nav-search',
      title: 'Semantic Search & RAG Chat',
      description: 'Run natural-language queries across inboxes and converse with AI',
      category: 'Navigation',
      icon: Search,
      action: () => {
        navigate('/search');
        onClose();
      },
    },
    {
      id: 'nav-graph',
      title: 'Action Graph & Relationships',
      description: 'Visualize operational dependencies, blocked tasks, and entity networks',
      category: 'Navigation',
      icon: Network,
      action: () => {
        navigate('/graph');
        onClose();
      },
    },
    {
      id: 'action-sync',
      title: 'Trigger Gmail Synchronization',
      description: 'Fetch new inbound emails and initiate background analysis',
      category: 'Actions',
      icon: RefreshCw,
      action: () => {
        const syncBtn = document.querySelector<HTMLButtonElement>('button:has-text("Sync Now"), [data-sync-button]');
        if (syncBtn) {
          syncBtn.click();
        } else {
          navigate('/dashboard');
        }
        onClose();
      },
    },
    {
      id: 'action-seed-demo',
      title: 'Seed Enterprise Demo Data',
      description: 'Populate mailbox with simulated customer escalations, invoices, and graph dependencies',
      category: 'Actions',
      icon: Zap,
      action: () => {
        onClose();
        requestConfirmation({
          title: 'Seed Enterprise Demo Data',
          message: 'Load realistic enterprise demo threads, invoices, and graph relationships?',
          confirmLabel: 'Load Demo Data',
          onConfirm: async () => {
            try {
              const res = await api.seedDemoData();
              toast.success(res.message || 'Demo data loaded successfully!');
              setTimeout(() => window.location.reload(), 600);
            } catch (e: any) {
              toast.error(`Demo seed failed: ${e.message}`);
            }
          },
        });
      },
    },
    {
      id: 'action-export-digest-csv',
      title: 'Export Executive Digest (CSV)',
      description: 'Download spreadsheet report of pending actions, business risks, and financial totals',
      category: 'Actions',
      icon: Download,
      action: async () => {
        onClose();
        try {
          await api.downloadDigestExport('csv');
          toast.success('Executive digest CSV downloaded successfully!');
        } catch (e: any) {
          toast.error(`Export failed: ${e.message}`);
        }
      },
    },
    {
      id: 'action-export-digest-md',
      title: 'Export Executive Digest (Markdown)',
      description: 'Download formatted markdown executive briefing report',
      category: 'Actions',
      icon: Download,
      action: async () => {
        onClose();
        try {
          await api.downloadDigestExport('markdown');
          toast.success('Executive digest Markdown downloaded successfully!');
        } catch (e: any) {
          toast.error(`Export failed: ${e.message}`);
        }
      },
    },
    {
      id: 'action-shortcuts-help',
      title: 'Keyboard Shortcuts Help',
      description: 'View Superhuman-style navigation hotkeys (j/k, r, a, x, ?)',
      category: 'Actions',
      icon: Keyboard,
      action: () => {
        onClose();
        window.dispatchEvent(new CustomEvent('open-keyboard-shortcuts'));
      },
    },
  ];

  const filteredCommands = commands.filter(
    (cmd) =>
      cmd.title.toLowerCase().includes(query.toLowerCase()) ||
      cmd.description.toLowerCase().includes(query.toLowerCase()) ||
      cmd.category.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % (filteredCommands.length || 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + filteredCommands.length) % (filteredCommands.length || 1));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].action();
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, filteredCommands, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/75 backdrop-blur-md p-4 font-sans animate-in fade-in duration-150">
      <div
        className="w-full max-w-xl bg-[#0f0f12] border border-white/[0.08] rounded-2xl shadow-[0_16px_50px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.08)] overflow-hidden text-[#ededed] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input header */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-white/[0.06] bg-[#0c0c0f]">
          <Search className="w-4 h-4 text-zinc-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or jump to workspace..."
            autoFocus
            className="w-full bg-transparent text-sm text-white placeholder-zinc-500 focus:outline-none"
          />
          <kbd className="hidden sm:inline-block text-[10px] font-mono bg-white/[0.05] border border-white/[0.08] px-1.5 py-0.5 rounded text-zinc-400">
            ESC
          </kbd>
        </div>

        {/* Command List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-0.5">
          {filteredCommands.length === 0 ? (
            <div className="text-center py-8 text-xs text-zinc-500">
              No matching commands found.
            </div>
          ) : (
            filteredCommands.map((cmd, idx) => {
              const Icon = cmd.icon;
              const isSelected = selectedIndex === idx;
              return (
                <div
                  key={cmd.id}
                  onClick={() => cmd.action()}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-xs transition-all duration-150 ${
                    isSelected
                      ? 'bg-white/[0.07] text-white border border-white/[0.12] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]'
                      : 'hover:bg-white/[0.03] text-zinc-300 border border-transparent'
                  }`}
                >
                  <div className={`p-1.5 rounded-md ${isSelected ? 'text-red-400 bg-red-950/40' : 'text-zinc-400 bg-white/[0.03]'}`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-white truncate">{cmd.title}</div>
                    <div className="text-[11px] text-zinc-400 truncate">{cmd.description}</div>
                  </div>
                  <span className="text-[10px] tracking-wider px-2 py-0.5 rounded-full bg-white/[0.04] text-zinc-400 font-mono border border-white/[0.06]">
                    {cmd.category}
                  </span>
                  {isSelected && <ArrowRight className="w-3.5 h-3.5 text-zinc-400" />}
                </div>
              );
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="px-4 py-2 border-t border-white/[0.06] bg-[#0c0c0f] flex items-center justify-between text-[11px] text-zinc-500">
          <span>
            Navigate: <kbd className="text-[10px] bg-white/[0.05] px-1 py-0.5 rounded border border-white/[0.08] text-zinc-400 font-mono">↑</kbd>{' '}
            <kbd className="text-[10px] bg-white/[0.05] px-1 py-0.5 rounded border border-white/[0.08] text-zinc-400 font-mono">↓</kbd>
          </span>
          <span>
            Select: <kbd className="text-[10px] bg-white/[0.05] px-1 py-0.5 rounded border border-white/[0.08] text-zinc-400 font-mono">↵</kbd>
          </span>
        </div>
      </div>
    </div>
  );
};
