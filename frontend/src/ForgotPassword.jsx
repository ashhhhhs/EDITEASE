import React, { useState } from 'react';
import { ShieldAlert, Loader2, ArrowLeft, MailCheck } from 'lucide-react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { API_BASE } from './config';
import AuthShell from './components/AuthShell';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (!email) return;
    
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/forgot-password`, { email });
      setSubmitted(true);
      startCooldown();
    } catch (err) {
      // Even errors should look like success to prevent enumeration,
      // but axios might throw on network errors. We still show the
      // generic success screen.
      setSubmitted(true);
      startCooldown();
    } finally {
      setLoading(false);
    }
  };

  const startCooldown = () => {
    setResendCooldown(60);
    const interval = setInterval(() => {
      setResendCooldown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  if (submitted) {
    return (
      <AuthShell title="Check your inbox" icon={MailCheck}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '15px', lineHeight: 1.6, marginBottom: 'var(--space-24)', textAlign: 'center' }}>
            If an account exists for <strong style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{email}</strong>, you will receive a password reset link shortly.
            Links expire in 15 minutes.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
            <Link to="/login" className="btn btn-secondary" style={{ width: '100%', padding: 'var(--space-12)', fontSize: '1rem', justifyContent: 'center' }}>
              Back to sign in
            </Link>
            
            <p style={{ margin: 0, fontSize: 'var(--font-small)', color: 'var(--text-muted)', textAlign: 'center' }}>
              Didn't receive it?{' '}
              {resendCooldown > 0 ? (
                <span>Resend available in {resendCooldown}s</span>
              ) : (
                <button onClick={handleSubmit} style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', padding: 0, fontSize: 'inherit' }}>
                  Resend email
                </button>
              )}
            </p>
          </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Forgot your password?"
      subtitle="Enter your email and we'll send you a reset link."
      icon={ShieldAlert}
    >
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-20)' }}>
          <div>
            <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Email</label>
            <input 
              type="email" 
              value={email} 
              onChange={e => setEmail(e.target.value)} 
              required 
              placeholder="jane@example.com"
              autoFocus
            />
          </div>
          
          <button type="submit" className="btn btn-primary" style={{ marginTop: 'var(--space-8)', width: '100%', padding: 'var(--space-12)', fontSize: '1rem' }} disabled={loading || !email}>
            {loading ? <><Loader2 size={18} className="spin" /> Sending...</> : 'Send Reset Link'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: 'var(--space-32)' }}>
          <Link to="/login" style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-4)', color: 'var(--text-muted)', textDecoration: 'none', fontSize: 'var(--font-small)', transition: 'color 0.2s' }} onMouseEnter={e => e.currentTarget.style.color='var(--text-primary)'} onMouseLeave={e => e.currentTarget.style.color='var(--text-muted)'}>
            <ArrowLeft size={16} /> Back to Sign In
          </Link>
        </div>
    </AuthShell>
  );
}
