import React from 'react';
import { ExtractedActionItem } from '../types/ai';

interface ActionItemsWidgetProps {
  actions: ExtractedActionItem[];
  onStatusUpdate?: (actionId: string, status: 'CONFIRMED' | 'DISMISSED' | 'COMPLETED') => void;
}

export const ActionItemsWidget: React.FC<ActionItemsWidgetProps> = ({ actions, onStatusUpdate }) => {
  const pendingActions = actions.filter((a) => a.status === 'PENDING');

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg text-slate-100 font-sans space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-slate-100">Work Action Items</h3>
          <span className="text-xs bg-purple-500/20 text-purple-300 font-semibold px-2 py-0.5 rounded-full border border-purple-500/30">
            {pendingActions.length} Pending
          </span>
        </div>
      </div>

      {pendingActions.length === 0 ? (
        <p className="text-xs text-slate-400 italic text-center py-4">No pending action items extracted.</p>
      ) : (
        <div className="space-y-2">
          {pendingActions.map((action) => (
            <div
              key={action.id}
              className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition"
            >
              <div className="space-y-1 pr-2">
                <p className="text-xs font-medium text-slate-200">{action.description}</p>
                <div className="flex items-center gap-3 text-[11px] text-slate-400">
                  {action.assignee && <span>Assignee: {action.assignee}</span>}
                  {action.due_date && <span className="text-amber-400">Due: {new Date(action.due_date).toLocaleDateString()}</span>}
                </div>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  onClick={() => onStatusUpdate && onStatusUpdate(action.id, 'CONFIRMED')}
                  className="text-xs px-2.5 py-1 rounded bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 font-medium hover:bg-emerald-600/30 transition"
                >
                  Confirm
                </button>
                <button
                  onClick={() => onStatusUpdate && onStatusUpdate(action.id, 'DISMISSED')}
                  className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 hover:bg-slate-700 transition"
                >
                  Dismiss
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
