// ToastProvider.jsx — JSX component lives here, not in the .js hook file
import React from 'react';
import { ToastContext, useToastState } from '../hooks/useToast';

// Re-export useToast so existing imports like:
//   import { useToast } from '../hooks/useToast'
// still work. (useToast is already in useToast.js)

export function ToastProvider({ children }) {
  const { toasts, addToast, removeToast } = useToastState();

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

// ── Toast Container ───────────────────────────────────────────
function ToastContainer({ toasts, onRemove }) {
  if (toasts.length === 0) return null;
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 min-w-[300px] max-w-sm">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onRemove={onRemove} />
      ))}
    </div>
  );
}

const TOAST_STYLES = {
  success: 'bg-emerald-600 border-emerald-500',
  error:   'bg-red-600 border-red-500',
  info:    'bg-blue-600 border-blue-500',
  warning: 'bg-amber-500 border-amber-400',
};

const TOAST_ICONS = {
  success: '✅',
  error:   '❌',
  info:    'ℹ️',
  warning: '⚠️',
};

function ToastItem({ toast, onRemove }) {
  return (
    <div
      className={`flex items-start gap-3 p-4 rounded-xl shadow-2xl border text-white
        ${TOAST_STYLES[toast.type] || TOAST_STYLES.info}`}
      style={{ animation: 'slideInRight 0.3s ease both' }}
    >
      <span className="text-lg flex-shrink-0">{TOAST_ICONS[toast.type]}</span>
      <p className="flex-1 text-sm font-medium leading-snug">{toast.message}</p>
      <button
        onClick={() => onRemove(toast.id)}
        className="flex-shrink-0 text-white/70 hover:text-white text-xl leading-none"
      >
        ×
      </button>
    </div>
  );
}

export default ToastProvider;
