import React, { useState } from 'react';
import { Wand2 } from 'lucide-react';
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
    <div className="app-container" style={{ alignItems: 'center', justifyContent: 'center', overflowY: 'auto', padding: '2rem 0' }}>
      <div className="panel" style={{ width: '100%', maxWidth: '440px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginBottom: '2rem' }}>
          <Wand2 size={28} color="var(--accent)" />
          <h2 style={{ marginBottom: 0 }}>Create Account</h2>
        </div>
        
        {error && <div style={{ color: 'var(--danger)', padding: '0.75rem', backgroundColor: 'rgba(218, 54, 51, 0.1)', borderRadius: '6px', fontSize: '0.9rem', border: '1px solid rgba(218,54,51,0.2)', marginBottom: '1.5rem' }}>{error}</div>}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Name</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} required placeholder="Full Name" />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="Email address" />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Username</label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} required placeholder="Username" />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="Create password" />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Confirm Password</label>
            <input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required placeholder="Repeat password" />
          </div>
          <button type="submit" className="btn btn-primary" style={{ marginTop: '0.5rem', width: '100%', justifyContent: 'center' }} disabled={loading}>
            {loading ? 'Creating Account...' : 'Sign Up'}
          </button>
        </form>

        <div style={{ textAlign: 'center', margin: '2rem 0', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}>Sign in here</Link>
        </div>
      </div>
    </div>
  );
}
