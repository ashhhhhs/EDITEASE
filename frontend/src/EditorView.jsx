import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud, CheckCircle, FolderOpen, Loader, X, FileVideo } from 'lucide-react';
import { API_BASE } from './config';
import { labelColors } from './constants';



export default function EditorView() {
  const [files, setFiles] = useState([]);            // Array of File objects
  const [jobs, setJobs] = useState([]);               // [{file, taskId, status, meta, result, error}]
  const [isProcessing, setIsProcessing] = useState(false);

  const fileInputRef = useRef(null);

  const addFiles = (newFiles) => {
    const videoFiles = Array.from(newFiles).filter(f => f.type.startsWith('video/'));
    setFiles(prev => {
      const existing = new Set(prev.map(f => f.name));
      const unique = videoFiles.filter(f => !existing.has(f.name));
      return [...prev, ...unique];
    });
  };

  const removeFile = (name) => {
    setFiles(prev => prev.filter(f => f.name !== name));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files?.length > 0) addFiles(e.dataTransfer.files);
  };

  const handleFileChange = (e) => {
    if (e.target.files?.length > 0) addFiles(e.target.files);
  };

  // Start processing all files
  const startOrganize = async () => {
    if (files.length === 0) return;
    setIsProcessing(true);

    const newJobs = files.map(file => ({
      file: file,
      name: file.name,
      taskId: null,
      status: 'UPLOADING',
      meta: null,
      result: null,
      error: null
    }));
    setJobs(newJobs);

    // Upload each file and get task IDs
    for (let i = 0; i < newJobs.length; i++) {
      const formData = new FormData();
      formData.append('file', newJobs[i].file);
      try {
        const res = await axios.post(`${API_BASE}/auto_organize`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        newJobs[i].taskId = res.data.task_id;
        newJobs[i].status = 'PENDING';
      } catch (err) {
        newJobs[i].status = 'FAILURE';
        newJobs[i].error = err.response?.data?.error || err.message;
      }
      setJobs([...newJobs]);
    }
  };

  // Poll for all active jobs
  useEffect(() => {
    const activeJobs = jobs.filter(j => j.taskId && j.status !== 'SUCCESS' && j.status !== 'FAILURE');
    if (activeJobs.length === 0) {
      if (jobs.length > 0 && jobs.every(j => j.status === 'SUCCESS' || j.status === 'FAILURE')) {
        setIsProcessing(false);
      }
      return;
    }

    const interval = setInterval(async () => {
      let updated = false;
      const newJobs = [...jobs];

      for (let job of newJobs) {
        if (!job.taskId || job.status === 'SUCCESS' || job.status === 'FAILURE') continue;
        try {
          const res = await axios.get(`${API_BASE}/task_status/${job.taskId}`);
          if (res.data.status !== job.status) updated = true;
          job.status = res.data.status;
          if (res.data.status === 'PROGRESS' && res.data.result) {
            job.meta = res.data.result;
          }
          if (res.data.status === 'SUCCESS') {
            job.result = res.data.result;
          }
          if (res.data.status === 'FAILURE') {
            job.error = 'Processing failed';
          }
        } catch (err) {
          // keep polling
        }
      }
      if (updated) setJobs(newJobs);
    }, 2000);

    return () => clearInterval(interval);
  }, [jobs]);

  const allDone = jobs.length > 0 && jobs.every(j => j.status === 'SUCCESS' || j.status === 'FAILURE');
  const successJobs = jobs.filter(j => j.status === 'SUCCESS' && j.result);

  const reset = () => {
    setFiles([]);
    setJobs([]);
    setIsProcessing(false);
  };

  const openFolder = async (path) => {
    try {
      await axios.post(`${API_BASE}/open_folder`, { path });
    } catch (err) {
      alert('Could not open folder: ' + (err.response?.data?.error || err.message));
    }
  };

  // ---- Results View ----
  if (allDone && successJobs.length > 0) {
    return (
      <div>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem'}}>
          <div>
            <h2 style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success)'}}>
              <CheckCircle size={28} /> All Done!
            </h2>
            <p style={{color: 'var(--text-muted)', marginTop: '0.25rem'}}>
              {successJobs.length} video{successJobs.length > 1 ? 's' : ''} organized into folders by dominant scene type
            </p>
          </div>
          <button className="btn" onClick={reset}>Organize More Videos</button>
        </div>

        {/* Per-video results */}
        {successJobs.map((job, idx) => {
          const result = job.result;
          const label = result.dominant_label || 'other';
          const exportPath = result.export_path || '';
          const exportDir = exportPath.substring(0, exportPath.lastIndexOf('\\')) || exportPath.substring(0, exportPath.lastIndexOf('/'));

          return (
            <div key={idx} className="panel" style={{marginBottom: '1.5rem', padding: '1.25rem'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem'}}>
                <FileVideo size={22} color="var(--accent)" />
                <h3 style={{margin: 0}}>{result.video}</h3>
              </div>

              <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem'}}>
                <span style={{color: 'var(--text-muted)', fontSize: '0.9rem'}}>Dominant Scene Type:</span>
                <span className="badge" style={{
                  backgroundColor: labelColors[label] || '#8b949e',
                  color: '#fff',
                  padding: '0.3rem 0.75rem',
                  borderRadius: '4px',
                  fontWeight: 600,
                  fontSize: '0.85rem'
                }}>{label}</span>
              </div>

              <div style={{
                background: 'var(--bg-color)', border: '1px solid var(--border-color)',
                borderRadius: '8px', padding: '0.75rem 1rem',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between'
              }}>
                <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', overflow: 'hidden'}}>
                  <FolderOpen size={16} color="var(--accent)" style={{flexShrink: 0}} />
                  <code style={{color: 'var(--text-muted)', fontSize: '0.8rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>{exportPath}</code>
                </div>
                <button className="btn btn-primary" onClick={() => openFolder(exportDir)} style={{padding: '0.4rem 1rem', fontSize: '0.8rem', flexShrink: 0, marginLeft: '0.75rem'}}>
                  <FolderOpen size={14} /> Open Folder
                </button>
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // ---- Upload & Processing View ----
  return (
    <div>
      <h2>Auto-Organize</h2>
      <p style={{color: 'var(--text-muted)', marginBottom: '2rem', maxWidth: '600px'}}>
        Drop one or more video files. The AI will detect scenes, classify them, and organize the full video into a folder based on its dominant scene type — all in one click.
      </p>

      {/* Drop zone */}
      {!isProcessing && (
        <>
          <div
            className={`upload-zone ${files.length > 0 ? 'active' : ''}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current.click()}
          >
            <UploadCloud size={56} color="var(--accent)" style={{marginBottom: '1rem'}} />
            {files.length > 0 ? (
              <h3>{files.length} video{files.length > 1 ? 's' : ''} selected</h3>
            ) : (
              <>
                <h3>Drop your videos here</h3>
                <p style={{color: 'var(--text-muted)', marginTop: '0.5rem'}}>Supports multiple files • MP4, MOV, AVI, MKV</p>
              </>
            )}
            <input
              type="file"
              ref={fileInputRef}
              style={{display: 'none'}}
              accept="video/*"
              multiple
              onChange={handleFileChange}
            />
          </div>

          {/* File list */}
          {files.length > 0 && (
            <div style={{marginTop: '1.5rem'}}>
              {files.map((f, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '0.6rem 1rem', background: 'var(--panel-bg)',
                  border: '1px solid var(--border-color)', borderRadius: '8px',
                  marginBottom: '0.5rem'
                }}>
                  <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
                    <FileVideo size={18} color="var(--accent)" />
                    <span style={{fontWeight: 500}}>{f.name}</span>
                    <span style={{color: 'var(--text-muted)', fontSize: '0.8rem'}}>
                      {(f.size / 1024 / 1024).toFixed(1)} MB
                    </span>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); removeFile(f.name); }}
                    style={{background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '4px'}}
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}

              <div style={{textAlign: 'center', marginTop: '2rem'}}>
                <button className="btn btn-primary" onClick={startOrganize} style={{padding: '0.75rem 2.5rem', fontSize: '1rem'}}>
                  🚀 Organize {files.length} Video{files.length > 1 ? 's' : ''}
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Processing status */}
      {isProcessing && jobs.length > 0 && (
        <div style={{marginTop: '1rem'}}>
          <h3 style={{marginBottom: '1rem'}}>Processing {jobs.length} video{jobs.length > 1 ? 's' : ''}...</h3>
          {jobs.map((job, i) => {
            const statusColor = job.status === 'SUCCESS' ? 'var(--success)' : job.status === 'FAILURE' ? 'var(--danger)' : 'var(--accent)';
            const progressWidth =
              job.status === 'SUCCESS' ? '100%' :
              job.status === 'FAILURE' ? '100%' :
              job.status === 'PROGRESS' && job.meta?.step === 'exporting' ? '75%' :
              job.status === 'PENDING' ? '15%' :
              job.taskId ? '30%' : '5%';

            return (
              <div key={i} className="panel" style={{marginBottom: '0.75rem', padding: '1rem'}}>
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem'}}>
                  <span style={{fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                    {job.status !== 'SUCCESS' && job.status !== 'FAILURE' && <Loader size={14} className="spin" />}
                    {job.status === 'SUCCESS' && <CheckCircle size={14} color="var(--success)" />}
                    {job.name}
                  </span>
                  <span style={{color: statusColor, fontSize: '0.8rem', fontWeight: 600}}>
                    {job.status === 'SUCCESS' ? 'Done ✓' : job.status === 'FAILURE' ? 'Failed' : (job.meta?.message || 'Processing...')}
                  </span>
                </div>
                <div className="progress-container">
                  <div className="progress-bar" style={{
                    width: progressWidth,
                    backgroundColor: statusColor,
                    transition: 'width 0.4s ease'
                  }}></div>
                </div>
                {job.error && <p style={{color: 'var(--danger)', fontSize: '0.8rem', marginTop: '0.5rem'}}>{job.error}</p>}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
