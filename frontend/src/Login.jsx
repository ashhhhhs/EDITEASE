import React, { useState } from 'react';
import { Wand2, AlertTriangle, Loader2, Eye, EyeOff } from 'lucide-react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { API_BASE } from './config';

export default function Login({ onLogin }) {
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

  return (
    <div className="app-container" style={{ position: 'relative', alignItems: 'center', justifyContent: 'center', background: 'radial-gradient(circle at 50% 0%, var(--surface-panel) 0%, var(--surface-base) 100%)' }}>
      <Link
        to="/"
        style={{ position: 'absolute', top: 'var(--space-24)', left: 'var(--space-32)', display: 'flex', alignItems: 'center', gap: 'var(--space-8)', textDecoration: 'none', color: 'var(--text-primary)', fontWeight: 700, fontSize: 'var(--font-title-card)', letterSpacing: '-0.01em' }}
      >
        <div style={{ width: 32, height: 32, borderRadius: 'var(--radius-md)', background: 'rgba(88,166,255,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(88,166,255,0.2)' }}>
          <Wand2 size={18} color="var(--accent)" />
        </div>
        <span>EditEase</span>
      </Link>
      <div className="panel" style={{ width: '100%', maxWidth: '400px', boxShadow: '0 24px 64px rgba(0,0,0,0.4)', border: '1px solid var(--border-default)' }}>
        
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-16)', marginBottom: 'var(--space-32)' }}>
          <div style={{ width: '56px', height: '56px', borderRadius: '16px', background: 'rgba(88, 166, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(88, 166, 255, 0.2)' }}>
            <Wand2 size={32} color="var(--accent)" />
          </div>
          <h2 style={{ margin: 0, fontSize: 'var(--font-title-section)', fontWeight: 600 }}>Welcome to EditEase</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '15px' }}>Sign in to continue to your workspace</p>
        </div>
        
        {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', color: 'var(--danger)', padding: 'var(--space-12)', backgroundColor: 'rgba(218, 54, 51, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(218,54,51,0.2)', marginBottom: 'var(--space-24)', fontSize: '14px' }}>
                <AlertTriangle size={18} style={{ flexShrink: 0 }} /> <span>{error}</span>
            </div>
        )}

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
      </div>
    </div>
  );
}
