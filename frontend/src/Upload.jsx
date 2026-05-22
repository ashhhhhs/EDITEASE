import React, { useRef, useState } from 'react';
import { UploadCloud, CheckCircle, FileVideo, AlertCircle, Brain, Activity, Eye, Zap } from 'lucide-react';
import PageHeader from './components/PageHeader';
import ContentSection from './components/ContentSection';
import { useUpload } from './UploadContext';

const formatLabel = (label) => {
  if (!label) return 'Pending';
  return label.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
};

const formatPercent = (value) => {
  if (value == null) return null;
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return null;
  return `${Math.round((numeric <= 1 ? numeric * 100 : numeric))}%`;
};

function AnalysisSummary({ file }) {
  const ai = file.aiMetadata;
  if (!ai && !file.dominantLabel) return null;

  const confidence = formatPercent(ai?.average_confidence);
  const faceCoverage = formatPercent(ai?.face_scene_ratio ?? ai?.face_sample_ratio);
  const faceText = ai?.has_faces
    ? `${ai.face_scene_count ?? 0}/${ai.total_scenes_detected ?? '?'} scenes`
    : 'No faces detected';
  const emotion = ai?.dominant_emotion && ai.dominant_emotion !== 'none'
    ? formatLabel(ai.dominant_emotion)
    : 'None';

  const metrics = [
    { icon: Activity, label: 'Scenes', value: ai?.total_scenes_detected ?? '-' },
    { icon: Eye, label: 'Faces', value: faceCoverage ? `${faceText} (${faceCoverage})` : faceText },
    { icon: Brain, label: 'Emotion', value: emotion },
    { icon: Zap, label: 'Confidence', value: confidence || '-' },
  ];

  return (
    <div style={{ marginTop: 'var(--space-12)', minWidth: 300 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--accent)', fontSize: 'var(--font-meta)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
        <Brain size={13} /> AI organization result
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(120px, 1fr))', gap: 8 }}>
        <div style={{ background: 'var(--surface-base)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '8px 10px', gridColumn: '1 / -1' }}>
          <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)', marginBottom: 2 }}>Folder</div>
          <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{formatLabel(file.dominantLabel || ai?.dominant_label)}</div>
        </div>
        {metrics.map(({ icon: Icon, label, value }) => (
          <div key={label} style={{ background: 'var(--surface-base)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '8px 10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 'var(--font-meta)', color: 'var(--text-muted)', marginBottom: 2 }}>
              <Icon size={11} /> {label}
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-small)', fontWeight: 500 }}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Upload() {
  const { files, setFiles, isProcessingQueue, setIsProcessingQueue } = useUpload();
  const fileInputRef = useRef(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files).map((f) => ({
        fileObj: f,
        name: f.name,
        size: f.size,
        status: 'PENDING',
        taskId: null,
        aiMetadata: null,
        dominantLabel: null,
        error: null,
      }));
      setFiles((prev) => [...prev, ...newFiles]);
    }
    e.target.value = null;
  };

  const handleDragEnter = (e) => { e.preventDefault(); setIsDragActive(true); };
  const handleDragLeave = (e) => { e.preventDefault(); setIsDragActive(false); };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files).map((f) => ({
        fileObj: f,
        name: f.name,
        size: f.size,
        status: 'PENDING',
        taskId: null,
        aiMetadata: null,
        dominantLabel: null,
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
        eyebrow="MEDIA · INGEST"
        description="Drop your raw media here. We'll automatically break it down, sort the scenes, and sync everything directly to your cloud storage."
      />

      <ContentSection>
        <div
          className={`upload-zone${isDragActive ? ' drag-active' : files.length > 0 ? ' active' : ''}`}
          onDragOver={(e) => e.preventDefault()}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
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
                <div key={idx} className="panel stagger-item" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--space-16)', padding: 'var(--space-16)' }}>
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
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, minWidth: 160 }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', color: 'var(--accent)' }}>Uploading...</span>
                        <div className="progress-container" style={{ width: '100%', marginTop: 0 }}>
                          <div className="progress-bar progress-bar--shimmer" style={{ width: '100%' }} />
                        </div>
                      </div>
                    )}
                    {file.status === 'PROCESSING' && (
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, minWidth: 240 }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', color: '#d97706' }}>
                          Analyzing & Sorting...
                        </span>
                        <div className="progress-container" style={{ width: '100%', marginTop: 0 }}>
                          <div className="progress-bar progress-bar--shimmer" style={{ width: '100%' }} />
                        </div>
                        {file.progressMessage && (
                          <span style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)', fontStyle: 'italic', maxWidth: 360, textAlign: 'right', lineHeight: 1.4 }}>
                            {file.progressMessage}
                          </span>
                        )}
                      </div>
                    )}
                    {file.status === 'SUCCESS' && (
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2, maxWidth: 420 }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', color: 'var(--success)' }}>
                          <CheckCircle size={16} /> Organized
                        </span>
                        <AnalysisSummary file={file} />
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
