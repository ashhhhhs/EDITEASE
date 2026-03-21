import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import api from './lib/api';

import Login from './Login';
import Register from './Register';
import AppShell from './AppShell';

import Dashboard from './Dashboard';
import Inspector from './Inspector';
import Upload from './Upload';
import EditorView from './EditorView';
import UserManagement from './UserManagement';
import JobMonitor from './JobMonitor';

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
    if (userData && userData.username) {
        setCurrentUser(userData);
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

  if (isAuthLoading) {
    return <div style={{height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-color)', color: '#fff'}}>Loading...</div>;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={token && currentUser ? <Navigate to="/app/dashboard" replace /> : <Navigate to="/login" replace />} />
        
        <Route path="/login" element={!token ? <Login onLogin={handleLogin} /> : <Navigate to="/app/dashboard" replace />} />
        
        <Route path="/register" element={!token ? <Register onLogin={handleLogin} /> : <Navigate to="/app/dashboard" replace />} />
        
        <Route path="/app" element={token && currentUser ? <AppShell currentUser={currentUser} onLogout={handleLogout} /> : <Navigate to="/login" replace />}>
          <Route path="dashboard" element={<Dashboard currentUser={currentUser} />} />
          <Route path="review" element={<RoleGuard allowedRoles={['admin', 'reviewer']}><Inspector /></RoleGuard>} />
          <Route path="admin/users" element={<RoleGuard allowedRoles={['admin']}><UserManagement currentUser={currentUser} /></RoleGuard>} />
          <Route path="admin/jobs" element={<RoleGuard allowedRoles={['admin']}><JobMonitor /></RoleGuard>} />
          <Route path="uploads" element={<RoleGuard allowedRoles={['admin', 'editor']}><Upload /></RoleGuard>} />
          <Route path="exports" element={<RoleGuard allowedRoles={['admin', 'editor']}><EditorView /></RoleGuard>} />
          <Route path="*" element={<Navigate to="dashboard" replace />} />
        </Route>
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
