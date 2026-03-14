import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud, CheckCircle } from 'lucide-react';
import { API_BASE } from './config';

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

  // Poll for task status
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
      <h2>Upload New Video</h2>
      <p style={{color: 'var(--text-muted)', marginBottom: '2rem'}}>
        Powered by Celery. Your video will be processed in the background, extracting scenes and thumbnails automatically.
      </p>

      <div 
        className={`upload-zone ${file ? 'active' : ''}`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current.click()}
      >
        <UploadCloud size={64} color="var(--accent)" style={{marginBottom: '1rem'}} />
        {file ? (
          <h3>{file.name}</h3>
        ) : (
          <h3>Drag and drop a video, or click to browse</h3>
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
        <div style={{marginTop: '2rem', textAlign: 'center'}}>
          <button className="btn btn-primary" onClick={uploadVideo}>Upload & Process</button>
        </div>
      )}

      {error && <div style={{color: 'var(--danger)', marginTop: '1rem', padding: '1rem', background: 'rgba(218, 54, 51, 0.1)', borderRadius: '8px'}}>{error}</div>}

      {(isUploading || taskStatus) && (
        <div className="panel" style={{marginTop: '2rem'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem'}}>
            <span style={{fontWeight: '600'}}>
              {taskStatus === 'SUCCESS' ? 'Completed!' : 'Processing...'}
            </span>
            <span style={{color: 'var(--text-muted)'}}>{taskStatus || 'UPLOADING'}</span>
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
            <p style={{color: 'var(--text-muted)', marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
              <CheckCircle size={18} color="var(--success)" /> Scenes extracted successfully. Go to Inspector to review them.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
