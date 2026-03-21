import React, { useState } from 'react';
import { Wand2, AlertTriangle, Loader2 } from 'lucide-react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { API_BASE } from './config';

export default function Register({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords don't match");
      return;
    }
    setError(null);
    setLoading(true);
    
    try {
      const res = await axios.post(`${API_BASE}/register`, { username, password, name, email });
      if (res.data.ok) {
        const loginRes = await axios.post(`${API_BASE}/login`, { username, password });
        if (loginRes.data.token) {
          onLogin(loginRes.data.token, loginRes.data.user || loginRes.data);
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error connecting to server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container" style={{ alignItems: 'center', justifyContent: 'center', overflowY: 'auto', padding: 'var(--space-40) 0', background: 'radial-gradient(circle at 50% 0%, var(--surface-panel) 0%, var(--surface-base) 100%)' }}>
      <div className="panel" style={{ width: '100%', maxWidth: '440px', boxShadow: '0 24px 64px rgba(0,0,0,0.4)', border: '1px solid var(--border-default)' }}>
        
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-16)', marginBottom: 'var(--space-32)' }}>
          <div style={{ width: '56px', height: '56px', borderRadius: '16px', background: 'rgba(88, 166, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(88, 166, 255, 0.2)' }}>
            <Wand2 size={32} color="var(--accent)" />
          </div>
          <h2 style={{ margin: 0, fontSize: 'var(--font-title-section)', fontWeight: 600 }}>Create Account</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>Sign up to join EditEase</p>
        </div>
        
        {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', color: 'var(--danger)', padding: 'var(--space-12)', backgroundColor: 'rgba(218, 54, 51, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(218,54,51,0.2)', marginBottom: 'var(--space-24)', fontSize: 'var(--font-small)' }}>
                <AlertTriangle size={16} /> <span>{error}</span>
            </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
          <div style={{ display: 'flex', gap: 'var(--space-16)' }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Full Name</label>
                <input type="text" value={name} onChange={e => setName(e.target.value)} required placeholder="Jane Doe" />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Username</label>
                <input type="text" value={username} onChange={e => setUsername(e.target.value)} required placeholder="janedoe" />
              </div>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="jane@example.com" />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="Create strong password" />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Confirm Password</label>
            <input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required placeholder="Repeat password" />
          </div>
          <button type="submit" className="btn btn-primary" style={{ marginTop: 'var(--space-12)', width: '100%', padding: 'var(--space-12)', fontSize: '1rem' }} disabled={loading}>
            {loading ? <><Loader2 size={18} className="spin" /> Creating Account...</> : 'Sign Up'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: 'var(--space-32)', fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}>Sign in here</Link>
        </div>
      </div>
    </div>
  );
}
