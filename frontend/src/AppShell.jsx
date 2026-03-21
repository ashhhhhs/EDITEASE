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

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <h1><Wand2 size={24} color="var(--accent)" /> EditEase</h1>

        <div style={{color: 'var(--text-muted)', fontSize: 'var(--font-meta)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: 'var(--space-8) var(--space-16)', marginBottom: 'var(--space-4)'}}>
          Navigation
        </div>

        {visibleNav.map(item => (
          <Link 
            to={item.path} 
            key={item.path} 
            className={`nav-item ${location.pathname.startsWith(item.path) ? 'active' : ''}`}
          >
            <item.icon size={20} /> {item.name}
          </Link>
        ))}

        {/* Bottom account info */}
        <div style={{marginTop: 'auto', paddingTop: 'var(--space-16)', borderTop: '1px solid var(--border-subtle)'}}>
          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-12)'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 'var(--space-8)', color: 'var(--text-secondary)', fontSize: 'var(--font-small)', textTransform: 'capitalize'}}>
              <Shield size={16} />
              {role}
            </div>
            <button 
              onClick={onLogout}
              style={{background: 'transparent', border: 'none', color: 'var(--danger)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 'var(--space-4)', fontSize: 'var(--font-small)', padding: 'var(--space-4)', borderRadius: 'var(--radius-sm)'}}
            >
              <LogOut size={16} /> Logout
            </button>
          </div>
          
          <div style={{display: 'flex', alignItems: 'center', gap: 'var(--space-12)', overflow: 'hidden', padding: 'var(--space-8)', background: 'var(--surface-base)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)'}}>
             <div style={{minWidth: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, var(--accent), #1f6feb)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 'var(--font-body)', fontWeight: '600'}}>
               {currentUser.username.charAt(0).toUpperCase()}
             </div>
             <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: 'var(--font-small)', fontWeight: '500', color: 'var(--text-primary)' }}>{currentUser.name || currentUser.username}</span>
          </div>
        </div>
      </div>

      <div className="main-wrapper">
        <div style={{ height: '64px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', padding: '0 var(--space-40)', justifyContent: 'space-between', backgroundColor: 'var(--surface-panel)' }}>
          <h2 style={{ fontSize: 'var(--font-title-card)', margin: 0, fontWeight: 600, color: 'var(--text-primary)' }}>
            {visibleNav.find(n => location.pathname.startsWith(n.path))?.name || 'Dashboard'}
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-16)' }}>
            <span className="badge info" style={{ margin: 0 }}>Role: {role}</span>
          </div>
        </div>
        
        <div className="main-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
