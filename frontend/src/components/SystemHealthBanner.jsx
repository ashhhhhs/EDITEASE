import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, AlertCircle, Loader2, X, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * SystemHealthBanner
 * Displays a single top-level status sentence about system health.
 * Dismissable per session via local state.
 *
 * Props:
 *   stats — the admin overview stats object from /admin/overview
 */
export default function SystemHealthBanner({ stats }) {
  const [dismissed, setDismissed] = useState(false);
  if (!stats || dismissed) return null;

  const failed = stats.tasks_failed || 0;
  const running = stats.tasks_running || 0;
  const pending = stats.pending_review || 0;
  const uncertain = stats.uncertain_clips || 0;

  let variant = 'healthy'; // 'healthy' | 'warning' | 'critical'
  let Icon = CheckCircle2;
  let message = 'System healthy — all tasks are running normally.';
  let link = null;

  if (failed > 0) {
    variant = 'critical';
    Icon = AlertCircle;
    message = `${failed} background task${failed > 1 ? 's' : ''} failed and require${failed === 1 ? 's' : ''} attention.`;
    link = { to: '/app/admin/jobs?status=FAILURE', label: 'View Failed Jobs' };
  } else if (uncertain > 0) {
    variant = 'warning';
    Icon = AlertTriangle;
    message = `${uncertain} clip${uncertain > 1 ? 's' : ''} flagged as uncertain by the AI — review recommended.`;
    link = { to: '/app/review', label: 'Open Review Queue' };
  } else if (pending > 10) {
    variant = 'warning';
    Icon = AlertTriangle;
    message = `Review queue is growing — ${pending} clips are waiting for human review.`;
    link = { to: '/app/review', label: 'Review Now' };
  } else if (running > 0) {
    variant = 'running';
    Icon = Loader2;
    message = `${running} task${running > 1 ? 's are' : ' is'} currently processing in the background.`;
    link = { to: '/app/admin/jobs', label: 'Monitor Jobs' };
  }

  const styles = {
    healthy: {
      bg: 'rgba(35, 134, 54, 0.08)',
      border: 'rgba(35, 134, 54, 0.25)',
      accent: 'var(--success)',
      iconColor: 'var(--success)',
    },
    warning: {
      bg: 'rgba(210, 153, 34, 0.08)',
      border: 'rgba(210, 153, 34, 0.25)',
      accent: 'var(--warning)',
      iconColor: 'var(--warning)',
    },
    critical: {
      bg: 'rgba(218, 54, 51, 0.08)',
      border: 'rgba(218, 54, 51, 0.25)',
      accent: 'var(--danger)',
      iconColor: 'var(--danger)',
    },
    running: {
      bg: 'rgba(88, 166, 255, 0.07)',
      border: 'rgba(88, 166, 255, 0.2)',
      accent: 'var(--accent)',
      iconColor: 'var(--accent)',
    },
  };

  const s = styles[variant];

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 'var(--space-16)',
        padding: 'var(--space-12) var(--space-20)',
        marginBottom: 'var(--space-24)',
        background: s.bg,
        border: `1px solid ${s.border}`,
        borderLeft: `4px solid ${s.accent}`,
        borderRadius: 'var(--radius-lg)',
        animation: 'fadeSlideIn 0.35s ease',
      }}
    >
      {/* Left: icon + message */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)', minWidth: 0 }}>
        <Icon
          size={18}
          color={s.iconColor}
          className={variant === 'running' ? 'spin' : undefined}
          style={{ flexShrink: 0 }}
        />
        <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-primary)', fontWeight: 500 }}>
          {message}
        </span>
      </div>

      {/* Right: CTA link + dismiss */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', flexShrink: 0 }}>
        {link && (
          <Link
            to={link.to}
            className="btn"
            style={{
              fontSize: 'var(--font-meta)',
              padding: '5px 12px',
              borderColor: s.border,
              color: s.accent,
              background: 'transparent',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 5,
            }}
          >
            {link.label}
            <ArrowRight size={12} />
          </Link>
        )}
        <button
          onClick={() => setDismissed(true)}
          aria-label="Dismiss system status banner"
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--text-muted)',
            padding: 4,
            display: 'flex',
            alignItems: 'center',
            borderRadius: 'var(--radius-sm)',
            transition: 'color 0.15s',
          }}
          onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-secondary)')}
          onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
        >
          <X size={15} />
        </button>
      </div>
    </div>
  );
}
