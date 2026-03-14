import React, { useState } from 'react';
import { LayoutDashboard, UploadCloud, Grid, Wand2, Shield } from 'lucide-react';
import EditorView from './EditorView';
import Dashboard from './Dashboard';
import Upload from './Upload';
import Inspector from './Inspector';

function App() {
  const [mode, setMode] = useState('editor'); // 'editor' or 'admin'
  const [currentView, setCurrentView] = useState('auto_organize'); // editor views vs admin views

  const switchMode = (newMode) => {
    setMode(newMode);
    setCurrentView(newMode === 'editor' ? 'auto_organize' : 'dashboard');
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <h1><Wand2 size={24} color="#58a6ff" /> EditEase</h1>

        {/* Mode Toggle */}
        <div style={{
          display: 'flex',
          background: 'var(--bg-color)',
          borderRadius: '8px',
          padding: '3px',
          marginBottom: '1.5rem',
          border: '1px solid var(--border-color)'
        }}>
          <button
            onClick={() => switchMode('editor')}
            style={{
              flex: 1,
              padding: '0.5rem',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.8rem',
              transition: 'all 0.2s',
              background: mode === 'editor' ? 'var(--accent)' : 'transparent',
              color: mode === 'editor' ? '#fff' : 'var(--text-muted)',
            }}
          >
            Editor
          </button>
          <button
            onClick={() => switchMode('admin')}
            style={{
              flex: 1,
              padding: '0.5rem',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.8rem',
              transition: 'all 0.2s',
              background: mode === 'admin' ? 'var(--accent)' : 'transparent',
              color: mode === 'admin' ? '#fff' : 'var(--text-muted)',
            }}
          >
            Admin
          </button>
        </div>

        {/* Editor Nav */}
        {mode === 'editor' && (
          <div
            className={`nav-item ${currentView === 'auto_organize' ? 'active' : ''}`}
            onClick={() => setCurrentView('auto_organize')}
          >
            <Wand2 size={20} /> Auto-Organize
          </div>
        )}

        {/* Admin Nav */}
        {mode === 'admin' && (
          <>
            <div style={{color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.1em', padding: '0.5rem 1rem', marginBottom: '0.25rem'}}>
              AI Calibration
            </div>
            <div
              className={`nav-item ${currentView === 'dashboard' ? 'active' : ''}`}
              onClick={() => setCurrentView('dashboard')}
            >
              <LayoutDashboard size={20} /> Dashboard
            </div>
            <div
              className={`nav-item ${currentView === 'upload' ? 'active' : ''}`}
              onClick={() => setCurrentView('upload')}
            >
              <UploadCloud size={20} /> Upload
            </div>
            <div
              className={`nav-item ${currentView === 'inspector' ? 'active' : ''}`}
              onClick={() => setCurrentView('inspector')}
            >
              <Grid size={20} /> Inspector
            </div>
          </>
        )}

        {/* Bottom info */}
        <div style={{marginTop: 'auto', padding: '1rem 0', borderTop: '1px solid var(--border-color)'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem'}}>
            <Shield size={14} />
            {mode === 'editor' ? 'Editor Mode' : 'Admin / AI Calibrator'}
          </div>
        </div>
      </div>

      {/* Main Content — components stay mounted to preserve state */}
      <div className="main-content">
        <div style={{display: currentView === 'auto_organize' ? 'block' : 'none'}}><EditorView /></div>
        <div style={{display: currentView === 'dashboard' ? 'block' : 'none'}}><Dashboard /></div>
        <div style={{display: currentView === 'upload' ? 'block' : 'none'}}><Upload /></div>
        <div style={{display: currentView === 'inspector' ? 'block' : 'none'}}><Inspector /></div>
      </div>
    </div>
  );
}

export default App;
