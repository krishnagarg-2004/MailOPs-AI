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
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-black/80 backdrop-blur-md p-4 font-sans animate-in fade-in duration-150">
      <div
        className="w-full max-w-xl bg-zinc-950 border border-zinc-800 rounded-2xl shadow-2xl overflow-hidden text-zinc-100 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input header */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-zinc-800">
          <span className="text-red-500 text-sm">🔍</span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or jump to workspace..."
            autoFocus
            className="w-full bg-transparent text-sm text-white placeholder-zinc-500 focus:outline-none"
          />
          <kbd className="hidden sm:inline-block text-[10px] font-semibold bg-zinc-900 border border-zinc-800 px-1.5 py-0.5 rounded text-zinc-400">
            ESC
          </kbd>
        </div>

        {/* Command List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {filteredCommands.length === 0 ? (
            <div className="text-center py-8 text-xs text-zinc-500">
              No matching commands found.
            </div>
          ) : (
            filteredCommands.map((cmd, idx) => (
              <div
                key={cmd.id}
                onClick={() => cmd.action()}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer text-xs transition ${
                  selectedIndex === idx
                    ? 'bg-red-950/60 text-red-300 border border-red-800/80 shadow-sm'
                    : 'hover:bg-zinc-900/80 text-zinc-300'
                }`}
              >
                <span className="text-base">{cmd.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold truncate">{cmd.title}</div>
                  <div className="text-[11px] text-zinc-400 truncate">{cmd.description}</div>
                </div>
                <span className="text-[9px] uppercase tracking-wider px-2 py-0.5 rounded bg-zinc-900 text-zinc-400 font-medium border border-zinc-800">
                  {cmd.category}
                </span>
              </div>
            ))
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="px-4 py-2 border-t border-zinc-800/80 bg-black/60 flex items-center justify-between text-[11px] text-zinc-500">
          <span>Navigation: <kbd className="text-[10px] bg-zinc-900 px-1 rounded border border-zinc-800 text-zinc-400">↑</kbd> <kbd className="text-[10px] bg-zinc-900 px-1 rounded border border-zinc-800 text-zinc-400">↓</kbd></span>
          <span>Select: <kbd className="text-[10px] bg-zinc-900 px-1 rounded border border-zinc-800 text-zinc-400">↵</kbd></span>
        </div>
      </div>
    </div>
  );
};
