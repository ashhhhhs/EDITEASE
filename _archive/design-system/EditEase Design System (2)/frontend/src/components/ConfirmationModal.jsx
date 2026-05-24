import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

/**
 * ConfirmationModal — Reusable gated confirmation for destructive or privileged actions.
 *
 * Props:
 *   isOpen        — boolean, controls visibility
 *   title         — string, modal heading
 *   body          — string or ReactNode, consequence description
 *   confirmLabel  — string (default: 'Confirm')
 *   variant       — 'danger' | 'warning' | 'primary' (default: 'danger')
 *   onConfirm     — async or sync function to call on confirm
 *   onCancel      — function to call on cancel / close
 *   loading       — boolean, disables buttons and shows loading text
 */
export default function ConfirmationModal({
  isOpen,
  title = 'Are you sure?',
  body,
  confirmLabel = 'Confirm',
  variant = 'danger',
  onConfirm,
  onCancel,
  loading = false,
}) {
  if (!isOpen) return null;

  const variantStyles = {
    danger: {
      iconColor: 'var(--danger)',
      iconBg: 'rgba(218, 54, 51, 0.1)',
      btnClass: 'btn-danger',
    },
    warning: {
      iconColor: 'var(--warning)',
      iconBg: 'rgba(210, 153, 34, 0.1)',
      btnClass: 'btn-warning',
    },
    primary: {
      iconColor: 'var(--accent)',
      iconBg: 'rgba(88, 166, 255, 0.1)',
      btnClass: 'btn-primary',
    },
  };

  const vs = variantStyles[variant] || variantStyles.danger;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget && !loading) onCancel();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
      onClick={handleBackdropClick}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 10000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0,0,0,0.65)',
        backdropFilter: 'blur(6px)',
        WebkitBackdropFilter: 'blur(6px)',
        animation: 'fadeIn 0.18s ease',
      }}
    >
      <div
        className="panel"
        style={{
          width: '100%',
          maxWidth: 460,
          margin: '0 var(--space-16)',
          background: 'var(--surface-panel)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-xl)',
          padding: 'var(--space-32)',
          boxShadow: 'var(--shadow-modal)',
          animation: 'slideUpIn 0.22s cubic-bezier(0.22, 1, 0.36, 1)',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-16)', marginBottom: 'var(--space-20)' }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 'var(--radius-md)',
              background: vs.iconBg,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <AlertTriangle size={20} color={vs.iconColor} />
          </div>
          <div style={{ flex: 1 }}>
            <h3
              id="confirm-modal-title"
              style={{ margin: '0 0 var(--space-8) 0', fontSize: 'var(--font-title-card)', fontWeight: 600, color: 'var(--text-primary)' }}
            >
              {title}
            </h3>
            {body && (
              <p style={{ margin: 0, fontSize: 'var(--font-small)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                {body}
              </p>
            )}
          </div>
          {!loading && (
            <button
              onClick={onCancel}
              aria-label="Close dialog"
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 4, flexShrink: 0, marginTop: -4 }}
            >
              <X size={16} />
            </button>
          )}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 'var(--space-12)', justifyContent: 'flex-end' }}>
          <button
            className="btn"
            onClick={onCancel}
            disabled={loading}
            style={{ background: 'transparent' }}
          >
            Cancel
          </button>
          <button
            className={`btn ${vs.btnClass}`}
            onClick={onConfirm}
            disabled={loading}
            aria-busy={loading}
          >
            {loading ? 'Processing…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
