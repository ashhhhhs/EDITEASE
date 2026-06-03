import React, { useState, useRef } from 'react';
import { User, Lock, Smartphone, ShieldAlert, Camera } from 'lucide-react';
import api from './lib/api';
import PageHeader from './components/PageHeader';

export default function Settings({ currentUser, onUserUpdate }) {
  const [activeTab, setActiveTab] = useState('profile');

  return (
    <div style={{ padding: 'var(--space-24) var(--space-40)', maxWidth: 800 }}>
      <PageHeader 
        title="Account Settings" 
        description="Manage your profile, security preferences, and connected accounts." 
      />

      <div style={{ display: 'flex', gap: 'var(--space-32)' }}>
        {/* Sidebar Tabs */}
        <div style={{ width: 200, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <TabButton active={activeTab === 'profile'} onClick={() => setActiveTab('profile')} icon={<User size={16} />}>Profile</TabButton>
          <TabButton active={activeTab === 'security'} onClick={() => setActiveTab('security')} icon={<Lock size={16} />}>Security</TabButton>
          <TabButton active={activeTab === 'danger'} onClick={() => setActiveTab('danger')} icon={<ShieldAlert size={16} />} danger>Danger Zone</TabButton>
        </div>

        {/* Content Area */}
        <div style={{ flex: 1, background: 'var(--surface-panel)', padding: 'var(--space-32)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-default)' }}>
          {activeTab === 'profile' && <ProfileSection currentUser={currentUser} onUserUpdate={onUserUpdate} />}
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

function ProfileSection({ currentUser, onUserUpdate }) {
  const [name, setName] = useState(currentUser.name || '');
  const [avatarPreview, setAvatarPreview] = useState(currentUser.avatar_url || null);
  const [avatarFile, setAvatarFile] = useState(null);
  const [status, setStatus] = useState({ loading: false, error: null, success: false });
  const fileInputRef = useRef(null);

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setAvatarFile(file);
    setAvatarPreview(URL.createObjectURL(file));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() && !avatarFile) return;
    setStatus({ loading: true, error: null, success: false });
    try {
      const fd = new FormData();
      if (name.trim()) fd.append('name', name.trim());
      if (avatarFile) fd.append('avatar', avatarFile);
      const res = await api.patch('/user/profile', fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setStatus({ loading: false, error: null, success: true });
      setAvatarFile(null);
      if (onUserUpdate) onUserUpdate(res.data.user);
      setTimeout(() => setStatus(s => ({ ...s, success: false })), 3000);
    } catch (err) {
      setStatus({ loading: false, error: err.response?.data?.error || 'Failed to update profile', success: false });
    }
  };

  const initials = (currentUser.name || currentUser.email || '?')
    .split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);

  return (
    <div>
      <h2 style={{ fontSize: '18px', margin: '0 0 var(--space-24)' }}>Profile Settings</h2>

      {/* Avatar picker */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-20)', marginBottom: 'var(--space-32)' }}>
        <div style={{ position: 'relative', flexShrink: 0 }}>
          <div style={{
            width: 72, height: 72, borderRadius: '50%',
            background: avatarPreview ? 'transparent' : 'var(--surface-active)',
            border: '2px solid var(--border-default)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            overflow: 'hidden', fontSize: '22px', fontWeight: 600, color: 'var(--text-secondary)'
          }}>
            {avatarPreview
              ? <img src={avatarPreview} alt="avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              : initials}
          </div>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            style={{
              position: 'absolute', bottom: 0, right: 0,
              width: 24, height: 24, borderRadius: '50%',
              background: 'var(--accent-blue)', border: 'none',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', color: '#fff'
            }}
          >
            <Camera size={12} />
          </button>
          <input ref={fileInputRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleAvatarChange} />
        </div>
        <div>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>{currentUser.name || '—'}</div>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{currentUser.email}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{currentUser.role}</div>
        </div>
      </div>

      <div style={{ height: 1, background: 'var(--border-subtle)', margin: 'var(--space-24) 0' }} />

      <form onSubmit={handleSubmit}>
        {status.error && <div className="toast toast-error" style={{ marginBottom: 'var(--space-16)' }}>{status.error}</div>}
        {status.success && <div className="toast toast-success" style={{ marginBottom: 'var(--space-16)' }}>Profile updated.</div>}

        <div className="input-group" style={{ marginBottom: 'var(--space-20)' }}>
          <label>Display name</label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Your name"
            maxLength={80}
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={status.loading || (!name.trim() && !avatarFile)}>
          {status.loading ? 'Saving...' : 'Save changes'}
        </button>
      </form>
    </div>
  );
}

function SecuritySection({ currentUser }) {
  const [hasPasswordOverride, setHasPasswordOverride] = useState(null);
  const hasPassword = hasPasswordOverride !== null ? hasPasswordOverride : (currentUser?.has_password ?? true);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otpCooldown, setOtpCooldown] = useState(0);
  const [status, setStatus] = useState({ loading: false, error: null, success: false });
  const [otpLoading, setOtpLoading] = useState(false);

  const mismatch = confirmPassword && newPassword !== confirmPassword;

  const handleSendOtp = async () => {
    setOtpLoading(true);
    setStatus(s => ({ ...s, error: null }));
    try {
      await api.post('/user/password/otp');
      setOtpSent(true);
      setOtpCooldown(60);
      const interval = setInterval(() => {
        setOtpCooldown(c => {
          if (c <= 1) { clearInterval(interval); return 0; }
          return c - 1;
        });
      }, 1000);
    } catch (err) {
      if (err.response?.status === 400 && err.response?.data?.error?.includes('already has a password')) {
        setHasPasswordOverride(true);
      } else {
        setStatus(s => ({ ...s, error: err.response?.data?.error || 'Failed to send code.' }));
      }
    } finally {
      setOtpLoading(false);
    }
  };

  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setStatus({ loading: false, error: 'New passwords do not match.', success: false });
      return;
    }
    setStatus({ loading: true, error: null, success: false });
    try {
      const body = { new_password: newPassword };
      if (hasPassword) body.current_password = currentPassword;
      else body.otp = otp.trim();
      const res = await api.patch('/user/password', body);
      localStorage.setItem('token', res.data.token);
      setStatus({ loading: false, error: null, success: true });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setOtp('');
      setOtpSent(false);
    } catch (err) {
      setStatus({ loading: false, error: err.response?.data?.error || 'Failed to update password', success: false });
    }
  };

  return (
    <div>
      <h2 style={{ fontSize: '18px', margin: '0 0 var(--space-24)' }}>Security</h2>

      <form onSubmit={handleUpdatePassword}>
        <h3 style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: '0 0 var(--space-16)' }}>
          {hasPassword ? 'Change Password' : 'Set a Password'}
        </h3>

        {!hasPassword && (
          <div style={{ marginBottom: 'var(--space-16)', background: 'rgba(88,166,255,0.08)', border: '1px solid rgba(88,166,255,0.25)', borderRadius: 'var(--radius-md)', padding: 'var(--space-12) var(--space-16)', fontSize: '13px', color: 'var(--accent-blue, #58a6ff)' }}>
            Your account uses Google sign-in. We'll send a verification code to <strong>{currentUser?.email}</strong> before you can set a password.
          </div>
        )}

        {status.error && <div className="toast toast-error" style={{ marginBottom: 'var(--space-16)' }}>{status.error}</div>}
        {status.success && (
          <div className="toast toast-success" style={{ marginBottom: 'var(--space-16)' }}>
            {hasPassword ? 'Password updated successfully. Other devices have been signed out.' : 'Password set. You can now sign in with your email and password.'}
          </div>
        )}

        {hasPassword ? (
          <div className="input-group" style={{ marginBottom: 'var(--space-16)' }}>
            <label>Current Password</label>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={currentPassword}
              onChange={e => setCurrentPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>
        ) : (
          <div className="input-group" style={{ marginBottom: 'var(--space-16)' }}>
            <label>Verification Code</label>
            <div style={{ display: 'flex', gap: 'var(--space-8)' }}>
              <input
                type="text"
                inputMode="numeric"
                pattern="\d{6}"
                maxLength={6}
                required
                value={otp}
                onChange={e => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="6-digit code"
                style={{ flex: 1, letterSpacing: '0.2em', textAlign: 'center', fontSize: '18px' }}
              />
              <button
                type="button"
                className="btn"
                onClick={handleSendOtp}
                disabled={otpLoading || otpCooldown > 0}
                style={{ flexShrink: 0, whiteSpace: 'nowrap' }}
              >
                {otpLoading ? 'Sending...' : otpCooldown > 0 ? `Resend in ${otpCooldown}s` : otpSent ? 'Resend code' : 'Send code'}
              </button>
            </div>
            {otpSent && (
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px', display: 'block' }}>
                Code sent to {currentUser?.email}. Check your inbox — expires in 10 minutes.
              </span>
            )}
          </div>
        )}

        <div className="input-group" style={{ marginBottom: 'var(--space-16)' }}>
          <label>New Password</label>
          <input
            type="password"
            required
            autoComplete="new-password"
            value={newPassword}
            onChange={e => setNewPassword(e.target.value)}
            placeholder="••••••••"
            minLength={8}
          />
        </div>
        <div className="input-group" style={{ marginBottom: 'var(--space-16)' }}>
          <label>Retype New Password</label>
          <input
            type="password"
            required
            autoComplete="new-password"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            placeholder="••••••••"
            style={mismatch ? { borderColor: 'var(--danger)' } : undefined}
          />
          {mismatch && (
            <span style={{ fontSize: '12px', color: 'var(--danger)', marginTop: '4px', display: 'block' }}>
              Passwords do not match.
            </span>
          )}
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={
            status.loading ||
            (hasPassword && !currentPassword) ||
            (!hasPassword && otp.length !== 6) ||
            !newPassword || !confirmPassword || mismatch
          }
        >
          {status.loading ? (hasPassword ? 'Updating...' : 'Setting...') : (hasPassword ? 'Update Password' : 'Set Password')}
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
      localStorage.setItem('token', res.data.token);
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

      </div>
    </div>
  );
}
