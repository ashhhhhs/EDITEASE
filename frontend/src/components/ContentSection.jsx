import React from 'react';

export default function ContentSection({ title, children, className = '' }) {
  return (
    <section className={`panel ${className}`} style={{ marginBottom: 'var(--space-24)', padding: 'var(--space-24)' }}>
      {title && <h2 style={{ marginBottom: 'var(--space-20)', fontSize: 'var(--font-title-section)' }}>{title}</h2>}
      {children}
    </section>
  );
}
