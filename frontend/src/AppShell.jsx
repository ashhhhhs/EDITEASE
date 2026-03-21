import React from 'react';
import { Outlet, useLocation, Link } from 'react-router-dom';
import { LayoutDashboard, UploadCloud, Grid, Wand2, Shield, LogOut, CheckSquare } from 'lucide-react';

export default function AppShell({ currentUser, onLogout }) {
  const location = useLocation();

  const role = currentUser?.role || 'editor';

  const navItems = [
    { name: 'Dashboard', path: '/app/dashboard', icon: LayoutDashboard, roles: ['admin', 'reviewer', 'editor'] },
    { name: 'Review Queue', path: '/app/review', icon: CheckSquare, roles: ['admin', 'reviewer'] },
    { name: 'Uploads', path: '/app/uploads', icon: UploadCloud, roles: ['admin', 'editor'] },
    { name: 'Exports', path: '/app/exports', icon: Grid, roles: ['admin', 'editor'] },
  ];

  const visibleNav = navItems.filter(item => item.roles.includes(role));

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <h1><Wand2 size={24} color="#58a6ff" /> EditEase</h1>

        <div style={{color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.1em', padding: '0.5rem 1rem', marginBottom: '0.25rem'}}>
          Navigation
        </div>

        {visibleNav.map(item => (
          <Link 
            to={item.path} 
            key={item.path} 
            className={`nav-item ${location.pathname.startsWith(item.path) ? 'active' : ''}`}
            style={{ textDecoration: 'none' }}
          >
            <item.icon size={20} /> {item.name}
          </Link>
        ))}

        {/* Bottom info */}
        <div style={{marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-color)'}}>
          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'capitalize'}}>
              <Shield size={14} />
              {role}
            </div>
            <button 
              onClick={onLogout}
              style={{background: 'transparent', border: 'none', color: 'var(--danger)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem'}}
            >
              <LogOut size={14} /> Logout
            </button>
          </div>
          <div style={{marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem', overflow: 'hidden'}}>
             <div style={{minWidth: 24, height: 24, borderRadius: '50%', background: 'linear-gradient(135deg, var(--accent), #1f6feb)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '0.75rem', fontWeight: 'bold'}}>
               {currentUser.username.charAt(0).toUpperCase()}
             </div>
             <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{currentUser.name || currentUser.username}</span>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
        <div style={{ height: '60px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', padding: '0 2rem', justifyContent: 'space-between', backgroundColor: 'var(--panel-bg)' }}>
          <h2 style={{ fontSize: '1.25rem', margin: 0 }}>
            {visibleNav.find(n => location.pathname.startsWith(n.path))?.name || 'Dashboard'}
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span className="badge" style={{ margin: 0, padding: '0.4rem 0.8rem' }}>Role: {role}</span>
          </div>
        </div>
        
        <div className="main-content" style={{ padding: '2rem', flex: 1, overflowY: 'auto' }}>
          <Outlet />
        </div>
      </div>
    </div>
  );
}
