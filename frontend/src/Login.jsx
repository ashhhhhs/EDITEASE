import React, { useState } from 'react';
import { Wand2, AlertTriangle, Loader2, Eye, EyeOff } from 'lucide-react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { API_BASE } from './config';
import AuthShell from './components/AuthShell';
import { useFormValidation, validationRules } from './hooks/useFormValidation';
import { FormInput, FormButton } from './components/FormComponents';

export default function Login({ onLogin, currentUser, onLogout }) {
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);

  // Form validation setup
  const {
    values,
    errors,
    touched,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit,
    resetForm,
  } = useFormValidation(
    {
      email: '',
      password: '',
    },
    {
      email: {
        ...validationRules.required('Email is required'),
        ...validationRules.email(),
      },
      password: {
        ...validationRules.required('Password is required'),
        ...validationRules.minLength(6, 'Password must be at least 6 characters'),
      },
    }
  );

  const handleFormSubmit = async (formValues) => {
    setError(null);
    try {
      const res = await axios.post(`${API_BASE}/login`, {
        email: formValues.email,
        password: formValues.password,
      });
      if (res.data.token) {
        onLogin(res.data.token, res.data.user || res.data);
        resetForm();
      } else {
        setError(res.data.error || 'Login failed');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error connecting to server');
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    setError(null);
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
      title="Welcome back"
      subtitle="Pick up where you left off in the review queue."
      asideEyebrow="Sign in"
      split
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

        <form onSubmit={(e) => {
          e.preventDefault();
          handleSubmit(handleFormSubmit);
        }} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-20)' }}>
          <FormInput
            name="email"
            label="Email"
            type="email"
            value={values.email}
            onChange={handleChange}
            onBlur={handleBlur}
            error={errors.email}
            touched={touched.email}
            placeholder="jane@example.com"
            required
            autoFocus
          />

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 'var(--space-8)' }}>
              <label style={{ fontSize: 'var(--font-small)', fontWeight: 500, color: 'var(--text-primary)' }}>Password</label>
              <Link to="/forgot-password" style={{ fontSize: '12px', color: 'var(--accent)', textDecoration: 'none', fontWeight: 500 }}>
                Forgot password?
              </Link>
            </div>
            <div style={{ position: 'relative' }}>
              <input
                name="password"
                type={showPassword ? "text" : "password"}
                value={values.password}
                onChange={handleChange}
                onBlur={handleBlur}
                required
                placeholder="Enter password"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  paddingRight: '40px',
                  backgroundColor: 'var(--surface-base)',
                  border: `1px solid ${errors.password && touched.password ? 'var(--danger)' : 'var(--border-subtle)'}`,
                  borderRadius: '8px',
                  fontSize: '1rem',
                  color: 'var(--text-primary)',
                  outline: 'none',
                  transition: 'all 0.2s',
                  ...(errors.password && touched.password && {
                    boxShadow: '0 0 0 3px rgba(218, 54, 51, 0.1)',
                  }),
                }}
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
            {errors.password && touched.password && (
              <div
                role="alert"
                style={{
                  marginTop: '6px',
                  fontSize: '0.875rem',
                  color: 'var(--danger)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                {errors.password}
              </div>
            )}
          </div>

          <FormButton
            type="submit"
            variant="primary"
            size="large"
            loading={isSubmitting}
            disabled={isSubmitting}
            style={{ marginTop: 'var(--space-8)', width: '100%' }}
          >
            {isSubmitting ? 'Signing In...' : 'Sign In'}
          </FormButton>
        </form>

        <div className="auth-switch">
          <span>Don't have an account?</span>
          <Link to="/register" className="auth-switch-button">Create account</Link>
        </div>
    </AuthShell>
  );
}
