import React, { useState } from 'react';
import { Wand2, AlertTriangle, Loader2, Eye, EyeOff } from 'lucide-react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { API_BASE } from './config';
import AuthShell from './components/AuthShell';

export default function Login({ onLogin, currentUser, onLogout }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/login`, { email, password });
      if (res.data.token) {
        onLogin(res.data.token, res.data.user || res.data);
      } else {
        setError(res.data.error || 'Login failed');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error connecting to server');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    setError(null);
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/auth/google`, {
        token: credentialResponse.credential
      });
      if (res.data.token) {
        onLogin(res.data.token, res.data.user || res.data);
      } else {
        setError(res.data.error || 'Google login failed');
      }
    } catch (err) {
      if (err.response?.data?.code === 'ACCOUNT_EXISTS_NEEDS_LINKING') {
        setError(err.response.data.error);
        localStorage.setItem('pending_google_link', JSON.stringify({
           ...err.response.data.pending_link,
           token: credentialResponse.credential
        }));
      } else {
        setError(err.response?.data?.error || 'Error connecting to server');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = () => {
    setError("Google sign in was unsuccessful. Try again later.");
  };

  if (currentUser && !currentUser.email_verified) {
    return (
      <AuthShell 
        title="Verify Your Email" 
        subtitle="You need to verify your email address to access your workspace."
      >
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-24)', color: 'var(--text-secondary)' }}>
          We've sent a verification link to <strong>{currentUser.email}</strong>.
          Please check your inbox and click the link to activate your account.
        </div>
        <button 
          onClick={onLogout} 
          className="btn" 
          style={{ width: '100%', justifyContent: 'center' }}
        >
          Sign Out
        </button>
      </AuthShell>
    );
  }

  return (
    <AuthShell 
      title="Welcome to EditEase" 
      subtitle="Sign in to continue to your workspace" 
      error={error}
    >
      <div style={{ marginBottom: 'var(--space-24)', display: 'flex', justifyContent: 'center' }}>
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            useOneTap={false}
            theme="outline"
            size="large"
            text="continue_with"
            width="320px"
          />
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)', marginBottom: 'var(--space-24)', color: 'var(--text-muted)' }}>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-default)' }} />
          <span style={{ fontSize: '12px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>or</span>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-default)' }} />
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
          
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 'var(--space-8)' }}>
              <label style={{ fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Password</label>
              <Link to="/forgot-password" style={{ fontSize: '12px', color: 'var(--accent)', textDecoration: 'none', fontWeight: 500 }}>
                Forgot password?
              </Link>
            </div>
            <div style={{ position: 'relative' }}>
              <input 
                type={showPassword ? "text" : "password"} 
                value={password} 
                onChange={e => setPassword(e.target.value)} 
                required 
                placeholder="Enter password"
                style={{ paddingRight: '40px' }}
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 0, display: 'flex' }}
                tabIndex="-1"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          
          <button type="submit" className="btn btn-primary" style={{ marginTop: 'var(--space-8)', width: '100%', padding: 'var(--space-12)', fontSize: '1rem' }} disabled={loading}>
            {loading ? <><Loader2 size={18} className="spin" /> Signing In...</> : 'Sign In'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: 'var(--space-32)', fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}>Create account</Link>
        </div>
    </AuthShell>
  );
}
