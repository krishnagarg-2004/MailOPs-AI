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
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4 text-slate-100 font-sans">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
          Semantic & Hybrid Search (pgvector)
        </h3>
        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => setMode('hybrid')}
            className={`px-2.5 py-1 rounded font-medium transition ${mode === 'hybrid'
                ? 'bg-purple-600/30 border border-purple-500/50 text-purple-300'
                : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
          >
            Hybrid (Keyword + Vector)
          </button>
          <button
            onClick={() => setMode('semantic')}
            className={`px-2.5 py-1 rounded font-medium transition ${mode === 'semantic'
                ? 'bg-indigo-600/30 border border-indigo-500/50 text-indigo-300'
                : 'bg-slate-800 text-slate-400 hover:text-slate-200'
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
          className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="bg-purple-600 hover:bg-purple-500 text-white text-xs px-4 py-2 rounded-lg font-medium transition disabled:opacity-50"
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {/* Search Results */}
      {hasSearched && !isLoading && (
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs font-semibold text-slate-400">
            Search Results
          </span>
          <span className="text-[11px] text-slate-500">
            {results.length} result{results.length !== 1 ? 's' : ''}
          </span>
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((item) => (
            <div key={item.id} className="bg-slate-950 border border-slate-800/80 rounded-lg p-3 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${item.source_type === 'DOCUMENT'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                      }`}
                  >
                    {item.source_type}
                  </span>
                  <span className="font-semibold text-slate-200">{item.source_name}</span>
                  {item.page_number && (
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded">
                      Page {item.page_number}
                    </span>
                  )}
                </div>
                <div className="text-[11px] font-mono text-purple-400 font-medium">
                  {Math.round(item.similarity_score * 100)}% match
                </div>
              </div>
              <p className="text-slate-300 font-mono text-[11px] leading-relaxed line-clamp-3">
                {item.chunk_text}
              </p>
            </div>
          ))}
        </div>
      )}

      {hasSearched && !isLoading && results.length === 0 && (
        <div className="text-center py-6 text-xs text-slate-500">
          No matching results found. Try another search.
        </div>
      )}

    </div>
  );
};
