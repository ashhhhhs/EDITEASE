import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, CheckCircle, FileVideo, AlertCircle, Loader } from 'lucide-react';
import api from './lib/api';
import PageHeader from './components/PageHeader';
import ContentSection from './components/ContentSection';

export default function Upload() {
  const [files, setFiles] = useState([]);
  const [isProcessingQueue, setIsProcessingQueue] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files).map(f => ({
        fileObj: f,
        name: f.name,
        size: f.size,
        status: 'PENDING',
        taskId: null,
        error: null,
      }));
      setFiles(prev => [...prev, ...newFiles]);
    }
    e.target.value = null; // reset input
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files).map(f => ({
        fileObj: f,
        name: f.name,
        size: f.size,
        status: 'PENDING',
        taskId: null,
        error: null,
      }));
      setFiles(prev => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index) => {
    if (isProcessingQueue) return;
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const startUploadQueue = () => {
    setIsProcessingQueue(true);
  };

  // Upload queue runner
  useEffect(() => {
    if (!isProcessingQueue) return;

    const activeIndex = files.findIndex(f => f.status === 'UPLOADING');
    if (activeIndex !== -1) return; // Currently uploading one, wait for it

    const nextIndex = files.findIndex(f => f.status === 'PENDING');
    if (nextIndex === -1) {
       setIsProcessingQueue(false); // Queue is empty/done uploading
       return;
    }

    const uploadNext = async () => {
       setFiles(prev => {
           const newF = [...prev];
           newF[nextIndex].status = 'UPLOADING';
           return newF;
       });

       const formData = new FormData();
       formData.append('file', files[nextIndex].fileObj);

       try {
           const res = await api.post('/auto_organize', formData, {
               headers: { 'Content-Type': 'multipart/form-data' }
           });
           
           if (res.data.task_id) {
               setFiles(prev => {
                   const newF = [...prev];
                   newF[nextIndex].taskId = res.data.task_id;
                   newF[nextIndex].status = 'PROCESSING';
                   return newF;
               });
           } else {
               setFiles(prev => {
                   const newF = [...prev];
                   newF[nextIndex].status = 'FAILURE';
                   newF[nextIndex].error = 'No task ID returned';
                   return newF;
               });
           }
       } catch (err) {
           setFiles(prev => {
               const newF = [...prev];
               newF[nextIndex].status = 'FAILURE';
               newF[nextIndex].error = err.response?.data?.error || err.message;
               return newF;
           });
       }
    };

    uploadNext();
  }, [isProcessingQueue, files]);

  // Polling for processing tasks
  useEffect(() => {
     let interval;
     const processingFiles = files.filter(f => f.status === 'PROCESSING' && f.taskId);
     
     if (processingFiles.length > 0) {
        interval = setInterval(async () => {
           let changed = false;
           const updatedFiles = await Promise.all(files.map(async f => {
               if (f.status === 'PROCESSING' && f.taskId) {
                   try {
                       const res = await api.get(`/task_status/${f.taskId}`);
                       if (res.data.status === 'SUCCESS' || res.data.status === 'FAILURE') {
                           changed = true;
                           return { 
                               ...f, 
                               status: res.data.status, 
                               error: res.data.status === 'FAILURE' ? 'Processing failed' : null 
                           };
                       }
                   } catch (err) {
                       console.error('Failed to get status for task', f.taskId, err);
                   }
               }
               return f;
           }));
           
           if (changed) {
               setFiles(updatedFiles);
           }
        }, 3000);
     }
     
     return () => clearInterval(interval);
  }, [files]);

  return (
    <div>
      <PageHeader 
        title="Upload Videos" 
        description="Videos will be automatically split, categorized, and organized into Cloudinary via our Agentic Workflow."
      />

      <ContentSection>
        <div 
            className={`upload-zone ${files.length > 0 ? 'active' : ''}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => !isProcessingQueue && fileInputRef.current.click()}
            style={{ cursor: isProcessingQueue ? 'not-allowed' : 'pointer' }}
        >
            <UploadCloud size={48} color="var(--accent)" style={{marginBottom: 'var(--space-16)'}} />
            <div>
                <h3 style={{ margin: '0 0 var(--space-8) 0' }}>Drag and drop multiple videos, or click to browse</h3>
                <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>Supports MP4, MOV, AVI, MKV formats.</p>
            </div>
            <input 
                type="file" 
                ref={fileInputRef} 
                style={{display: 'none'}} 
                accept="video/mp4,video/x-m4v,video/*"
                multiple
                onChange={handleFileChange}
                disabled={isProcessingQueue}
            />
        </div>

        {files.length > 0 && (
            <div style={{ marginTop: 'var(--space-24)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-16)' }}>
                    <h3 style={{ margin: 0 }}>Upload Queue ({files.length})</h3>
                    {!isProcessingQueue && files.some(f => f.status === 'PENDING') && (
                        <button className="btn btn-primary" onClick={startUploadQueue}>
                            Start Agentic Processing
                        </button>
                    )}
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-12)' }}>
                    {files.map((file, idx) => (
                        <div key={idx} className="panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 'var(--space-16)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-16)' }}>
                                <FileVideo size={24} color="var(--text-secondary)" />
                                <div>
                                    <h4 style={{ margin: '0 0 var(--space-4) 0' }}>{file.name}</h4>
                                    <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>
                                        {(file.size / 1024 / 1024).toFixed(1)} MB
                                    </span>
                                </div>
                            </div>
                            
                            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-16)' }}>
                                {file.status === 'PENDING' && (
                                    <button onClick={() => removeFile(idx)} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}>Remove</button>
                                )}
                                {file.status === 'UPLOADING' && (
                                    <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', color: 'var(--accent)' }}>Uploading...</span>
                                )}
                                {file.status === 'PROCESSING' && (
                                    <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', color: '#d97706' }}>Agent Processing...</span>
                                )}
                                {file.status === 'SUCCESS' && (
                                    <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', color: 'var(--success)' }}><CheckCircle size={16} /> Organized</span>
                                )}
                                {file.status === 'FAILURE' && (
                                    <span title={file.error} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', color: 'var(--danger)' }}><AlertCircle size={16} /> Failed</span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )}
      </ContentSection>
    </div>
  );
}
