import React from 'react';
import { Outlet, useLocation, Link } from 'react-router-dom';
import { LayoutDashboard, UploadCloud, Grid, Wand2, Shield, LogOut, CheckSquare, Users, Activity } from 'lucide-react';

export default function AppShell({ currentUser, onLogout }) {
  const location = useLocation();
  const role = currentUser?.role || 'editor';

  const navItems = [
    { name: 'Dashboard', path: '/app/dashboard', icon: LayoutDashboard, roles: ['admin', 'reviewer', 'editor'] },
    { name: 'Review Queue', path: '/app/review', icon: CheckSquare, roles: ['admin', 'reviewer'] },
    { name: 'Users', path: '/app/admin/users', icon: Users, roles: ['admin'] },
    { name: 'Job Monitor', path: '/app/admin/jobs', icon: Activity, roles: ['admin'] },
    { name: 'Uploads', path: '/app/uploads', icon: UploadCloud, roles: ['admin', 'editor'] },
    { name: 'Exports', path: '/app/exports', icon: Grid, roles: ['admin', 'editor'] },
  ];

  const visibleNav = navItems.filter(item => item.roles.includes(role));
  const activeNav = visibleNav.find(n => location.pathname.startsWith(n.path));

  return (
    <div className="app-container">
      <div className="sidebar">
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', marginBottom: 'var(--space-32)' }}>
          <div style={{ width: 32, height: 32, borderRadius: 'var(--radius-md)', background: 'rgba(88,166,255,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(88,166,255,0.2)' }}>
            <Wand2 size={18} color="var(--accent)" />
          </div>
          <span style={{ fontWeight: 700, fontSize: 'var(--font-title-card)', letterSpacing: '-0.01em' }}>EditEase</span>
        </div>

        <div style={{ color: 'var(--text-muted)', fontSize: 'var(--font-meta)', textTransform: 'uppercase', letterSpacing: '0.07em', padding: '0 var(--space-16)', marginBottom: 'var(--space-8)' }}>
          Navigation
        </div>

        <nav style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {visibleNav.map((item, idx) => {
            const isActive = location.pathname.startsWith(item.path);
            return (
              <Link
                to={item.path}
                key={item.path}
                className={`nav-item stagger-item link-draw ${isActive ? 'active' : ''}`}
                style={{ position: 'relative', overflow: 'hidden', animationDelay: `${idx * 0.06}s` }}
              >
                {isActive && (
                  <span style={{
                    position: 'absolute',
                    left: 0,
                    top: 0,
                    bottom: 0,
                    width: 3,
                    background: 'var(--accent)',
                    borderRadius: '0 2px 2px 0',
                    animation: 'fadeIn 0.2s ease'
                  }} />
                )}
                <item.icon size={18} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Bottom account */}
        <div style={{ marginTop: 'auto', paddingTop: 'var(--space-16)', borderTop: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-12)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', color: 'var(--text-secondary)', fontSize: 'var(--font-small)', textTransform: 'capitalize' }}>
              <Shield size={14} /> {role}
            </div>
            <button
              onClick={onLogout}
              style={{ background: 'transparent', border: 'none', color: 'var(--danger)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 'var(--space-4)', fontSize: 'var(--font-small)', padding: 'var(--space-4)', borderRadius: 'var(--radius-sm)', transition: 'opacity 0.15s' }}
              onMouseEnter={e => e.currentTarget.style.opacity = '0.7'}
              onMouseLeave={e => e.currentTarget.style.opacity = '1'}
            >
              <LogOut size={14} /> Logout
            </button>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)', overflow: 'hidden', padding: 'var(--space-8)', background: 'var(--surface-base)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ minWidth: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, var(--accent) 0%, #1f6feb 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: 'var(--font-body)', flexShrink: 0 }}>
              {currentUser.username.charAt(0).toUpperCase()}
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontWeight: 500, fontSize: 'var(--font-small)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {currentUser.name || currentUser.username}
              </div>
              <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                {role}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Top bar + content */}
      <div className="main-wrapper">
        <div style={{ height: 56, borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', padding: '0 var(--space-40)', justifyContent: 'space-between', backgroundColor: 'var(--surface-panel)', flexShrink: 0 }}>
          <span style={{ fontWeight: 600, fontSize: 'var(--font-title-card)', letterSpacing: '-0.01em' }}>
            {activeNav?.name || 'Dashboard'}
          </span>
          <span className="badge info" style={{ margin: 0 }}>
            {role}
          </span>
        </div>

        <div className="main-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
