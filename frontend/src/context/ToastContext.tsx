import React, { createContext, useCallback, useContext, useEffect, useState, ReactNode } from 'react';

export type ToastType = 'info' | 'success' | 'error' | 'warning';

export interface ToastItem {
  id: string;
  message: string;
  type: ToastType;
}

export interface ConfirmationOptions {
  title?: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isDanger?: boolean;
  onConfirm: () => void | Promise<void>;
  onCancel?: () => void;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType, duration?: number) => void;
  toast: {
    success: (message: string, duration?: number) => void;
    error: (message: string, duration?: number) => void;
    info: (message: string, duration?: number) => void;
    warning: (message: string, duration?: number) => void;
  };
  requestConfirmation: (options: ConfirmationOptions) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

type ToastSubscriber = (msg: string, type: ToastType, duration?: number) => void;
const subscribers = new Set<ToastSubscriber>();

export const notifyToast = (msg: string, type: ToastType = 'info', duration?: number) => {
  subscribers.forEach((fn) => fn(msg, type, duration));
};

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [confirmation, setConfirmation] = useState<ConfirmationOptions | null>(null);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback((message: string, type: ToastType = 'info', duration: number = 4000) => {
    const id = `${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
    setToasts((prev) => [...prev, { id, message, type }]);

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }, [removeToast]);

  useEffect(() => {
    const handler: ToastSubscriber = (msg, type, duration) => {
      showToast(msg, type, duration);
    };
    subscribers.add(handler);
    return () => {
      subscribers.delete(handler);
    };
  }, [showToast]);

  const toastMethods = {
    success: (msg: string, duration?: number) => showToast(msg, 'success', duration),
    error: (msg: string, duration?: number) => showToast(msg, 'error', duration),
    info: (msg: string, duration?: number) => showToast(msg, 'info', duration),
    warning: (msg: string, duration?: number) => showToast(msg, 'warning', duration),
  };

  const requestConfirmation = useCallback((options: ConfirmationOptions) => {
    setConfirmation(options);
  }, []);

  return (
    <ToastContext.Provider
      value={{
        showToast,
        toast: toastMethods,
        requestConfirmation,
      }}
    >
      {children}

      {/* Modern Floating Toast Notification Stack */}
      <div
        className="fixed bottom-6 right-6 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none"
        aria-live="polite"
      >
        {toasts.map((t) => {
          let borderClasses = 'border-zinc-800/90 bg-zinc-950/90 text-zinc-100 shadow-xl';
          let icon = <span className="text-zinc-400 font-bold shrink-0">ℹ</span>;

          if (t.type === 'error') {
            borderClasses = 'border-rose-600/70 bg-zinc-950/95 text-zinc-100 shadow-rose-950/40 shadow-xl';
            icon = <span className="text-rose-500 font-bold shrink-0">✕</span>;
          } else if (t.type === 'success') {
            borderClasses = 'border-emerald-600/60 bg-zinc-950/95 text-zinc-100 shadow-emerald-950/30 shadow-xl';
            icon = <span className="text-emerald-400 font-bold shrink-0">✓</span>;
          } else if (t.type === 'warning') {
            borderClasses = 'border-amber-600/60 bg-zinc-950/95 text-zinc-100 shadow-amber-950/30 shadow-xl';
            icon = <span className="text-amber-400 font-bold shrink-0">⚠</span>;
          }

          return (
            <div
              key={t.id}
              className={`pointer-events-auto border rounded-2xl p-3.5 text-xs backdrop-blur-xl flex items-start gap-3 transition-all duration-200 animate-fadeIn ${borderClasses}`}
            >
              <div className="pt-0.5">{icon}</div>
              <div className="flex-1 font-medium leading-relaxed break-words">{t.message}</div>
              <button
                onClick={() => removeToast(t.id)}
                className="text-zinc-500 hover:text-white ml-1 text-xs shrink-0 px-1 py-0.5 rounded transition"
                title="Dismiss"
              >
                ✕
              </button>
            </div>
          );
        })}
      </div>

      {/* Styled Non-Modal Confirmation Dialog */}
      {confirmation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-150">
          <div className="bg-zinc-950/95 border border-zinc-800/90 text-zinc-100 shadow-2xl rounded-2xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center gap-2.5">
              {confirmation.isDanger ? (
                <div className="w-8 h-8 rounded-xl bg-red-950/80 border border-red-800/80 flex items-center justify-center text-rose-400 text-sm">
                  ⚠
                </div>
              ) : (
                <div className="w-8 h-8 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-red-400 text-sm">
                  ⚡
                </div>
              )}
              <h3 className="text-sm font-bold text-zinc-100 tracking-tight">
                {confirmation.title || 'Confirm Action'}
              </h3>
            </div>
            <p className="text-xs text-zinc-300 leading-relaxed">
              {confirmation.message}
            </p>
            <div className="flex items-center justify-end gap-2 pt-3 border-t border-zinc-800/80">
              <button
                type="button"
                onClick={() => {
                  const onCancel = confirmation.onCancel;
                  setConfirmation(null);
                  onCancel?.();
                }}
                className="px-4 py-2 rounded-xl text-xs font-medium text-zinc-300 bg-zinc-900 hover:bg-zinc-850 border border-zinc-800 transition active:scale-95"
              >
                {confirmation.cancelLabel || 'Cancel'}
              </button>
              <button
                type="button"
                onClick={async () => {
                  const onConfirm = confirmation.onConfirm;
                  setConfirmation(null);
                  await onConfirm();
                }}
                className={`px-4 py-2 rounded-xl text-xs font-semibold text-white transition active:scale-95 ${
                  confirmation.isDanger
                    ? 'bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 shadow-lg shadow-red-950/60'
                    : 'bg-zinc-800 hover:bg-zinc-700'
                }`}
              >
                {confirmation.confirmLabel || 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextValue => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
