import React from 'react';
import { Inbox } from 'lucide-react';

export default function EmptyState({ 
  icon: Icon = Inbox, 
  title = 'No Data Found', 
  message = 'There is currently no data to display here.', 
  action 
}) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--space-64) var(--space-24)',
      textAlign: 'center',
      backgroundColor: 'rgba(255,255,255,0.01)',
      border: '1px dashed var(--border-subtle)',
      borderRadius: 'var(--radius-lg)'
    }}>
      <div style={{
        width: '64px',
        height: '64px',
        borderRadius: '50%',
        backgroundColor: 'var(--surface-panel)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 'var(--space-20)',
        boxShadow: 'var(--shadow-card)'
      }}>
        <Icon size={32} color="var(--text-secondary)" />
      </div>
      <h3 style={{ fontSize: 'var(--font-title-card)', margin: '0 0 var(--space-8) 0', color: 'var(--text-primary)' }}>
        {title}
      </h3>
      <p style={{ color: 'var(--text-secondary)', maxWidth: '400px', fontSize: 'var(--font-body)', margin: '0 0 var(--space-24) 0' }}>
        {message}
      </p>
      {action && (
        <div>{action}</div>
      )}
    </div>
  );
}
