import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';

const ToastContext = createContext(null);

let _id = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const add = useCallback((message, type = 'info', duration = 4000) => {
    const id = ++_id;
    setToasts(prev => [...prev, { id, message, type, duration }]);
    if (duration > 0) {
      setTimeout(() => remove(id), duration);
    }
    return id;
  }, []);

  const remove = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const toast = useMemo(() => ({
    success: (msg, dur) => add(msg, 'success', dur),
    error:   (msg, dur) => add(msg, 'error', dur),
    warning: (msg, dur) => add(msg, 'warning', dur),
    info:    (msg, dur) => add(msg, 'info', dur),
    dismiss: remove,
  }), [add, remove]);

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <ToastContainer toasts={toasts} onRemove={remove} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within a ToastProvider');
  return ctx;
}

const ICONS = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ',
};

const COLORS = {
  success: { bg: 'rgba(35, 134, 54, 0.15)', border: 'rgba(35, 134, 54, 0.4)', accent: '#3fb950', dot: '#238636' },
  error:   { bg: 'rgba(218, 54, 51, 0.15)', border: 'rgba(218, 54, 51, 0.4)', accent: '#ff7b72', dot: '#da3633' },
  warning: { bg: 'rgba(210, 153, 34, 0.15)', border: 'rgba(210, 153, 34, 0.4)', accent: '#e3b341', dot: '#d29922' },
  info:    { bg: 'rgba(88, 166, 255, 0.12)', border: 'rgba(88, 166, 255, 0.3)', accent: '#58a6ff', dot: '#58a6ff' },
};

function ToastContainer({ toasts, onRemove }) {
  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column',
      gap: '10px',
      pointerEvents: 'none',
    }}>
      {toasts.map(t => (
        <ToastItem key={t.id} toast={t} onRemove={onRemove} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onRemove }) {
  const c = COLORS[toast.type] || COLORS.info;

  return (
    <div
      onClick={() => onRemove(toast.id)}
      title="Click to dismiss"
      style={{
        pointerEvents: 'all',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        padding: '14px 18px',
        background: c.bg,
        border: `1px solid ${c.border}`,
        borderRadius: '10px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        maxWidth: '360px',
        cursor: 'pointer',
        animation: 'toastSlideIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
        color: '#c9d1d9',
        fontSize: '14px',
        lineHeight: 1.4,
      }}
    >
      <div style={{
        width: '20px',
        height: '20px',
        borderRadius: '50%',
        background: c.dot,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        fontSize: '11px',
        fontWeight: 700,
        flexShrink: 0,
        marginTop: '1px'
      }}>
        {ICONS[toast.type]}
      </div>
      <span style={{ flex: 1 }}>{toast.message}</span>
    </div>
  );
}
