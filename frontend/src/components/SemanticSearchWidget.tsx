import React, { useState } from 'react';
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
    <div className="bg-zinc-950/90 border border-zinc-800/80 rounded-2xl p-5 shadow-xl space-y-4 text-zinc-100 font-sans">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800/80 pb-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
          Semantic & Hybrid Search (pgvector)
        </h3>
        <div className="flex items-center gap-1 bg-zinc-900/90 p-1 rounded-xl border border-zinc-800/80 text-xs">
          <button
            onClick={() => setMode('hybrid')}
            className={`px-3 py-1 rounded-lg font-medium transition ${
              mode === 'hybrid'
                ? 'bg-red-950/80 border border-red-800/80 text-red-400 font-semibold shadow-xs'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            Hybrid Search
          </button>
          <button
            onClick={() => setMode('semantic')}
            className={`px-3 py-1 rounded-lg font-medium transition ${
              mode === 'semantic'
                ? 'bg-red-950/80 border border-red-800/80 text-red-400 font-semibold shadow-xs'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            Vector Only
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search emails, invoices, agreements, or tasks..."
          className="flex-1 bg-zinc-900/90 border border-zinc-800 rounded-xl px-4 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500/80 focus:ring-1 focus:ring-red-500/30 transition"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white text-xs px-4 py-2 rounded-xl font-medium transition disabled:opacity-50 shadow-md shadow-red-950/50 active:scale-95"
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {/* Search Results */}
      {hasSearched && !isLoading && (
        <div className="flex items-center justify-between pt-1">
          <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
            Results
          </span>
          <span className="text-[11px] text-zinc-400 font-mono">
            {results.length} item{results.length !== 1 ? 's' : ''} found
          </span>
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
          {results.map((item) => (
            <div key={item.id} className="bg-zinc-900/60 border border-zinc-800/80 rounded-xl p-3.5 space-y-2 text-xs hover:border-zinc-700 transition">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                      item.source_type === 'DOCUMENT'
                        ? 'bg-zinc-800 text-zinc-300 border border-zinc-700'
                        : 'bg-red-950/70 text-red-400 border border-red-800/70'
                    }`}
                  >
                    {item.source_type}
                  </span>
                  <span className="font-semibold text-zinc-200">{item.source_name}</span>
                  {item.page_number && (
                    <span className="text-[10px] bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded font-mono">
                      Page {item.page_number}
                    </span>
                  )}
                </div>
                <div className="text-[11px] font-mono text-red-400 font-bold bg-red-950/70 px-2 py-0.5 rounded-full border border-red-800/70">
                  {Math.round(item.similarity_score * 100)}% match
                </div>
              </div>
              <p className="text-zinc-300 font-mono text-[11px] leading-relaxed line-clamp-3 bg-black/60 p-3 rounded-lg border border-zinc-800/80 shadow-inner">
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
