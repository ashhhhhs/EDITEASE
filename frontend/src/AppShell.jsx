import React, { useState, useRef, useCallback } from 'react';
import { Outlet, useLocation, Link } from 'react-router-dom';
import { LayoutDashboard, UploadCloud, Download, Library, Wand2, Shield, LogOut, CheckSquare, Users, Activity, AlertTriangle, Settings, Zap, Bell, CheckCircle } from 'lucide-react';
import { Joyride, STATUS } from 'react-joyride';
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
    } catch {
      localStorage.removeItem('pending_google_link');
    }
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

function TourTip({ title, body }) {
  return (
    <div className="tour-tip">
      <h4>{title}</h4>
      <p>{body}</p>
    </div>
  );
}

export default function AppShell({ currentUser, onLogout }) {
  const location = useLocation();
  const role = currentUser?.role || 'editor';
  const [openReviewRequests, setOpenReviewRequests] = useState(0);
  const [assignedReviewRequests, setAssignedReviewRequests] = useState(0);
  const [resolvedReviewRequests, setResolvedReviewRequests] = useState(0);
  const [resolvedReviewTarget, setResolvedReviewTarget] = useState(null);
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
    { name: 'Dashboard',    path: '/app/dashboard', icon: LayoutDashboard, roles: ['admin', 'editor', 'reviewer'] },
    { name: 'Review Queue', path: '/app/review',     icon: CheckSquare,     roles: ['admin', 'editor', 'reviewer'] },
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

  React.useEffect(() => {
    if (role !== 'admin') {
      setOpenReviewRequests(0);
      return;
    }

    let cancelled = false;
    const fetchOpenReviewRequests = async () => {
      try {
        const res = await api.get('/search?review_request_status=open&reviewed=false&limit=1');
        if (!cancelled) setOpenReviewRequests(res.data.total || 0);
      } catch {
        if (!cancelled) setOpenReviewRequests(0);
      }
    };

    fetchOpenReviewRequests();
    window.addEventListener('review-requests-changed', fetchOpenReviewRequests);
    const timer = setInterval(fetchOpenReviewRequests, 30000);
    return () => {
      cancelled = true;
      window.removeEventListener('review-requests-changed', fetchOpenReviewRequests);
      clearInterval(timer);
    };
  }, [role, location.pathname]);

  React.useEffect(() => {
    if (!['editor', 'reviewer'].includes(role)) {
      setAssignedReviewRequests(0);
      return;
    }

    let cancelled = false;
    const fetchAssignedReviewRequests = async () => {
      try {
        const res = await api.get('/search?review_request_status=assigned&assigned_to_me=true&reviewed=false&limit=1');
        if (!cancelled) setAssignedReviewRequests(res.data.total || 0);
      } catch {
        if (!cancelled) setAssignedReviewRequests(0);
      }
    };

    fetchAssignedReviewRequests();
    window.addEventListener('review-requests-changed', fetchAssignedReviewRequests);
    const timer = setInterval(fetchAssignedReviewRequests, 30000);
    return () => {
      cancelled = true;
      window.removeEventListener('review-requests-changed', fetchAssignedReviewRequests);
      clearInterval(timer);
    };
  }, [role, location.pathname]);

  React.useEffect(() => {
    if (role !== 'editor') {
      setResolvedReviewRequests(0);
      setResolvedReviewTarget(null);
      return;
    }

    let cancelled = false;
    const fetchResolvedReviewRequests = async () => {
      try {
        const res = await api.get('/search?review_request_status=resolved&requested_by_me=true&resolution_unseen=true&limit=1');
        if (!cancelled) {
          setResolvedReviewRequests(res.data.total || 0);
          setResolvedReviewTarget((res.data.results || [])[0] || null);
        }
      } catch {
        if (!cancelled) {
          setResolvedReviewRequests(0);
          setResolvedReviewTarget(null);
        }
      }
    };

    fetchResolvedReviewRequests();
    window.addEventListener('review-requests-changed', fetchResolvedReviewRequests);
    const timer = setInterval(fetchResolvedReviewRequests, 30000);
    return () => {
      cancelled = true;
      window.removeEventListener('review-requests-changed', fetchResolvedReviewRequests);
      clearInterval(timer);
    };
  }, [role, location.pathname]);

  const resolvedReviewLink = React.useMemo(() => {
    const params = new URLSearchParams({ review_resolved: 'true' });
    if (resolvedReviewTarget?.video) params.set('video', resolvedReviewTarget.video);
    if (resolvedReviewTarget?.scene_id !== undefined && resolvedReviewTarget?.scene_id !== null) {
      params.set('scene_id', String(resolvedReviewTarget.scene_id));
    }
    const label = resolvedReviewTarget?.manual_scene_label || resolvedReviewTarget?.scene_label;
    if (label) params.set('label', label);
    const clipKey = resolvedReviewTarget?._key || (
      resolvedReviewTarget?.video && resolvedReviewTarget?.scene_id !== undefined
        ? `${resolvedReviewTarget.video}::${resolvedReviewTarget.scene_id}`
        : ''
    );
    if (clipKey) params.set('clip_key', clipKey);
    return `/app/organized-videos?${params.toString()}`;
  }, [resolvedReviewTarget]);

  // Tour guide state

  const [runTour, setRunTour] = useState(false);
  const tourSteps = [
    {
      target: 'body',
      placement: 'center',
      content: (
        <TourTip
          title="Welcome to EditEase"
          body="Take a quick walkthrough of the main workspace areas and the path from upload to review to organized output."
        />
      ),
      disableBeacon: true,
    },
    {
      target: '.tour-sidebar',
      content: (
        <TourTip
          title="Workspace navigation"
          body="Use the sidebar to move between dashboard, uploads, review queue, organized videos, and admin tools."
        />
      ),
      placement: 'right',
    },
    {
      target: '.tour-nav-Dashboard',
      content: (
        <TourTip
          title="Dashboard"
          body="Check recent activity, processing status, review workload, and system health before starting work."
        />
      ),
      placement: 'right',
    },
    {
      target: '.tour-nav-Uploads',
      content: (
        <TourTip
          title="Uploads"
          body="Start with raw footage here. EditEase creates scene records and prepares clips for review and organization."
        />
      ),
      placement: 'right',
    },
    {
      target: '.tour-nav-Review-Queue',
      content: (
        <TourTip
          title="Review queue"
          body="Clips that need a human decision appear here, so reviewers can approve, flag, or leave notes."
        />
      ),
      placement: 'right',
    },
    {
      target: '.tour-nav-Organized-Videos',
      content: (
        <TourTip
          title="Organized videos"
          body="Reviewed assets and organized folders collect here for download, follow-up review, or export."
        />
      ),
      placement: 'right',
    },
    {
      target: '.workspace-topbar',
      content: (
        <TourTip
          title="Current context"
          body="The topbar confirms where you are and keeps quick navigation actions close by."
        />
      ),
      placement: 'bottom',
    },
    {
      target: '.tour-start-btn',
      content: (
        <TourTip
          title="Restart the tour"
          body="Use this button any time you want to run the walkthrough again."
        />
      ),
      placement: 'left',
    }
  ];

  const handleJoyrideCallback = (data) => {
    const { status } = data;
    if ([STATUS.FINISHED, STATUS.SKIPPED].includes(status)) {
      setRunTour(false);
    }
  };

  const spotRef = useRef(null);
  const onSpotMove = useCallback((e) => {
    spotRef.current?.style.setProperty('--wx', `${e.clientX}px`);
    spotRef.current?.style.setProperty('--wy', `${e.clientY}px`);
  }, []);

  return (
    <div className="app-container workspace-shell" onMouseMove={onSpotMove}>
      <div className="workspace-grid-overlay" aria-hidden="true" />
      <div className="workspace-spotlight" ref={spotRef} aria-hidden="true" />
      <Joyride
        steps={tourSteps}
        run={runTour}
        continuous
        showProgress
        showSkipButton
        callback={handleJoyrideCallback}
        locale={{
          back: 'Back',
          close: 'Close',
          last: 'Done',
          next: 'Next',
          skip: 'Skip tour',
        }}
        styles={{
          options: {
            primaryColor: 'var(--accent)',
            backgroundColor: 'transparent',
            textColor: 'var(--text-primary)',
            arrowColor: 'transparent',
            overlayColor: 'rgba(0, 0, 0, 0.65)',
            zIndex: 10000,
          },
          tooltipContainer: {
            textAlign: 'left',
            borderRadius: '20px',
            border: 'none',
            boxShadow: 'none',
            backdropFilter: 'none',
            WebkitBackdropFilter: 'none',
            padding: '24px 28px',
            maxWidth: '420px',
            background: 'transparent',
          },
          buttonNext: {
            borderRadius: '12px',
            fontWeight: 600,
            padding: '10px 18px',
            fontSize: '0.95rem',
            backgroundColor: 'var(--accent)',
            color: '#fff',
            border: 'none',
            boxShadow: '0 8px 24px rgba(88, 166, 255, 0.25)',
            transition: 'all 0.2s ease',
          },
          buttonBack: {
            color: 'var(--text-secondary)',
            marginRight: 12,
            backgroundColor: 'transparent',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            borderRadius: '12px',
            padding: '10px 18px',
            fontWeight: 500,
            transition: 'all 0.2s ease',
            cursor: 'pointer',
          },
          buttonSkip: {
            color: 'var(--text-secondary)',
            backgroundColor: 'transparent',
            border: 'none',
            fontSize: '0.95rem',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'color 0.2s ease',
          },
          tooltip: {
            fontSize: '0.95rem',
            lineHeight: '1.6',
          },
          tooltipTitle: {
            fontSize: '1.05rem',
            fontWeight: 700,
            marginBottom: '8px',
            color: 'var(--accent)',
          },
          badge: {
            backgroundColor: 'rgba(88, 166, 255, 0.15)',
            color: 'var(--accent)',
            borderRadius: '8px',
            padding: '4px 10px',
            fontSize: '0.75rem',
            fontWeight: 600,
            border: '1px solid rgba(88, 166, 255, 0.25)',
          },
        }}
      />
      <div className="workspace-ambient workspace-ambient-a" />
      <div className="workspace-ambient workspace-ambient-b" />
      <div className="sidebar workspace-sidebar tour-sidebar">
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
            const tourClass = `tour-nav-${item.name.replace(/\s+/g, '-')}`;
            return (
              <Link key={item.path} to={item.path}
                className={`nav-item workspace-nav-item ${isActive ? 'active' : ''} ${tourClass}`}
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
            <div className="workspace-account-avatar" style={{ overflow: 'hidden', padding: 0 }}>
              {currentUser.avatar_url
                ? <img src={currentUser.avatar_url} alt="avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                : (currentUser.name || currentUser.email || 'U').charAt(0).toUpperCase()}
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
            {role === 'admin' && openReviewRequests > 0 && (
              <Link
                to="/app/review?request=open"
                className="workspace-notification-pill"
                title="Open admin review requests"
              >
                <Bell size={14} />
                <span>{openReviewRequests} review request{openReviewRequests === 1 ? '' : 's'}</span>
              </Link>
            )}
            {role !== 'admin' && assignedReviewRequests > 0 && (
              <Link
                to="/app/review?request=assigned&assigned_to_me=true&reviewed=false"
                className="workspace-notification-pill"
                title="Assigned review requests"
              >
                <Bell size={14} />
                <span>{assignedReviewRequests} assigned review{assignedReviewRequests === 1 ? '' : 's'}</span>
              </Link>
            )}
            {role === 'editor' && resolvedReviewRequests > 0 && (
              <Link
                to={resolvedReviewLink}
                className="workspace-notification-pill workspace-notification-pill-success"
                title="Resolved review requests ready in Organized Videos"
              >
                <CheckCircle size={14} />
                <span>{resolvedReviewRequests} resolved request{resolvedReviewRequests === 1 ? '' : 's'}</span>
              </Link>
            )}
            <button 
              className="btn workspace-ghost-btn tour-start-btn"
              onClick={() => setRunTour(true)}
              style={{ gap: '8px' }}
            >
              <Zap size={14} color="var(--accent)" fill="var(--accent)" style={{ opacity: 0.8 }} />
              Start Tour
            </button>
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
