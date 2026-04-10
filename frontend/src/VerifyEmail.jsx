import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import api from './lib/api';
import AuthShell from './components/AuthShell';

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
    <AuthShell
      title={status === 'loading' ? 'Verifying email...' : status === 'success' ? 'Email verified!' : 'Verification failed'}
      subtitle={status === 'loading' ? 'Please wait while we confirm your email address.' : status === 'success' ? 'Your email has been successfully verified. Redirecting to your dashboard...' : ''}
      icon={status === 'loading' ? Loader2 : status === 'success' ? CheckCircle : XCircle}
      iconClassName={status === 'loading' ? 'spin' : ''}
      error={status === 'error' ? errorMessage : undefined}
    >
      {status === 'error' && (
        <div style={{ textAlign: 'center' }}>
          <Link to="/app/dashboard" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', padding: 12 }}>
            Return to Dashboard
          </Link>
        </div>
      )}
    </AuthShell>
  );
}
