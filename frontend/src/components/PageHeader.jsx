import React from 'react';

/**
 * Editorial PageHeader — Danik Bartolini composition style.
 * Title slides up from a mask reveal. Subtitle fades in with delay.
 * Optionally shows breadcrumb/description in small-caps on the side.
 */
export default function PageHeader({ title, description, actions, breadcrumbs }) {
  return (
    <header style={{
      paddingBottom: 'var(--space-40)',
      marginBottom: 'var(--space-40)',
      borderBottom: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-16)',
    }}>
      {/* Top row: breadcrumbs + actions */}
      {(breadcrumbs || actions) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {breadcrumbs && (
            <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)', display: 'flex', gap: 'var(--space-8)', alignItems: 'center' }}>
              {breadcrumbs}
            </div>
          )}
          {actions && (
            <div style={{ display: 'flex', gap: 'var(--space-12)', alignItems: 'center', marginLeft: 'auto' }}>
              {actions}
            </div>
          )}
        </div>
      )}

      {/* Display title with mask reveal */}
      <div style={{ overflow: 'hidden' }}>
        <h1 className="display-title reveal-text d1">
          {title}
        </h1>
      </div>

      {/* Description as editorial subtitle */}
      {description && (
        <p className="display-subtitle reveal-text d2" style={{ animationDelay: '0.18s' }}>
          {description}
        </p>
      )}
    </header>
  );
}
