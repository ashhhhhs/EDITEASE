import React, { useState } from 'react';
import { Mail, Lock, LogOut, Trash2, Smartphone, ShieldAlert } from 'lucide-react';
import api from './lib/api';

export default function Settings({ currentUser }) {
  const [activeTab, setActiveTab] = useState('profile');

  return (
    <div style={{ padding: 'var(--space-24) var(--space-40)', maxWidth: 800 }}>
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-32)' }}>
        <h1 style={{ margin: '0 0 var(--space-8) 0', fontSize: '24px', fontWeight: 600 }}>Account Settings</h1>
        <p style={{ margin: 0, color: 'var(--text-secondary)' }}>Manage your profile, security preferences, and connected accounts.</p>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-32)' }}>
        {/* Sidebar Tabs */}
        <div style={{ width: 200, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <TabButton active={activeTab === 'profile'} onClick={() => setActiveTab('profile')} icon={<Mail size={16} />}>Profile</TabButton>
          <TabButton active={activeTab === 'security'} onClick={() => setActiveTab('security')} icon={<Lock size={16} />}>Security</TabButton>
          <TabButton active={activeTab === 'danger'} onClick={() => setActiveTab('danger')} icon={<ShieldAlert size={16} />} danger>Danger Zone</TabButton>
        </div>

        {/* Content Area */}
        <div style={{ flex: 1, background: 'var(--surface-panel)', padding: 'var(--space-32)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-default)' }}>
          {activeTab === 'profile' && <ProfileSection currentUser={currentUser} />}
          {activeTab === 'security' && <SecuritySection currentUser={currentUser} />}
          {activeTab === 'danger' && <DangerZoneSection />}
        </div>
      </div>
    </div>
  );
}

function TabButton({ active, onClick, icon, children, danger }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 'var(--space-12)', padding: 'var(--space-12) var(--space-16)',
        width: '100%', textAlign: 'left', background: active ? (danger ? 'rgba(218,54,51,0.1)' : 'var(--surface-active)') : 'transparent',
        border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer',
        color: danger ? 'var(--danger)' : (active ? 'var(--text-primary)' : 'var(--text-secondary)'),
        fontWeight: active ? 500 : 400,
        transition: 'all 0.15s ease'
      }}
      onMouseEnter={e => !active && (e.currentTarget.style.background = 'var(--surface-hover)')}
      onMouseLeave={e => !active && (e.currentTarget.style.background = 'transparent')}
    >
      {icon} {children}
    </button>
  );
}

function ProfileSection({ currentUser }) {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState({ loading: false, error: null, success: false });

  const handleUpdateEmail = async (e) => {
    e.preventDefault();
    setStatus({ loading: true, error: null, success: false });
    try {
      await api.patch('/user/email', { email });
      setStatus({ loading: false, error: null, success: true });
      setEmail('');
      // In a real app we might force a page reload or update context
      setTimeout(() => window.location.reload(), 2000);
    } catch (err) {
      setStatus({ loading: false, error: err.response?.data?.error || 'Failed to update email', success: false });
    }
  };

  return (
    <div>
      <h2 style={{ fontSize: '18px', margin: '0 0 var(--space-24)' }}>Profile Settings</h2>
      
      <div style={{ marginBottom: 'var(--space-32)' }}>
        <h3 style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: '0 0 var(--space-8)' }}>Current Email</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)' }}>
          <div style={{ fontWeight: 500 }}>{currentUser.email}</div>
          {currentUser.email_verified ? (
            <span className="badge tag">Verified</span>
          ) : (
            <span className="badge warning">Unverified</span>
          )}
        </div>
      </div>

      <div style={{ height: 1, background: 'var(--border-subtle)', margin: 'var(--space-24) 0' }} />

      <form onSubmit={handleUpdateEmail}>
        <h3 style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: '0 0 var(--space-16)' }}>Change Email Address</h3>
        {status.error && <div className="toast toast-error" style={{ marginBottom: 'var(--space-16)' }}>{status.error}</div>}
        {status.success && <div className="toast toast-success" style={{ marginBottom: 'var(--space-16)' }}>Email updated successfully. Please check your new inbox to verify it.</div>}
        
        <div className="input-group" style={{ marginBottom: 'var(--space-16)' }}>
          <label>New Email</label>
          <input 
            type="email" 
            required 
            value={email} 
            onChange={e => setEmail(e.target.value)} 
            placeholder="new@example.com"
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={status.loading || !email}>
          {status.loading ? 'Updating...' : 'Update Email'}
        </button>
      </form>
    </div>
  );
}

