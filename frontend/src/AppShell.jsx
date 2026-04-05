import React, { useState } from 'react';
import { Outlet, useLocation, Link } from 'react-router-dom';
import { LayoutDashboard, UploadCloud, Download, Library, Wand2, Shield, LogOut, CheckSquare, Users, Activity, AlertTriangle, Settings } from 'lucide-react';
import api from './lib/api';

function VerificationBanner({ currentUser }) {
  const [sending, setSending] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [message, setMessage] = useState('');

  if (currentUser?.email_verified) return null;

  const handleResend = async () => {
    if (countdown > 0) return;
    setSending(true);
    try {
      await api.post('/verify-email/resend');
      setMessage('Verification email sent!');
      setCountdown(60);
      const timer = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err) {
      if (err.response?.status === 429) {
          setMessage('Too many requests. Please wait a while.');
      } else {
          setMessage('Failed to resend. Try again later.');
      }
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ background: 'var(--surface-elevated)', borderBottom: '1px solid var(--border-subtle)', padding: 'var(--space-12) var(--space-40)', display: 'flex', alignItems: 'center', gap: 'var(--space-16)', color: 'var(--warning)', fontSize: 'var(--font-small)' }}>
      <AlertTriangle size={16} />
      <span>Please verify your email address (<strong>{currentUser?.email}</strong>) to unlock all features.</span>
      <button 
        onClick={handleResend}
        disabled={sending || countdown > 0}
        className="btn"
        style={{ padding: 'var(--space-4) var(--space-12)', fontSize: 'var(--font-meta)', borderColor: 'var(--warning)', color: 'var(--warning)', background: 'transparent' }}
      >
        {sending ? 'Sending...' : countdown > 0 ? `Resend in ${countdown}s` : 'Resend Email'}
      </button>
      {message && <span style={{color: 'var(--text-secondary)'}}>{message}</span>}
    </div>
  );
}

function GoogleLinkModal({ currentUser }) {
  const [pendingLink, setPendingLink] = useState(null);
  const [linking, setLinking] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  React.useEffect(() => {
    try {
      const stored = localStorage.getItem('pending_google_link');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.email === currentUser.email) {
          setPendingLink(parsed);
        } else {
           localStorage.removeItem('pending_google_link');
        }
      }
    } catch(e) {}
  }, [currentUser]);

  if (!pendingLink) return null;

  const handleLink = async () => {
    setLinking(true);
    setError('');
    try {
      await api.post('/auth/google/link', { token: pendingLink.token });
      setSuccess(true);
      localStorage.removeItem('pending_google_link');
      setTimeout(() => {
         setPendingLink(null);
      }, 2000);
    } catch(err) {
      setError(err.response?.data?.error || 'Failed to link account.');
      setLinking(false);
    }
  };

  const handleSkip = () => {
    localStorage.removeItem('pending_google_link');
    setPendingLink(null);
  };

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }}>
      <div className="panel" style={{ width: '400px', backgroundColor: 'var(--surface-panel)', padding: 'var(--space-24)', borderRadius: 'var(--radius-lg)', boxShadow: '0 24px 64px rgba(0,0,0,0.4)', border: '1px solid var(--border-default)' }}>
        <h3 style={{ margin: '0 0 var(--space-8) 0', fontSize: '18px', fontWeight: 600 }}>Link Google Account?</h3>
        {!success ? (
          <>
            <p style={{ margin: '0 0 var(--space-20) 0', color: 'var(--text-secondary)', fontSize: '14px', lineHeight: 1.5 }}>
              You recently tried to sign in with Google. Would you like to link your Google account to your EditEase workspace for easier access next time?
            </p>
            {error && <div style={{ color: 'var(--danger)', marginBottom: 'var(--space-16)', fontSize: '14px', background: 'rgba(218,54,51,0.1)', padding: '8px 12px', borderRadius: '4px' }}>{error}</div>}
            <div style={{ display: 'flex', gap: 'var(--space-12)', justifyContent: 'flex-end' }}>
              <button onClick={handleSkip} className="btn" style={{ background: 'transparent', border: '1px solid var(--border-default)' }} disabled={linking}>Not Now</button>
              <button onClick={handleLink} className="btn btn-primary" disabled={linking}>{linking ? 'Linking...' : 'Link Account'}</button>
            </div>
          </>
        ) : (
          <div style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '8px', padding: 'var(--space-12) 0', fontWeight: 500 }}>
             <CheckSquare size={20} /> Successfully linked!
          </div>
        )}
      </div>
    </div>
  );
}

