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

// Standalone global emitter for toast notifications
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

      {/* Non-blocking Toast Notification Stack */}
      <div
        className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
        aria-live="polite"
      >
        {toasts.map((t) => {
          let borderClasses = 'border-zinc-800 bg-zinc-950 text-zinc-100';
          let icon = <span className="text-zinc-400 font-bold shrink-0">ℹ</span>;

          if (t.type === 'error') {
            borderClasses = 'border-red-600/70 bg-zinc-950 text-zinc-100 shadow-red-950/20';
            icon = <span className="text-red-500 font-bold shrink-0">✕</span>;
          } else if (t.type === 'success') {
            borderClasses = 'border-zinc-700 bg-zinc-950 text-zinc-100';
            icon = <span className="text-red-400 font-bold shrink-0">✓</span>;
          } else if (t.type === 'warning') {
            borderClasses = 'border-red-900/60 bg-zinc-950 text-zinc-200';
            icon = <span className="text-red-400 font-bold shrink-0">⚠</span>;
          }

          return (
            <div
              key={t.id}
              className={`pointer-events-auto border rounded-lg p-3 text-xs shadow-xl flex items-start gap-2.5 transition-all duration-200 ${borderClasses}`}
            >
              <div className="pt-0.5">{icon}</div>
              <div className="flex-1 font-medium leading-relaxed break-words">{t.message}</div>
              <button
                onClick={() => removeToast(t.id)}
                className="text-zinc-500 hover:text-zinc-300 ml-1 text-xs shrink-0 px-1 py-0.5"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="bg-zinc-950 border border-zinc-800 text-zinc-100 shadow-2xl rounded-xl max-w-md w-full p-5 space-y-4">
            <div className="flex items-center gap-2">
              {confirmation.isDanger ? (
                <span className="text-red-500 text-base">⚠</span>
              ) : (
                <span className="text-zinc-400 text-base">⚡</span>
              )}
              <h3 className="text-sm font-bold text-zinc-100">
                {confirmation.title || 'Confirm Action'}
              </h3>
            </div>
            <p className="text-xs text-zinc-300 leading-relaxed">
              {confirmation.message}
            </p>
            <div className="flex items-center justify-end gap-2 pt-3 border-t border-zinc-800">
              <button
                type="button"
                onClick={() => {
                  const onCancel = confirmation.onCancel;
                  setConfirmation(null);
                  onCancel?.();
                }}
                className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-zinc-300 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 transition"
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
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white transition ${
                  confirmation.isDanger
                    ? 'bg-red-600 hover:bg-red-500 shadow-lg shadow-red-950/50'
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
