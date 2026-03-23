import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Mail, Shield, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react';
import api from './lib/api';

export default function Invite({ currentUser }) {
  const { token } = useParams();
  const navigate = useNavigate();
  
  const [inviteData, setInviteData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [accepting, setAccepting] = useState(false);

  useEffect(() => {
    // Fetch invite details
    api.get(`/invite/${token}`)
      .then(res => {
        setInviteData(res.data.invite || res.data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.response?.data?.error || 'Invalid or expired invitation link');
        setLoading(false);
      });
  }, [token]);

  const handleAccept = async () => {
    setAccepting(true);
    try {
      await api.post(`/invite/${token}/accept`);
      // Update the user state if possible, but dashboard redirect is fine
      navigate('/app/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to accept invitation');
      setAccepting(false);
    }
  };

  const savePendingAndNavigate = (path) => {
    localStorage.setItem('pending_invite', token);
    navigate(path);
  };

  if (loading) {
    return (
      <div className="auth-container">
        <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>Loading invitation...</div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="card auth-card" style={{ maxWidth: 460 }}>
        {/* Logo Header */}
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-32)' }}>
          <div style={{ display: 'inline-flex', padding: 12, background: 'var(--surface-active)', borderRadius: '50%', marginBottom: 'var(--space-16)' }}>
            <Mail size={24} color="var(--accent)" />
          </div>
          <h1 className="auth-title">Team Invitation</h1>
          {!error && (
            <p className="auth-subtitle">You have been invited to join an EditEase workspace.</p>
          )}
        </div>

        {error ? (
          <div style={{ textAlign: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--danger)', marginBottom: 'var(--space-16)' }}>
              <AlertTriangle size={32} />
            </div>
            <p style={{ color: 'var(--text-primary)', marginBottom: 'var(--space-24)' }}>{error}</p>
            <Link to="/" className="btn" style={{ width: '100%', justifyContent: 'center' }}>
              Return to Home
            </Link>
          </div>
        ) : (
          <div>
            <div style={{ background: 'var(--surface-base)', padding: 'var(--space-20)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-default)', marginBottom: 'var(--space-32)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-12)' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Invited Email</span>
                <span style={{ fontWeight: 500, fontSize: '14px' }}>{inviteData.email}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-12)' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Role</span>
                <span style={{ fontWeight: 500, fontSize: '14px', textTransform: 'capitalize', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Shield size={14} /> {inviteData.role}
                </span>
              </div>
            </div>

            {currentUser ? (
              // Logged in — but check if email matches
              currentUser.email === inviteData.email ? (
                <div>
                  <button onClick={handleAccept} disabled={accepting} className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginBottom: 'var(--space-16)' }}>
                    {accepting ? 'Accepting...' : 'Accept Invitation'} <CheckCircle size={16} />
                  </button>
                  <p style={{ textAlign: 'center', fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
                    You are logged in as <strong>{currentUser.email}</strong>.
                  </p>
                </div>
              ) : (
                <div style={{ background: 'rgba(218,54,51,0.1)', color: 'var(--danger)', padding: 'var(--space-16)', borderRadius: 'var(--radius-md)', fontSize: '14px', textAlign: 'center' }}>
                  You are currently logged in as <strong>{currentUser.email}</strong>, but this invite is for <strong>{inviteData.email}</strong>. Please sign out and sign in with the correct account.
                </div>
              )
            ) : (
              // Not logged in
              <div>
                <p style={{ textAlign: 'center', fontSize: '14px', marginBottom: 'var(--space-24)' }}>
                  To accept this invitation, you need to sign in or create an account with <strong>{inviteData.email}</strong>.
                </p>
                <div style={{ display: 'flex', gap: 'var(--space-12)' }}>
                  <button onClick={() => savePendingAndNavigate('/register')} className="btn btn-primary" style={{ flex: 1, justifyContent: 'center' }}>
                    Create Account
                  </button>
                  <button onClick={() => savePendingAndNavigate('/login')} className="btn" style={{ flex: 1, justifyContent: 'center', backgroundColor: 'var(--surface-elevated)' }}>
                    Sign In <ArrowRight size={16} />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
