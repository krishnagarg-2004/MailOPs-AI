import React, { useState } from 'react';
import { Search, Sparkles } from 'lucide-react';
import { SearchResultItem } from '../types/search';

interface SemanticSearchWidgetProps {
  onSearch?: (query: string, mode: 'semantic' | 'hybrid') => void;
  results?: SearchResultItem[];
  isLoading?: boolean;
}

export const SemanticSearchWidget: React.FC<SemanticSearchWidgetProps> = ({
  onSearch,
  results = [],
  isLoading = false,
}) => {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<'semantic' | 'hybrid'>('hybrid');
  const [hasSearched, setHasSearched] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (query.trim() && onSearch) {
      setHasSearched(true);
      onSearch(query.trim(), mode);
    }
  };

  return (
    <div className="bg-[#0e0e12] border border-white/[0.07] rounded-xl p-4 sm:p-5 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)] space-y-3.5 text-[#ededed] font-sans">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/[0.06] pb-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-red-400" />
          Semantic & Hybrid Search (pgvector)
        </h3>
        <div className="flex items-center gap-1 bg-[#121216] p-1 rounded-lg border border-white/[0.06] text-xs">
          <button
            onClick={() => setMode('hybrid')}
            className={`px-2.5 py-1 rounded-md font-medium transition ${
              mode === 'hybrid'
                ? 'bg-white/[0.08] border border-white/[0.12] text-white font-semibold shadow-sm'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            Hybrid Search
          </button>
          <button
            onClick={() => setMode('semantic')}
            className={`px-2.5 py-1 rounded-md font-medium transition ${
              mode === 'semantic'
                ? 'bg-white/[0.08] border border-white/[0.12] text-white font-semibold shadow-sm'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            Vector Only
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search emails, invoices, agreements, or tasks..."
            className="w-full bg-[#0a0a0d] border border-white/[0.07] rounded-lg pl-9 pr-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500/60 transition"
          />
        </div>
        <button
          type="submit"
          disabled={isLoading}
          className="bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white text-xs px-4 py-2 rounded-lg font-medium transition disabled:opacity-50 shadow-sm active:scale-95"
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {/* Search Results */}
      {hasSearched && !isLoading && (
        <div className="flex items-center justify-between pt-1">
          <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">
            Results
          </span>
          <span className="text-[10px] text-zinc-400 font-mono tabular-nums">
            {results.length} item{results.length !== 1 ? 's' : ''} found
          </span>
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
          {results.map((item) => (
            <div key={item.id} className="bg-[#0a0a0d] border border-white/[0.06] rounded-lg p-3 space-y-2 text-xs hover:border-white/[0.12] transition">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-mono uppercase ${
                      item.source_type === 'DOCUMENT'
                        ? 'bg-white/[0.04] text-zinc-300 border border-white/[0.08]'
                        : 'bg-red-950/40 text-red-400 border border-red-500/20'
                    }`}
                  >
                    {item.source_type}
                  </span>
                  <span className="font-medium text-zinc-200">{item.source_name}</span>
                  {item.page_number && (
                    <span className="text-[10px] bg-white/[0.04] text-zinc-400 px-1.5 py-0.5 rounded font-mono tabular-nums">
                      Page {item.page_number}
                    </span>
                  )}
                </div>
                <div className="text-[10px] font-mono text-red-400 font-medium bg-red-950/50 px-2 py-0.5 rounded-full border border-red-500/20 tabular-nums">
                  {Math.round(item.similarity_score * 100)}% match
                </div>
              </div>
              <p className="text-zinc-300 font-mono text-[11px] leading-relaxed line-clamp-3 bg-[#121216] p-2.5 rounded-md border border-white/[0.05]">
                {item.chunk_text}
              </p>
            </div>
          ))}
        </div>
      )}

      {hasSearched && !isLoading && results.length === 0 && (
        <div className="text-center py-8 text-xs text-zinc-500">
          No matching results found. Try another search keyword or switch search modes.
        </div>
      )}
    </div>
  );
};