function SecuritySection({ currentUser }) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [status, setStatus] = useState({ loading: false, error: null, success: false });

  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    setStatus({ loading: true, error: null, success: false });
    try {
      const res = await api.patch('/user/password', { current_password: currentPassword, new_password: newPassword });
      localStorage.setItem('auth_token', res.data.token); // update the token!
      setStatus({ loading: false, error: null, success: true });
      setCurrentPassword('');
      setNewPassword('');
    } catch (err) {
      setStatus({ loading: false, error: err.response?.data?.error || 'Failed to update password', success: false });
    }
  };

  return (
    <div>
      <h2 style={{ fontSize: '18px', margin: '0 0 var(--space-24)' }}>Security</h2>
      
      <form onSubmit={handleUpdatePassword}>
        <h3 style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: '0 0 var(--space-16)' }}>Change Password</h3>
        {status.error && <div className="toast toast-error" style={{ marginBottom: 'var(--space-16)' }}>{status.error}</div>}
        {status.success && <div className="toast toast-success" style={{ marginBottom: 'var(--space-16)' }}>Password updated successfully. Other devices have been signed out.</div>}
        
        <div className="input-group" style={{ marginBottom: 'var(--space-16)' }}>
          <label>Current Password</label>
          <input 
            type="password" 
            required 
            value={currentPassword} 
            onChange={e => setCurrentPassword(e.target.value)} 
            placeholder="••••••••"
          />
        </div>
        <div className="input-group" style={{ marginBottom: 'var(--space-16)' }}>
          <label>New Password</label>
          <input 
            type="password" 
            required 
            value={newPassword} 
            onChange={e => setNewPassword(e.target.value)} 
            placeholder="••••••••"
            minLength={8}
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={status.loading || !currentPassword || !newPassword}>
          {status.loading ? 'Updating...' : 'Update Password'}
        </button>
      </form>
    </div>
  );
}

function DangerZoneSection() {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSignOutAll = async () => {
    if(!window.confirm("Are you sure you want to sign out all other devices? You will remain signed in here.")) return;
    setLoading(true);
    try {
      const res = await api.post('/user/logout-all');
      localStorage.setItem('auth_token', res.data.token);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch(err) {
      alert("Failed to sign out devices");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 style={{ fontSize: '18px', margin: '0 0 var(--space-24)', color: 'var(--danger)' }}>Danger Zone</h2>
      
      <div style={{ border: '1px solid var(--danger)', borderRadius: 'var(--radius-md)', padding: 'var(--space-20)', background: 'rgba(218,54,51,0.02)' }}>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-24)' }}>
          <div>
            <h4 style={{ margin: '0 0 var(--space-4)', fontSize: '15px' }}>Sign out all devices</h4>
            <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>Instantly revoke access for all other active sessions across all devices.</p>
          </div>
          <button onClick={handleSignOutAll} disabled={loading} className="btn" style={{ borderColor: 'var(--border-default)', whiteSpace: 'nowrap' }}>
            <Smartphone size={16} /> {loading ? 'Processing...' : 'Sign Out All Devices'}
          </button>
        </div>
        
        {success && <div style={{ color: 'var(--success)', fontSize: '13px', marginBottom: 'var(--space-24)' }}>Successfully signed out all other devices.</div>}

        <div style={{ height: 1, background: 'rgba(218,54,51,0.2)', margin: 'var(--space-20) 0' }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h4 style={{ margin: '0 0 var(--space-4)', fontSize: '15px', color: 'var(--danger)' }}>Delete Account</h4>
            <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>Permanently remove your account and all associated data. This cannot be undone.</p>
          </div>
          <button onClick={() => alert("Account deletion not yet available.")} className="btn" style={{ color: 'var(--danger)', borderColor: 'rgba(218,54,51,0.3)', whiteSpace: 'nowrap' }}>
            <Trash2 size={16} /> Delete Account
          </button>
        </div>

      </div>
    </div>
  );
}
