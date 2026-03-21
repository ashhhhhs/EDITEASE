import React, { useState } from 'react';
import { Wand2, AlertTriangle, Loader2 } from 'lucide-react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { API_BASE } from './config';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/login`, { username, password });
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

  return (
    <div className="app-container" style={{ alignItems: 'center', justifyContent: 'center', background: 'radial-gradient(circle at 50% 0%, var(--surface-panel) 0%, var(--surface-base) 100%)' }}>
      <div className="panel" style={{ width: '100%', maxWidth: '400px', boxShadow: '0 24px 64px rgba(0,0,0,0.4)', border: '1px solid var(--border-default)' }}>
        
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-16)', marginBottom: 'var(--space-32)' }}>
          <div style={{ width: '56px', height: '56px', borderRadius: '16px', background: 'rgba(88, 166, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(88, 166, 255, 0.2)' }}>
            <Wand2 size={32} color="var(--accent)" />
          </div>
          <h2 style={{ margin: 0, fontSize: 'var(--font-title-section)', fontWeight: 600 }}>Welcome to EditEase</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>Sign in to continue to your workspace</p>
        </div>
        
        {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', color: 'var(--danger)', padding: 'var(--space-12)', backgroundColor: 'rgba(218, 54, 51, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(218,54,51,0.2)', marginBottom: 'var(--space-24)', fontSize: 'var(--font-small)' }}>
                <AlertTriangle size={16} /> <span>{error}</span>
            </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-20)' }}>
          <div>
            <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Username</label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} required placeholder="Enter username" />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="Enter password" />
          </div>
          <button type="submit" className="btn btn-primary" style={{ marginTop: 'var(--space-8)', width: '100%', padding: 'var(--space-12)', fontSize: '1rem' }} disabled={loading}>
            {loading ? <><Loader2 size={18} className="spin" /> Signing In...</> : 'Sign In'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: 'var(--space-32)', fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}>Register here</Link>
        </div>
      </div>
    </div>
  );
}
