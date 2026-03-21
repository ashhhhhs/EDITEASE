import React from 'react';

export default function PageHeader({ title, description, actions, breadcrumbs }) {
  return (
    <div style={{ marginBottom: 'var(--space-32)', display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
      {breadcrumbs && (
        <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)', display: 'flex', gap: 'var(--space-8)' }}>
          {breadcrumbs.map((crumb, idx) => (
            <span key={idx}>
              {crumb} {idx < breadcrumbs.length - 1 && <span style={{ margin: '0 4px' }}>/</span>}
            </span>
          ))}
        </div>
      )}
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-16)' }}>
        <div>
          <h1 style={{ margin: 0, lineHeight: 1.2 }}>{title}</h1>
          {description && (
            <p style={{ margin: 'var(--space-8) 0 0 0', color: 'var(--text-secondary)', fontSize: 'var(--font-body)', maxWidth: '600px' }}>
              {description}
            </p>
          )}
        </div>
        
        {actions && (
          <div style={{ display: 'flex', gap: 'var(--space-12)', alignItems: 'center' }}>
            {actions}
          </div>
        )}
      </div>
    </div>
  );
}
