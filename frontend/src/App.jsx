import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { API_BASE } from './config';

import Login from './Login';
import Register from './Register';
import AppShell from './AppShell';

import Dashboard from './Dashboard';
import Inspector from './Inspector';
import Upload from './Upload';
import EditorView from './EditorView';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthLoading, setIsAuthLoading] = useState(!!token);

  useEffect(() => {
    if (token) {
      axios.get(`${API_BASE}/me`)
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
        await axios.post(`${API_BASE}/logout`);
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
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="review" element={<RoleGuard allowedRoles={['admin', 'reviewer']}><Inspector /></RoleGuard>} />
          <Route path="uploads" element={<RoleGuard allowedRoles={['admin', 'editor']}><Upload /></RoleGuard>} />
          <Route path="exports" element={<RoleGuard allowedRoles={['admin', 'editor']}><EditorView /></RoleGuard>} />
          <Route path="*" element={<Navigate to="dashboard" replace />} />
        </Route>
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
