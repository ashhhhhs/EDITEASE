import React, { useRef } from 'react';
import { UploadCloud, CheckCircle, FileVideo, AlertCircle } from 'lucide-react';
import PageHeader from './components/PageHeader';
import ContentSection from './components/ContentSection';
import { useUpload } from './UploadContext';

export default function Upload() {
  const { files, setFiles, isProcessingQueue, setIsProcessingQueue } = useUpload();
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files).map((f) => ({
        fileObj: f,
        name: f.name,
        size: f.size,
        status: 'PENDING',
        taskId: null,
        error: null,
      }));
      setFiles((prev) => [...prev, ...newFiles]);
    }
    e.target.value = null;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files).map((f) => ({
        fileObj: f,
        name: f.name,
        size: f.size,
        status: 'PENDING',
        taskId: null,
        error: null,
      }));
      setFiles((prev) => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index) => {
    if (isProcessingQueue) return;
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const startUploadQueue = () => {
    setIsProcessingQueue(true);
  };

  return (
    <div>
      <PageHeader
        title="Ingest Footage"
        description="Drop your raw media here. We'll automatically break it down, sort the scenes, and sync everything directly to your cloud storage."
      />

      <ContentSection>
        <div
          className={`upload-zone ${files.length > 0 ? 'active' : ''}`}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => !isProcessingQueue && fileInputRef.current.click()}
          style={{ cursor: isProcessingQueue ? 'not-allowed' : 'pointer' }}
        >
          <UploadCloud size={48} color="var(--accent)" style={{ marginBottom: 'var(--space-16)' }} />
          <div>
            <h3 style={{ margin: '0 0 var(--space-8) 0' }}>Drag and drop multiple videos, or click to browse</h3>
            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>
              Supports MP4, MOV, AVI, MKV formats.
            </p>
          </div>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
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
              {!isProcessingQueue && files.some((f) => f.status === 'PENDING') && (
                <button className="btn btn-primary" onClick={startUploadQueue}>
                  Start Processing
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
                      <button onClick={() => removeFile(idx)} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}>
                        Remove
                      </button>
                    )}
                    {file.status === 'UPLOADING' && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', color: 'var(--accent)' }}>Uploading...</span>
                    )}
                    {file.status === 'PROCESSING' && (
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2 }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', color: '#d97706' }}>
                          Analyzing & Sorting...
                        </span>
                        {file.progressMessage && (
                          <span style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)', fontStyle: 'italic', maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {file.progressMessage}
                          </span>
                        )}
                      </div>
                    )}
                    {file.status === 'SUCCESS' && (
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2 }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', color: 'var(--success)' }}>
                          <CheckCircle size={16} /> Organized
                        </span>
                        {file.exportPath && (
                          <div style={{ marginTop: 'var(--space-4)', maxWidth: 280, textAlign: 'right' }}>
                            <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginBottom: 2 }}>
                              Stored at
                            </div>
                            <span
                              style={{
                                display: 'block',
                                fontSize: 'var(--font-meta)',
                                color: 'var(--text-muted)',
                                fontFamily: 'var(--font-mono)',
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                              }}
                              title={file.exportPath}
                            >
                              ↳ {file.exportPath.split('/').slice(-3).map((p, i) => i === 1 && p.length > 12 ? p.substring(0, 8) + '…' : p).join(' / ')}
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                    {file.status === 'FAILURE' && (
                      <span title={file.error} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', color: 'var(--danger)' }}>
                        <AlertCircle size={16} /> Failed
                      </span>
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
