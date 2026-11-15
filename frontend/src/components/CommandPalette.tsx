import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

interface CommandItem {
  id: string;
  title: string;
  description: string;
  category: 'Navigation' | 'Actions' | 'Filters';
  icon: string;
  action: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const navigate = useNavigate();

  const commands: CommandItem[] = [
    {
      id: 'nav-inbox',
      title: 'Go to Inbox & AI Reply',
      description: 'Review synchronized emails, AI analysis, and generate reply drafts',
      category: 'Navigation',
      icon: '📬',
      action: () => {
        navigate('/dashboard');
        onClose();
      },
    },
    {
      id: 'nav-docs',
      title: 'Go to Document OCR',
      description: 'Inspect extracted invoices, purchase orders, and PDF/DOCX contracts',
      category: 'Navigation',
      icon: '📄',
      action: () => {
        navigate('/documents');
        onClose();
      },
    },
    {
      id: 'nav-search',
      title: 'Go to Semantic Search & RAG Chat',
      description: 'Run natural-language queries across inboxes and converse with AI',
      category: 'Navigation',
      icon: '🔍',
      action: () => {
        navigate('/search');
        onClose();
      },
    },
    {
      id: 'nav-graph',
      title: 'Go to Action Graph & Relationships',
      description: 'Visualize operational dependencies, blocked tasks, and entity networks',
      category: 'Navigation',
      icon: '⚙️',
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
      icon: '⚡',
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
      title: '⚡ Seed Realistic Enterprise Demo Data',
      description: 'Populate mailbox with simulated customer escalations, invoices, and graph dependencies',
      category: 'Actions',
      icon: '🚀',
      action: async () => {
        onClose();
        if (confirm('Load realistic enterprise demo threads, invoices, and graph relationships?')) {
          try {
            const res = await api.seedDemoData();
            alert(res.message || 'Demo data loaded successfully!');
            window.location.reload();
          } catch (e: any) {
            alert(`Demo seed failed: ${e.message}`);
          }
        }
      },
    },
    {
      id: 'action-export-digest-csv',
      title: '📊 Export Executive Digest (CSV)',
      description: 'Download spreadsheet report of pending actions, business risks, and financial totals',
      category: 'Actions',
      icon: '📥',
      action: async () => {
        onClose();
        try {
          await api.downloadDigestExport('csv');
        } catch (e: any) {
          alert(`Export failed: ${e.message}`);
        }
      },
    },
    {
      id: 'action-export-digest-md',
      title: '📝 Export Executive Digest (Markdown)',
      description: 'Download formatted markdown executive briefing report',
      category: 'Actions',
      icon: '📋',
      action: async () => {
        onClose();
        try {
          await api.downloadDigestExport('markdown');
        } catch (e: any) {
          alert(`Export failed: ${e.message}`);
        }
      },
    },
    {
      id: 'action-shortcuts-help',
      title: '⌨️ Keyboard Shortcuts Help',
      description: 'View Superhuman-style navigation hotkeys (j/k, r, a, x, ?)',
      category: 'Actions',
      icon: '⌨️',
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
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-slate-950/70 backdrop-blur-sm p-4 font-sans animate-in fade-in duration-150">
      <div
        className="w-full max-w-xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden text-slate-100 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input header */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-800">
          <span className="text-slate-400 text-sm">🔍</span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or jump to workspace..."
            autoFocus
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          <kbd className="hidden sm:inline-block text-[10px] font-semibold bg-slate-800 border border-slate-700 px-1.5 py-0.5 rounded text-slate-400">
            ESC
          </kbd>
        </div>

        {/* Command List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {filteredCommands.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-500">
              No matching commands found.
            </div>
          ) : (
            filteredCommands.map((cmd, idx) => (
              <div
                key={cmd.id}
                onClick={() => cmd.action()}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer text-xs transition ${
                  selectedIndex === idx
                    ? 'bg-gradient-to-r from-sky-500/20 to-indigo-500/20 text-sky-200 border border-sky-500/30'
                    : 'hover:bg-slate-800/60 text-slate-300'
                }`}
              >
                <span className="text-base">{cmd.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold truncate">{cmd.title}</div>
                  <div className="text-[11px] text-slate-400 truncate">{cmd.description}</div>
                </div>
                <span className="text-[9px] uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">
                  {cmd.category}
                </span>
              </div>
            ))
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="px-4 py-2 border-t border-slate-800/80 bg-slate-950/40 flex items-center justify-between text-[11px] text-slate-500">
          <span>Navigation: <kbd className="text-[10px] bg-slate-800 px-1 rounded">↑</kbd> <kbd className="text-[10px] bg-slate-800 px-1 rounded">↓</kbd></span>
          <span>Select: <kbd className="text-[10px] bg-slate-800 px-1 rounded">↵</kbd></span>
        </div>
      </div>
    </div>
  );
};
