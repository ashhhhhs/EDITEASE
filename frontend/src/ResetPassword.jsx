import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Loader2, AlertTriangle, KeyRound, CheckCircle2 } from 'lucide-react';
import axios from 'axios';
import zxcvbn from 'zxcvbn';
import { API_BASE } from './config';
import AuthShell from './components/AuthShell';

export default function ResetPassword() {
  const { token } = useParams();
  const navigate = useNavigate();
  
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const score = zxcvbn(password).score; // 0 to 4
  const colors = ['var(--danger)', 'var(--danger)', 'var(--warning)', 'var(--success)', 'var(--success)'];
  const labels = ['Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/reset-password`, { token, password });
      if (res.data.ok) {
        setSuccess(true);
      }
    } catch (err) {
      setError(err.response?.data?.error || "Error connecting to server. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <AuthShell title="Password updated" icon={CheckCircle2}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '15px', lineHeight: 1.6, marginBottom: 'var(--space-32)', textAlign: 'center' }}>
            Your password has been changed successfully. You can now sign in with your new password.
          </p>

          <Link to="/login" className="btn btn-primary" style={{ width: '100%', padding: 'var(--space-12)', fontSize: '1rem', justifyContent: 'center' }}>
            Go to Sign In →
          </Link>
      </AuthShell>
    );
  }

  const errorNode = error ? (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
      <div style={{ fontWeight: 600, marginBottom: 2 }}>Reset failed</div>
      <div>{error}</div>
      {error.includes("expired") && (
        <Link to="/forgot-password" style={{ display: 'block', marginTop: 'var(--space-8)', color: 'var(--accent)', fontWeight: 600, textDecoration: 'none' }}>
          Request a new link →
        </Link>
      )}
    </div>
  ) : undefined;

  return (
    <AuthShell
      title="Set a new password"
      subtitle="Pick something strong that you don't use elsewhere."
      icon={KeyRound}
      error={errorNode}
    >
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-20)' }}>
          <div>
            <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>New Password</label>
            <div style={{ position: 'relative' }}>
              <input 
                type={showPassword ? "text" : "password"} 
                value={password} 
                onChange={e => setPassword(e.target.value)} 
                required 
                placeholder="At least 8 characters"
                style={{ paddingRight: '40px' }}
                autoFocus
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
            
            {password.length > 0 && (
              <div style={{ marginTop: 'var(--space-8)' }}>
                <div style={{ display: 'flex', gap: '4px', height: '4px', borderRadius: '2px', overflow: 'hidden' }}>
                  {[0, 1, 2, 3].map(i => (
                    <div key={i} style={{ flex: 1, backgroundColor: i <= score && password.length > 0 ? colors[score] : 'var(--border-subtle)', transition: 'background-color 0.3s' }} />
                  ))}
                </div>
                <div style={{ fontSize: '12px', marginTop: '4px', textAlign: 'right', color: colors[score], fontWeight: 500 }}>
                  {labels[score]}
                </div>
              </div>
            )}
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Confirm New Password</label>
            <input 
              type={showPassword ? "text" : "password"} 
              value={confirmPassword} 
              onChange={e => setConfirmPassword(e.target.value)} 
              required 
              placeholder="Repeat password"
            />
          </div>
          
          <button type="submit" className="btn btn-primary" style={{ marginTop: 'var(--space-8)', width: '100%', padding: 'var(--space-12)', fontSize: '1rem' }} disabled={loading || password.length < 8 || password !== confirmPassword}>
            {loading ? <><Loader2 size={18} className="spin" /> Updating...</> : 'Update Password'}
          </button>
        </form>
    </AuthShell>
  );
}
