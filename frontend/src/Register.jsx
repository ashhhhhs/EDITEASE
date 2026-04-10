import React, { useState } from 'react';
import { Wand2, AlertTriangle, Loader2, Eye, EyeOff } from 'lucide-react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import zxcvbn from 'zxcvbn';
import { API_BASE } from './config';
import AuthShell from './components/AuthShell';

export default function Register({ onLogin }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Password strength
  const score = zxcvbn(password).score; // 0 to 4
  const colors = ['var(--danger)', 'var(--danger)', 'var(--warning)', 'var(--success)', 'var(--success)'];
  const labels = ['Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];
  const passwordsMatch = password === confirmPassword;
  const showPasswordMismatch = confirmPassword.length > 0 && !passwordsMatch;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!agreedToTerms) {
      setError("Please agree to the Terms of Service.");
      return;
    }
    if (!passwordsMatch) {
      setError("Passwords don't match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    
    setError(null);
    setLoading(true);
    
    try {
      const res = await axios.post(`${API_BASE}/register`, {
        email,
        password,
        confirm_password: confirmPassword,
        name,
      });
      if (res.data.ok) {
        // Auto sign-in after successful registration
        const loginRes = await axios.post(`${API_BASE}/login`, { email, password });
        if (loginRes.data.token) {
          onLogin(loginRes.data.token, loginRes.data.user || loginRes.data);
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed. The email might already be in use.');
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
        setError(res.data.error || 'Google signup failed');
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
    setError("Google sign up was unsuccessful. Try again later.");
  };

  return (
    <AuthShell
      title="Create Account"
      subtitle="Sign up to join EditEase"
      error={error}
      maxWidth={440}
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

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
          <div>
            <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Full Name</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} required placeholder="Jane Doe" autoFocus />
          </div>
          
          <div>
            <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="jane@example.com" />
          </div>
          
          <div>
            <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Password</label>
            <div style={{ position: 'relative' }}>
              <input 
                type={showPassword ? "text" : "password"} 
                value={password} 
                onChange={e => setPassword(e.target.value)} 
                required 
                placeholder="At least 8 characters"
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
            <label style={{ display: 'block', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Confirm Password</label>
            <input
              type={showPassword ? "text" : "password"}
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              required
              placeholder="Repeat password"
            />
            {showPasswordMismatch && (
              <div style={{ marginTop: 'var(--space-8)', fontSize: '12px', color: 'var(--danger)', fontWeight: 500 }}>
                Passwords don't match yet.
              </div>
            )}
          </div>
          
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-12)', marginTop: 'var(--space-4)' }}>
            <input 
              type="checkbox" 
              id="terms" 
              checked={agreedToTerms}
              onChange={e => setAgreedToTerms(e.target.checked)}
              style={{ marginTop: '2px', width: '16px', height: '16px', accentColor: 'var(--accent)', cursor: 'pointer' }}
            />
            <label htmlFor="terms" style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.4, cursor: 'pointer' }}>
              I agree to the <a href="#" style={{ color: 'var(--accent)', textDecoration: 'none' }}>Terms of Service</a> and <a href="#" style={{ color: 'var(--accent)', textDecoration: 'none' }}>Privacy Policy</a>.
            </label>
          </div>

          <button type="submit" className="btn btn-primary" style={{ marginTop: 'var(--space-12)', width: '100%', padding: 'var(--space-12)', fontSize: '1rem' }} disabled={loading || !agreedToTerms || password.length < 8 || !passwordsMatch}>
            {loading ? <><Loader2 size={18} className="spin" /> Creating Account...</> : 'Get Started'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: 'var(--space-32)', fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}>Sign in here</Link>
        </div>
    </AuthShell>
  );
}
