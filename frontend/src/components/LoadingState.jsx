import React from 'react';

export default function LoadingState({ message = 'Loading...', type = 'default' }) {
  if (type === 'cards') {
    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 'var(--space-20)', padding: 'var(--space-24)' }}>
        {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i} className="panel" style={{ padding: 0, overflow: 'hidden' }}>
            <div className="skeleton" style={{ width: '100%', height: '60px', borderRadius: '0' }} />
            <div style={{ padding: 'var(--space-12)' }}>
              <div className="skeleton" style={{ width: '65%', height: '14px', marginBottom: '8px' }} />
              <div className="skeleton" style={{ width: '40%', height: '12px' }} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (type === 'table') {
    return (
      <div style={{ padding: 'var(--space-24)', display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
        <div className="skeleton" style={{ width: '100%', height: '40px' }} />
        <div className="skeleton" style={{ width: '100%', height: '40px' }} />
        <div className="skeleton" style={{ width: '100%', height: '40px' }} />
        <div className="skeleton" style={{ width: '100%', height: '40px' }} />
        <div className="skeleton" style={{ width: '100%', height: '40px' }} />
      </div>
    );
  }

  if (type === 'grid') {
    return (
      <div className="clip-grid">
        {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i} className="clip-card" style={{ padding: 0 }}>
             <div className="skeleton" style={{ width: '100%', aspectRatio: '16/9', borderRadius: '0' }} />
             <div style={{ padding: 'var(--space-12)' }}>
                <div className="skeleton" style={{ width: '70%', height: '16px', marginBottom: '8px' }} />
                <div className="skeleton" style={{ width: '40%', height: '12px' }} />
             </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center', 
      padding: 'var(--space-64)',
      color: 'var(--text-muted)'
    }}>
      <div className="spin" style={{ 
        width: '32px', 
        height: '32px', 
        border: '3px solid var(--border-subtle)', 
        borderTopColor: 'var(--accent)', 
        borderRadius: '50%',
        marginBottom: 'var(--space-16)'
      }} />
      <span style={{ fontSize: 'var(--font-body)', fontWeight: 500 }}>{message}</span>
    </div>
  );
}
