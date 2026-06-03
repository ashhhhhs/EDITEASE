import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, CheckCircle, FolderOpen, Loader, X, FileVideo } from 'lucide-react';
import api from './lib/api';
import { labelColors } from './constants';
import PageHeader from './components/PageHeader';
import ContentSection from './components/ContentSection';

export default function EditorView({ currentUser }) {
  const [files, setFiles] = useState([]);
  const [jobs, setJobs] = useState([]);
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

    for (let i = 0; i < newJobs.length; i++) {
      const formData = new FormData();
      formData.append('file', newJobs[i].file);
      try {
        const res = await api.post('/auto_organize', formData, {
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
          const res = await api.get(`/task_status/${job.taskId}`);
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
      await api.post('/open_folder', { path });
    } catch (err) {
      alert('Could not open folder: ' + (err.response?.data?.error || err.message));
    }
  };

  if (allDone && successJobs.length > 0) {
    return (
      <div>
        <PageHeader 
          title={<span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', color: 'var(--success)' }}><CheckCircle size={28} /> Batch Process Complete</span>} 
          description={`${successJobs.length} video(s) have been successfully organized into folders based on their dominant classification.`}
          actions={<button className="btn" onClick={reset}>Organize More Videos</button>}
        />
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-20)' }}>
            {successJobs.map((job, idx) => {
            const result = job.result;
            const label = result.dominant_label || 'other';
            const exportPath = result.export_path || '';
            const exportDir = exportPath.substring(0, exportPath.lastIndexOf('\\')) || exportPath.substring(0, exportPath.lastIndexOf('/'));

            return (
                <ContentSection key={idx} style={{ marginBottom: 0, padding: 0, overflow: 'hidden' }}>
                    <div style={{ padding: 'var(--space-20)', borderBottom: '1px solid var(--border-subtle)' }}>
                        <div style={{display: 'flex', alignItems: 'center', gap: 'var(--space-12)', marginBottom: 'var(--space-16)'}}>
                            <FileVideo size={20} color="var(--accent)" />
                            <h3 style={{margin: 0}}>{result.video}</h3>
                        </div>

                        <div style={{display: 'flex', alignItems: 'center', gap: 'var(--space-12)'}}>
                            <span style={{color: 'var(--text-secondary)', fontSize: 'var(--font-meta)'}}>Dominant Scene Type:</span>
                            <span className="badge" style={{ backgroundColor: labelColors[label] || '#8b949e', color: '#fff' }}>{label}</span>
                        </div>
                    </div>

                    <div style={{ background: 'var(--surface-base)', padding: 'var(--space-16) var(--space-20)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{display: 'flex', alignItems: 'center', gap: 'var(--space-8)', overflow: 'hidden', color: 'var(--text-secondary)' }}>
                            <FolderOpen size={16} color="var(--accent)" style={{flexShrink: 0}} />
                            <code style={{fontSize: 'var(--font-meta)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>{exportPath}</code>
                        </div>
                        <button className="btn btn-primary" onClick={() => openFolder(exportDir)} style={{padding: 'var(--space-8) var(--space-16)', fontSize: 'var(--font-meta)', flexShrink: 0, marginLeft: 'var(--space-16)'}}>
                            <FolderOpen size={14} /> Open Folder
                        </button>
                    </div>
                </ContentSection>
            );
            })}
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader 
        title="Auto-Organize Batch Export" 
        description="Drop one or more video files. The AI will detect scenes, classify them, and organize the full video into a folder based on its dominant scene type instantly."
      />

      {!isProcessing && (
        <ContentSection>
          <div
            className={`upload-zone ${files.length > 0 ? 'active' : ''}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current.click()}
          >
            <UploadCloud size={48} color="var(--accent)" style={{marginBottom: 'var(--space-16)'}} />
            {files.length > 0 ? (
              <h3>{files.length} video{files.length > 1 ? 's' : ''} queued</h3>
            ) : (
              <>
                <h3 style={{ margin: '0 0 var(--space-8) 0' }}>Drag and drop videos here</h3>
                <p style={{color: 'var(--text-secondary)', margin: 0}}>Supports multiple batch files (MP4, MOV, AVI, MKV)</p>
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

          {files.length > 0 && (
            <div style={{marginTop: 'var(--space-24)', display: 'flex', flexDirection: 'column', gap: 'var(--space-8)'}}>
              {files.map((f, i) => (
                <div key={i} className="panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 'var(--space-12) var(--space-16)' }}>
                  <div style={{display: 'flex', alignItems: 'center', gap: 'var(--space-12)'}}>
                    <FileVideo size={18} color="var(--accent)" />
                    <span style={{fontWeight: 500}}>{f.name}</span>
                    <span style={{color: 'var(--text-secondary)', fontSize: 'var(--font-meta)'}}>
                      {(f.size / 1024 / 1024).toFixed(1)} MB
                    </span>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); removeFile(f.name); }}
                    style={{background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: 'var(--space-4)', borderRadius: 'var(--radius-sm)'}}
                    title="Remove item"
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}

              <div style={{textAlign: 'center', marginTop: 'var(--space-24)'}}>
                {currentUser?.email_verified ? (
                    <button className="btn btn-primary" onClick={startOrganize} style={{padding: 'var(--space-12) var(--space-32)', fontSize: '1rem'}}>
                    🚀 Auto-Organize {files.length} Video{files.length > 1 ? 's' : ''}
                    </button>
                ) : (
                    <button className="btn" disabled style={{padding: 'var(--space-12) var(--space-32)', fontSize: '1rem', opacity: 0.6, cursor: 'not-allowed'}}>
                        Verify your email to enable exports
                    </button>
                )}
              </div>
            </div>
          )}
        </ContentSection>
      )}

      {isProcessing && jobs.length > 0 && (
        <ContentSection>
          <h3 style={{marginBottom: 'var(--space-20)'}}>Processing {jobs.length} video{jobs.length > 1 ? 's' : ''}...</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
            {jobs.map((job, i) => {
                const statusColor = job.status === 'SUCCESS' ? 'var(--success)' : job.status === 'FAILURE' ? 'var(--danger)' : 'var(--accent)';
                const progressWidth =
                job.status === 'SUCCESS' ? '100%' :
                job.status === 'FAILURE' ? '100%' :
                job.status === 'PROGRESS' && job.meta?.step === 'exporting' ? '75%' :
                job.status === 'PENDING' ? '15%' :
                job.taskId ? '30%' : '5%';

                return (
                <div key={i} className="panel" style={{ padding: 'var(--space-20)' }}>
                    <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-12)'}}>
                    <span style={{fontWeight: 500, display: 'flex', alignItems: 'center', gap: 'var(--space-8)'}}>
                        {job.status !== 'SUCCESS' && job.status !== 'FAILURE' && <Loader size={14} color="var(--accent)" className="spin" />}
                        {job.status === 'SUCCESS' && <CheckCircle size={14} color="var(--success)" />}
                        {job.name}
                    </span>
                    <span style={{color: statusColor, fontSize: 'var(--font-meta)', fontWeight: 600}}>
                        {job.status === 'SUCCESS' ? 'Done ✓' : job.status === 'FAILURE' ? 'Failed' : (job.meta?.message || 'Processing...')}
                    </span>
                    </div>
                    <div className="progress-container" style={{ margin: 0 }}>
                    <div className="progress-bar" style={{
                        width: progressWidth,
                        backgroundColor: statusColor,
                        transition: 'width 0.4s ease'
                    }}></div>
                    </div>
                    {job.error && <p style={{color: 'var(--danger)', fontSize: 'var(--font-small)', marginTop: 'var(--space-8)', marginBottom: 0 }}>{job.error}</p>}
                </div>
                );
            })}
          </div>
        </ContentSection>
      )}
    </div>
  );
}
