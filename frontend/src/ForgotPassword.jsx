import React, { useState } from 'react';
import { ShieldAlert, Loader2, ArrowLeft, MailCheck } from 'lucide-react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { API_BASE } from './config';

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
      <div className="app-container" style={{ alignItems: 'center', justifyContent: 'center', background: 'radial-gradient(circle at 50% 0%, var(--surface-panel) 0%, var(--surface-base) 100%)' }}>
        <div className="panel" style={{ width: '100%', maxWidth: '400px', boxShadow: '0 24px 64px rgba(0,0,0,0.4)', border: '1px solid var(--border-default)', textAlign: 'center' }}>
          
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-16)', marginBottom: 'var(--space-24)' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '16px', background: 'rgba(56, 139, 253, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(56, 139, 253, 0.2)' }}>
              <MailCheck size={32} color="#58a6ff" />
            </div>
            <h2 style={{ margin: 0, fontSize: 'var(--font-title-section)', fontWeight: 600 }}>Check your inbox</h2>
          </div>
          
          <p style={{ color: 'var(--text-secondary)', fontSize: '15px', lineHeight: 1.6, marginBottom: 'var(--space-24)' }}>
            If an account exists for <strong style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{email}</strong>, you will receive a password reset link shortly.
            Links expire in 15 minutes.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
            <Link to="/login" className="btn btn-secondary" style={{ width: '100%', padding: 'var(--space-12)', fontSize: '1rem', justifyContent: 'center' }}>
              Back to sign in
            </Link>
            
            <p style={{ margin: 0, fontSize: 'var(--font-small)', color: 'var(--text-muted)' }}>
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
        </div>
      </div>
    );
  }

  return (
    <div className="app-container" style={{ alignItems: 'center', justifyContent: 'center', background: 'radial-gradient(circle at 50% 0%, var(--surface-panel) 0%, var(--surface-base) 100%)' }}>
      <div className="panel" style={{ width: '100%', maxWidth: '400px', boxShadow: '0 24px 64px rgba(0,0,0,0.4)', border: '1px solid var(--border-default)' }}>
        
        <Link to="/login" style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-4)', color: 'var(--text-muted)', textDecoration: 'none', fontSize: 'var(--font-small)', marginBottom: 'var(--space-24)', transition: 'color 0.2s' }} onMouseEnter={e => e.currentTarget.style.color='var(--text-primary)'} onMouseLeave={e => e.currentTarget.style.color='var(--text-muted)'}>
          <ArrowLeft size={16} /> Back
        </Link>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-12)', marginBottom: 'var(--space-32)' }}>
          <h2 style={{ margin: 0, fontSize: 'var(--font-title-section)', fontWeight: 600 }}>Forgot your password?</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '15px', lineHeight: 1.5 }}>
            Enter your email and we'll send you a reset link.
          </p>
        </div>
        
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
      </div>
    </div>
  );
}
