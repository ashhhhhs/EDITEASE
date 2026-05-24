import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import api from './lib/api';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

import Login from './Login';
import Register from './Register';
import ForgotPassword from './ForgotPassword';
import ResetPassword from './ResetPassword';
import AppShell from './AppShell';
import VerifyEmail from './VerifyEmail';

import Dashboard from './Dashboard';
import Inspector from './Inspector';
import Upload from './Upload';
import OrganizedVideos from './OrganizedVideos';
import UserManagement from './UserManagement';
import JobMonitor from './JobMonitor';
import Landing from './Landing';
import Settings from './Settings';
import Invite from './Invite';
import { UploadProvider } from './UploadContext';

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

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <BrowserRouter>
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
            <Route path="review" element={<RoleGuard allowedRoles={['admin', 'reviewer', 'editor']}><VerifiedGuard><Inspector /></VerifiedGuard></RoleGuard>} />
            <Route path="admin/users" element={<RoleGuard allowedRoles={['admin']}><VerifiedGuard><UserManagement currentUser={currentUser} /></VerifiedGuard></RoleGuard>} />
            <Route path="admin/jobs" element={<RoleGuard allowedRoles={['admin']}><VerifiedGuard><JobMonitor /></VerifiedGuard></RoleGuard>} />
            <Route path="uploads" element={<RoleGuard allowedRoles={['admin', 'editor']}><VerifiedGuard><Upload /></VerifiedGuard></RoleGuard>} />
            <Route path="organized-videos" element={<RoleGuard allowedRoles={['admin', 'editor']}><VerifiedGuard><OrganizedVideos /></VerifiedGuard></RoleGuard>} />
            <Route path="settings" element={<VerifiedGuard><Settings currentUser={currentUser} /></VerifiedGuard>} />
            <Route path="*" element={<Navigate to="dashboard" replace />} />
          </Route>
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </GoogleOAuthProvider>
  );
}
