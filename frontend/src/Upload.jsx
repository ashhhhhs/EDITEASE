import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud, CheckCircle, FileVideo } from 'lucide-react';
import { API_BASE } from './config';
import PageHeader from './components/PageHeader';
import ContentSection from './components/ContentSection';

export default function Upload() {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null); // 'PENDING', 'SUCCESS', 'FAILURE', etc.
  const [error, setError] = useState(null);

  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const uploadVideo = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    setTaskId(null);
    setTaskStatus(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_BASE}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      console.log('Upload response:', res.data);
      if (res.data.task_id) {
        setTaskId(res.data.task_id);
      } else {
        setError('No task ID returned.');
        setIsUploading(false);
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message);
      setIsUploading(false);
    }
  };

  useEffect(() => {
    let interval;
    if (taskId && taskStatus !== 'SUCCESS' && taskStatus !== 'FAILURE') {
      interval = setInterval(async () => {
        try {
          const res = await axios.get(`${API_BASE}/task_status/${taskId}`);
          setTaskStatus(res.data.status);
          if (res.data.status === 'SUCCESS' || res.data.status === 'FAILURE') {
            clearInterval(interval);
            setIsUploading(false);
            if (res.data.status === 'FAILURE') setError('Background processing failed.');
          }
        } catch (err) {
          console.error('Failed to get status', err);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [taskId, taskStatus]);

  return (
    <div>
      <PageHeader 
        title="Upload Video" 
        description="Videos will be automatically split into scenes and loaded into the Review Queue for moderation."
      />

      <ContentSection>
        <div 
            className={`upload-zone ${file ? 'active' : ''}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current.click()}
        >
            <UploadCloud size={48} color="var(--accent)" style={{marginBottom: 'var(--space-16)'}} />
            {file ? (
                <div>
                    <h3 style={{ margin: '0 0 var(--space-8) 0', color: 'var(--accent)' }}>{file.name}</h3>
                    <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>{(file.size / 1024 / 1024).toFixed(1)} MB</p>
                </div>
            ) : (
                <div>
                    <h3 style={{ margin: '0 0 var(--space-8) 0' }}>Drag and drop a video, or click to browse</h3>
                    <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>Supports MP4, MOV, AVI, MKV formats up to 2GB</p>
                </div>
            )}
            <input 
                type="file" 
                ref={fileInputRef} 
                style={{display: 'none'}} 
                accept="video/mp4,video/x-m4v,video/*"
                onChange={handleFileChange}
            />
        </div>

        {file && !isUploading && taskStatus !== 'SUCCESS' && (
            <div style={{marginTop: 'var(--space-24)', textAlign: 'center'}}>
                <button className="btn btn-primary" onClick={uploadVideo} style={{ padding: 'var(--space-12) var(--space-32)', fontSize: '1rem' }}>
                    Upload & Process Automatically
                </button>
            </div>
        )}

        {error && <div style={{color: 'var(--danger)', marginTop: 'var(--space-16)', padding: 'var(--space-16)', background: 'rgba(218, 54, 51, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(218, 54, 51, 0.2)'}}>{error}</div>}

        {(isUploading || taskStatus) && (
            <div className="panel" style={{marginTop: 'var(--space-24)'}}>
                <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-8)'}}>
                    <span style={{fontWeight: '600', color: 'var(--text-primary)'}}>
                        {taskStatus === 'SUCCESS' ? 'Processing Complete!' : 'Extracting Scenes...'}
                    </span>
                    <span style={{color: 'var(--text-secondary)', fontSize: 'var(--font-small)'}}>{taskStatus || 'UPLOADING'}</span>
                </div>
                
                <div className="progress-container">
                    <div 
                        className="progress-bar" 
                        style={{
                            width: taskStatus === 'SUCCESS' ? '100%' : (isUploading ? '50%' : '0%'),
                            backgroundColor: taskStatus === 'SUCCESS' ? 'var(--success)' : 'var(--accent)'
                        }}
                    ></div>
                </div>
                
                {taskStatus === 'SUCCESS' && (
                    <div style={{color: 'var(--text-secondary)', marginTop: 'var(--space-16)', display: 'flex', alignItems: 'center', gap: 'var(--space-8)', fontSize: 'var(--font-body)'}}>
                        <CheckCircle size={18} color="var(--success)" /> 
                        Scenes extracted successfully. They are now available in the Review Queue.
                    </div>
                )}
            </div>
        )}
      </ContentSection>
    </div>
  );
}