export default function AppShell({ currentUser, onLogout }) {
  const location = useLocation();
  const role = currentUser?.role || 'editor';
  const navDescriptions = {
    Dashboard: 'Your creative hub. Track recent ingests and see what the system is organizing for you.',
    'Review Queue': 'Quickly review and sort ambiguous clips so they land in the right folders.',
    Uploads: 'Drop in your raw files. We\'ll split the scenes and sync them securely to the cloud.',
    'Organized Videos': 'Browse your auto-organized clips, grouped by label, ready for batch download.',
    Users: 'Manage access, roles, and team operations from one place.',
    'Job Monitor': 'Track background processing across the queue in real time.',
  };

  // Workspace nav — shown to all roles (primary tasks)
  const workspaceNav = [
    { name: 'Dashboard',    path: '/app/dashboard', icon: LayoutDashboard, roles: ['admin', 'reviewer', 'editor'] },
    { name: 'Review Queue', path: '/app/review',     icon: CheckSquare,     roles: ['admin', 'reviewer'] },
    { name: 'Uploads',      path: '/app/uploads',    icon: UploadCloud,     roles: ['admin', 'editor'] },
    { name: 'Organized Videos', path: '/app/organized-videos', icon: Library, roles: ['admin', 'editor'] },
  ];

  // System nav — admin only (operational visibility)
  const adminNav = [
    { name: 'Users',       path: '/app/admin/users', icon: Users,    roles: ['admin'] },
    { name: 'Job Monitor', path: '/app/admin/jobs',  icon: Activity, roles: ['admin'] },
  ];

  const visibleWorkspace = workspaceNav.filter(i => i.roles.includes(role));
  const visibleAdmin     = adminNav.filter(i => i.roles.includes(role));
  const visibleNav       = [...visibleWorkspace, ...visibleAdmin];
  const activeNav        = visibleNav.find(n => location.pathname.startsWith(n.path));
  const activeTitle = activeNav?.name || 'Dashboard';
  const activeDescription = navDescriptions[activeTitle] || 'Move through review, uploads, and exports from one shared workspace.';

  return (
    <div className="app-container workspace-shell">
      <div className="workspace-ambient workspace-ambient-a" />
      <div className="workspace-ambient workspace-ambient-b" />
      <div className="sidebar workspace-sidebar">
        {/* Logo */}
        <Link
          to="/"
          className="workspace-logo"
        >
          <div className="workspace-logo-mark">
            <Wand2 size={18} color="var(--accent)" />
          </div>
          <div className="workspace-logo-copy">
            <span className="workspace-logo-text">EditEase</span>
            <span className="workspace-logo-subtext">Review workspace</span>
          </div>
        </Link>


        <nav className="workspace-nav">
          {/* Workspace items */}
          <div className="workspace-nav-group">
            <div className="workspace-section-label">Workspace</div>
          {visibleWorkspace.map(item => {
            const isActive = location.pathname.startsWith(item.path);
            return (
              <Link key={item.path} to={item.path}
                className={`nav-item workspace-nav-item ${isActive ? 'active' : ''}`}
              >
                <item.icon size={18} />
                {item.name}
              </Link>
            );
          })}
          </div>

          {/* Admin section — divider + items */}
          {visibleAdmin.length > 0 && (
            <div className="workspace-nav-group workspace-nav-group-admin">
              <div className="workspace-section-label">System</div>
              {visibleAdmin.map(item => {
                const isActive = location.pathname.startsWith(item.path);
                return (
                  <Link key={item.path} to={item.path}
                    className={`nav-item workspace-nav-item ${isActive ? 'active' : ''}`}
                  >
                    <item.icon size={18} />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          )}
        </nav>

        {/* Bottom account */}
        <div className="workspace-sidebar-footer">
          <div className="workspace-footer-actions">
            <Link to="/app/settings" className="btn workspace-ghost-btn">
              <Settings size={14} /> Settings
            </Link>
            <button
              onClick={onLogout}
              className="workspace-logout-btn"
            >
              <LogOut size={14} />
            </button>
          </div>
          <div className="workspace-account-card">
            <div className="workspace-account-avatar">
              {(currentUser.name || currentUser.email || 'U').charAt(0).toUpperCase()}
            </div>
            <div className="workspace-account-copy">
              <div className="workspace-account-name">
                {currentUser.name || currentUser.email}
              </div>
              <div className="workspace-account-role">
                {role}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Top bar + content */}
      <div className="main-wrapper workspace-main">
        <div className="workspace-topbar">
          <div className="workspace-topbar-copy">
            <span className="workspace-topbar-eyebrow">Workspace</span>
            <span className="workspace-topbar-title">{activeTitle}</span>
            <span className="workspace-topbar-subtitle">{activeDescription}</span>
          </div>
          <div className="workspace-topbar-actions">
            <Link
              to="/"
              className="btn workspace-home-btn"
            >
              Homepage
            </Link>
            <span className="badge info workspace-role-badge">
              {role}
            </span>
          </div>
        </div>

        <VerificationBanner currentUser={currentUser} />
        <GoogleLinkModal currentUser={currentUser} />

        <div className="main-content workspace-content">
          <div className="workspace-content-inner">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}
