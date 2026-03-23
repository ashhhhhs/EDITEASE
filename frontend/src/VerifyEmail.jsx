import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Mail, Loader, CheckCircle, XCircle } from 'lucide-react';
import api from './lib/api';

export default function VerifyEmail({ onVerificationSuccess }) {
  const { token } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('loading'); // loading, success, error
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setErrorMessage('No verification token provided.');
      return;
    }

    api.get(`/verify-email/${token}`)
      .then(res => {
        setStatus('success');
        if (onVerificationSuccess) {
            onVerificationSuccess();
        }
        setTimeout(() => {
            navigate('/app/dashboard');
        }, 3000);
      })
      .catch(err => {
        setStatus('error');
        setErrorMessage(err.response?.data?.error || 'Verification failed. The link may be expired.');
      });
  }, [token, navigate, onVerificationSuccess]);

  return (
    <div className="auth-layout">
        <div style={{ position: 'absolute', top: 32, left: 32, display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: 'rgba(88,166,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(88,166,255,0.2)' }}>
            <Mail size={18} color="var(--accent)" />
            </div>
            <span style={{ fontWeight: 700, fontSize: 18, letterSpacing: '-0.01em' }}>EditEase</span>
        </div>

        <div className="auth-box">
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
                {status === 'loading' && <Loader size={48} className="spin" color="var(--accent)" style={{ margin: '0 auto 24px' }} />}
                {status === 'success' && <CheckCircle size={48} color="var(--success)" style={{ margin: '0 auto 24px' }} />}
                {status === 'error' && <XCircle size={48} color="var(--danger)" style={{ margin: '0 auto 24px' }} />}
                
                <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 12, letterSpacing: '-0.02em' }}>
                    {status === 'loading' ? 'Verifying email...' : status === 'success' ? 'Email verified!' : 'Verification failed'}
                </h1>
                
                <p style={{ color: 'var(--text-secondary)', fontSize: 15, lineHeight: 1.5, margin: 0 }}>
                    {status === 'loading' ? 'Please wait while we confirm your email address.' : 
                     status === 'success' ? 'Your email has been successfully verified. Redirecting to your dashboard...' :
                     errorMessage}
                </p>
            </div>

            {status === 'error' && (
                <div style={{ textAlign: 'center' }}>
                    <Link to="/app/dashboard" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', padding: 12 }}>
                        Return to Dashboard
                    </Link>
                </div>
            )}
        </div>
    </div>
  );
}
