import React, { createContext, useCallback, useContext, useEffect, useState, ReactNode } from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

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

      {/* Fey Floating Notification Stack */}
      <div
        className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
        aria-live="polite"
      >
        {toasts.map((t) => {
          let borderClasses = 'border-white/[0.08] bg-[#0f0f12]/95 text-zinc-200 shadow-2xl';
          let icon = <Info className="w-4 h-4 text-zinc-400 shrink-0" />;

          if (t.type === 'error') {
            borderClasses = 'border-rose-500/30 bg-[#0f0f12]/95 text-zinc-100 shadow-rose-950/20 shadow-2xl';
            icon = <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />;
          } else if (t.type === 'success') {
            borderClasses = 'border-emerald-500/30 bg-[#0f0f12]/95 text-zinc-100 shadow-emerald-950/20 shadow-2xl';
            icon = <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />;
          } else if (t.type === 'warning') {
            borderClasses = 'border-amber-500/30 bg-[#0f0f12]/95 text-zinc-100 shadow-amber-950/20 shadow-2xl';
            icon = <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />;
          }

          return (
            <div
              key={t.id}
              className={`pointer-events-auto border rounded-xl p-3 text-xs backdrop-blur-xl flex items-start gap-2.5 transition-all duration-200 animate-fadeIn ${borderClasses}`}
            >
              <div className="pt-0.5">{icon}</div>
              <div className="flex-1 font-medium leading-relaxed break-words">{t.message}</div>
              <button
                onClick={() => removeToast(t.id)}
                className="text-zinc-500 hover:text-white p-0.5 rounded transition"
                title="Dismiss"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>

      {/* Styled Fey Non-Modal Confirmation Dialog */}
      {confirmation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4 animate-in fade-in duration-150">
          <div className="bg-[#0f0f12] border border-white/[0.09] text-[#ededed] shadow-[0_16px_50px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.08)] rounded-xl max-w-md w-full p-5 space-y-3.5">
            <div className="flex items-center gap-2.5">
              {confirmation.isDanger ? (
                <div className="w-7 h-7 rounded-lg bg-red-950/60 border border-red-500/30 flex items-center justify-center text-rose-400">
                  <AlertTriangle className="w-4 h-4" />
                </div>
              ) : (
                <div className="w-7 h-7 rounded-lg bg-white/[0.04] border border-white/[0.08] flex items-center justify-center text-red-400">
                  <Info className="w-4 h-4" />
                </div>
              )}
              <h3 className="text-xs font-semibold text-white tracking-tight">
                {confirmation.title || 'Confirm Action'}
              </h3>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed">
              {confirmation.message}
            </p>
            <div className="flex items-center justify-end gap-2 pt-2.5 border-t border-white/[0.06]">
              <button
                type="button"
                onClick={() => {
                  const onCancel = confirmation.onCancel;
                  setConfirmation(null);
                  onCancel?.();
                }}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-300 bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] transition active:scale-95"
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
                className={`px-3 py-1.5 rounded-lg text-xs font-medium text-white transition active:scale-95 ${
                  confirmation.isDanger
                    ? 'bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 shadow-sm'
                    : 'bg-white/[0.08] hover:bg-white/[0.14] border border-white/[0.12]'
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
