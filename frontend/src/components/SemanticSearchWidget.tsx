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
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-5 shadow-lg space-y-4 text-zinc-100 font-sans">
      <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
          Semantic & Hybrid Search (pgvector)
        </h3>
        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => setMode('hybrid')}
            className={`px-2.5 py-1 rounded font-medium transition ${mode === 'hybrid'
                ? 'bg-red-950/70 border border-red-800/80 text-red-400 font-semibold'
                : 'bg-zinc-900 text-zinc-400 hover:text-white border border-zinc-800'
              }`}
          >
            Hybrid (Keyword + Vector)
          </button>
          <button
            onClick={() => setMode('semantic')}
            className={`px-2.5 py-1 rounded font-medium transition ${mode === 'semantic'
                ? 'bg-red-950/70 border border-red-800/80 text-red-400 font-semibold'
                : 'bg-zinc-900 text-zinc-400 hover:text-white border border-zinc-800'
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
          className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/30"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="bg-red-600 hover:bg-red-500 text-white text-xs px-4 py-2 rounded-lg font-medium transition disabled:opacity-50 shadow-md shadow-red-950/50"
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {/* Search Results */}
      {hasSearched && !isLoading && (
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs font-semibold text-zinc-400">
            Search Results
          </span>
          <span className="text-[11px] text-zinc-500">
            {results.length} result{results.length !== 1 ? 's' : ''}
          </span>
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((item) => (
            <div key={item.id} className="bg-zinc-900 border border-zinc-800/80 rounded-lg p-3 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${item.source_type === 'DOCUMENT'
                        ? 'bg-zinc-800 text-zinc-300 border border-zinc-700'
                        : 'bg-red-950/60 text-red-400 border border-red-800/60'
                      }`}
                  >
                    {item.source_type}
                  </span>
                  <span className="font-semibold text-zinc-200">{item.source_name}</span>
                  {item.page_number && (
                    <span className="text-[10px] bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded">
                      Page {item.page_number}
                    </span>
                  )}
                </div>
                <div className="text-[11px] font-mono text-red-400 font-semibold bg-red-950/60 px-2 py-0.5 rounded border border-red-800/60">
                  {Math.round(item.similarity_score * 100)}% match
                </div>
              </div>
              <p className="text-zinc-300 font-mono text-[11px] leading-relaxed line-clamp-3 bg-black/40 p-2.5 rounded border border-zinc-800/60">
                {item.chunk_text}
              </p>
            </div>
          ))}
        </div>
      )}

      {hasSearched && !isLoading && results.length === 0 && (
        <div className="text-center py-6 text-xs text-zinc-500">
          No matching results found. Try another search.
        </div>
      )}

    </div>
  );
};
