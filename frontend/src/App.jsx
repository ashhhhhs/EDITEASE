import React, { useState, useEffect, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import api from './lib/api';
import ErrorBoundary from './components/ErrorBoundary';
import { UploadProvider } from './UploadContext';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

// Lazy load components for code splitting
const Login = lazy(() => import('./Login'));
const Register = lazy(() => import('./Register'));
const ForgotPassword = lazy(() => import('./ForgotPassword'));
const ResetPassword = lazy(() => import('./ResetPassword'));
const AppShell = lazy(() => import('./AppShell'));
const VerifyEmail = lazy(() => import('./VerifyEmail'));
const Dashboard = lazy(() => import('./Dashboard'));
const Inspector = lazy(() => import('./Inspector'));
const Upload = lazy(() => import('./Upload'));
const OrganizedVideos = lazy(() => import('./OrganizedVideos'));
const UserManagement = lazy(() => import('./UserManagement'));
const JobMonitor = lazy(() => import('./JobMonitor'));
const Landing = lazy(() => import('./Landing'));
const Settings = lazy(() => import('./Settings'));
const Invite = lazy(() => import('./Invite'));

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthLoading, setIsAuthLoading] = useState(!!token);

  useEffect(() => {
    if (token) {
      api.get('/me')
        .then(res => {
          setCurrentUser(res.data.user);
          setIsAuthLoading(false);
        })
        .catch(() => {
          handleLogout();
          setIsAuthLoading(false);
        });
    } else {
      setIsAuthLoading(false);
    }
  }, [token]);

  const handleLogin = (newToken, userData) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    if (userData && (userData.email || userData.name)) {
        setCurrentUser(userData);
    }
    
    // Check for pending invite redirect
    const pendingInvite = localStorage.getItem('pending_invite');
    if (pendingInvite) {
      localStorage.removeItem('pending_invite');
      setTimeout(() => {
        window.location.href = `/invite/${pendingInvite}`;
      }, 0);
    }
  };

  const handleVerificationSuccess = () => {
    if (currentUser) {
      setCurrentUser({ ...currentUser, email_verified: true });
    }
  };

  const handleLogout = async () => {
    if (token) {
      try {
        await api.post('/logout');
      } catch (e) {
        // ignore
      }
    }
    localStorage.removeItem('token');
    setToken(null);
    setCurrentUser(null);
  };

  const RoleGuard = ({ allowedRoles, children }) => {
    if (!currentUser) return <Navigate to="/login" replace />;
    const role = currentUser.role || 'editor';
    if (!allowedRoles.includes(role)) return <Navigate to="/app/dashboard" replace />;
    return children;
  };

  const VerifiedGuard = ({ children }) => {
    if (!currentUser) return <Navigate to="/login" replace />;
    if (!currentUser.email_verified) return <Navigate to="/login" replace />;
    return children;
  };

  if (isAuthLoading) {
    return <div style={{height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-color)', color: '#fff'}}>Loading...</div>;
  }

  // Loading fallback for lazy-loaded components
  const LoadingFallback = () => (
    <div style={{height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-color)', color: '#fff'}}>
      <div className="spin" style={{
        width: '32px',
        height: '32px',
        border: '3px solid var(--border-subtle)',
        borderTopColor: 'var(--accent)',
        borderRadius: '50%',
        marginRight: '12px'
      }} />
      Loading...
    </div>
  );

  return (
    <ErrorBoundary>
      <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Suspense fallback={<LoadingFallback />}>
            <Routes>
              <Route path="/" element={<Landing />} />

              <Route path="/login" element={!token ? <Login onLogin={handleLogin} /> : (currentUser?.email_verified ? <Navigate to="/app/dashboard" replace /> : <Login onLogin={handleLogin} currentUser={currentUser} onLogout={handleLogout} />)} />

              <Route path="/register" element={!token ? <Register onLogin={handleLogin} /> : <Navigate to="/app/dashboard" replace />} />
              <Route path="/forgot-password" element={!token ? <ForgotPassword /> : <Navigate to="/app/dashboard" replace />} />
              <Route path="/reset-password/:token" element={!token ? <ResetPassword /> : <Navigate to="/app/dashboard" replace />} />
              <Route path="/verify-email/:token" element={<VerifyEmail onVerificationSuccess={handleVerificationSuccess} />} />
              <Route path="/invite/:token" element={<Invite currentUser={currentUser} />} />

              <Route path="/app" element={token && currentUser ? <UploadProvider><AppShell currentUser={currentUser} onLogout={handleLogout} /></UploadProvider> : <Navigate to="/login" replace />}>
                <Route path="dashboard" element={<VerifiedGuard><Dashboard currentUser={currentUser} /></VerifiedGuard>} />
                <Route path="review" element={<RoleGuard allowedRoles={['admin', 'editor', 'reviewer']}><VerifiedGuard><Inspector currentUser={currentUser} /></VerifiedGuard></RoleGuard>} />
                <Route path="admin/users" element={<RoleGuard allowedRoles={['admin']}><VerifiedGuard><UserManagement currentUser={currentUser} /></VerifiedGuard></RoleGuard>} />
                <Route path="admin/jobs" element={<RoleGuard allowedRoles={['admin']}><VerifiedGuard><JobMonitor /></VerifiedGuard></RoleGuard>} />
                <Route path="uploads" element={<RoleGuard allowedRoles={['admin', 'editor']}><VerifiedGuard><Upload /></VerifiedGuard></RoleGuard>} />
                <Route path="organized-videos" element={<RoleGuard allowedRoles={['admin', 'editor']}><VerifiedGuard><OrganizedVideos /></VerifiedGuard></RoleGuard>} />
                <Route path="settings" element={<VerifiedGuard><Settings currentUser={currentUser} onUserUpdate={(u) => setCurrentUser(prev => ({ ...prev, ...u }))} /></VerifiedGuard>} />
                <Route path="*" element={<Navigate to="/app/dashboard" replace />} />
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </GoogleOAuthProvider>
    </ErrorBoundary>
  );
}
