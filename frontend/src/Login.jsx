import React, { useState } from 'react';
import { Wand2 } from 'lucide-react';
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
    <div className="app-container" style={{ alignItems: 'center', justifyContent: 'center' }}>
      <div className="panel" style={{ width: '100%', maxWidth: '400px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginBottom: '2rem' }}>
          <Wand2 size={28} color="var(--accent)" />
          <h2 style={{ marginBottom: 0 }}>EditEase</h2>
        </div>
        
        {error && <div style={{ color: 'var(--danger)', padding: '0.75rem', backgroundColor: 'rgba(218, 54, 51, 0.1)', borderRadius: '6px', fontSize: '0.9rem', border: '1px solid rgba(218,54,51,0.2)', marginBottom: '1.5rem' }}>{error}</div>}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Username</label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} required placeholder="Enter username" />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="Enter password" />
          </div>
          <button type="submit" className="btn btn-primary" style={{ marginTop: '0.5rem', width: '100%', justifyContent: 'center' }} disabled={loading}>
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <div style={{ textAlign: 'center', margin: '2rem 0', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}>Register here</Link>
        </div>
      </div>
    </div>
  );
}
