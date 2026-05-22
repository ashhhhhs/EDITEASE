import React, { useEffect, useState, useCallback } from 'react';
import {
  Folder, Download, RefreshCw, Search,
  CheckCircle, Archive, X, ChevronLeft, PlayCircle,
  FileText, Clock, Hash, Brain, Eye, Zap,
  Activity, AlertTriangle, ChevronDown, ChevronUp, FolderDown
} from 'lucide-react';
import api from './lib/api';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);
import { useToast } from './hooks/useToast.jsx';
import PageHeader from './components/PageHeader';
import LoadingState from './components/LoadingState';

const BATCH_MAX = 10;

const LABEL_MAP = {
  testimonial: 'Testimonials',
  presenter: 'Presenters',
  audience_reaction: 'Audience Reactions',
  text_slide: 'Text Slides',
  screen_recording: 'Screen Recordings',
  'b-roll': 'B-Rolls',
  establishing_shot: 'Establishing Shots',
  edited: 'Edited Videos',
  other: 'Other'
};

const getDisplayLabel = (key) => {
  if (!key) return 'Other';
  if (LABEL_MAP[key]) return LABEL_MAP[key];
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) + 's';
};

/* ── Inline style helpers ── */
const metaRowStyle = {
  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  fontSize: 'var(--font-meta)', padding: '3px 0',
};
const metaKeyStyle = { color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 };
const metaValStyle = { color: 'var(--text-secondary)', fontWeight: 500, fontFamily: 'var(--font-mono)', fontSize: '0.7rem' };

/* ── Status color mapping ── */
const STATUS_COLORS = {
  SUCCESS: { bg: 'rgba(35,134,54,0.12)', color: 'var(--success)', border: 'rgba(35,134,54,0.3)' },
  FAILURE: { bg: 'rgba(218,54,51,0.12)', color: 'var(--danger)', border: 'rgba(218,54,51,0.3)' },
  STARTED: { bg: 'rgba(88,166,255,0.12)', color: 'var(--accent)', border: 'rgba(88,166,255,0.3)' },
  PENDING: { bg: 'rgba(210,153,34,0.12)', color: 'var(--warning)', border: 'rgba(210,153,34,0.3)' },
  NO_RECORD: { bg: 'rgba(110,118,129,0.12)', color: 'var(--text-muted)', border: 'rgba(110,118,129,0.3)' },
  NO_TASK: { bg: 'rgba(110,118,129,0.12)', color: 'var(--text-muted)', border: 'rgba(110,118,129,0.3)' },
};

function StatusBadge({ status }) {
  const s = STATUS_COLORS[status] || STATUS_COLORS.NO_RECORD;
  return (
    <span style={{
      background: s.bg, color: s.color, border: `1px solid ${s.border}`,
      fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.06em',
      padding: '2px 8px', borderRadius: 20, textTransform: 'uppercase',
    }}>{status?.replace(/_/g, ' ') || 'Unknown'}</span>
  );
}

/* ── Label badge ── */
function LabelBadge({ label }) {
  const display = getDisplayLabel(label);
  const isEdited = label === 'edited';
  return (
    <span style={{
      background: isEdited ? 'rgba(191,144,255,0.15)' : 'rgba(88,166,255,0.15)', 
      color: isEdited ? '#d2a8ff' : '#58a6ff',
      fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em',
      padding: '2px 8px', borderRadius: 20,
      border: `1px solid ${isEdited ? 'rgba(191,144,255,0.33)' : 'rgba(88,166,255,0.33)'}`,
    }}>{isEdited ? '✨ ' : ''}{display}</span>
  );
}

/* ── Duplicate badge ── */
function DupBadge() {
  return (
    <span style={{
      background: 'rgba(218,54,51,0.12)', color: 'var(--danger)',
      fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.06em',
      padding: '2px 7px', borderRadius: 20, border: '1px solid rgba(218,54,51,0.3)',
    }}>DUPLICATE</span>
  );
}

/* ── Metadata strip for video cards ── */
function MetadataStrip({ ai }) {
  if (!ai || Object.keys(ai).length === 0) return null;
  
  const confidence = ai.average_confidence != null ? Math.round(ai.average_confidence * 100) : null;
  const emotionConfidence = ai.dominant_emotion_confidence != null ? Math.round(ai.dominant_emotion_confidence) : null;
  const scenes = ai.total_scenes_detected;
  const emotion = ai.dominant_emotion;
  const hasFaces = ai.has_faces;

  return (
    <div style={{
      background: 'rgba(88,166,255,0.04)',
      border: '1px solid rgba(88,166,255,0.08)',
      borderRadius: 'var(--radius-md)',
      padding: '8px 10px',
      display: 'flex', flexDirection: 'column', gap: 2,
      marginTop: 2,
    }}>
      <div style={{ fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.1em', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 2, display: 'flex', alignItems: 'center', gap: 4 }}>
        <Brain size={9} /> AI Metadata
      </div>
      {confidence != null && (
        <div style={metaRowStyle}>
          <span style={metaKeyStyle}><Zap size={10} /> Confidence</span>
          <span style={{
            ...metaValStyle,
            color: confidence >= 80 ? 'var(--success)' : confidence >= 50 ? 'var(--warning)' : 'var(--danger)',
          }}>{confidence}%</span>
        </div>
      )}
      {scenes != null && (
        <div style={metaRowStyle}>
          <span style={metaKeyStyle}><Activity size={10} /> Scenes</span>
          <span style={metaValStyle}>{scenes} cuts</span>
        </div>
      )}
      {emotion && emotion !== 'none' && (
        <div style={metaRowStyle}>
          <span style={metaKeyStyle}><Eye size={10} /> Emotion</span>
          <span style={{ ...metaValStyle, textTransform: 'capitalize' }}>{emotion}</span>
        </div>
      )}
      {emotionConfidence != null && (
        <div style={metaRowStyle}>
          <span style={metaKeyStyle}><Zap size={10} /> Emotion Conf.</span>
          <span style={metaValStyle}>{emotionConfidence}%</span>
        </div>
      )}
      {hasFaces != null && (
        <div style={metaRowStyle}>
          <span style={metaKeyStyle}><Eye size={10} /> Faces</span>
          <span style={metaValStyle}>{hasFaces ? 'Detected' : 'None'}</span>
        </div>
      )}
    </div>
  );
}

/* ── Folder card ── */
function FolderCard({ label, count, onClick, onDownloadAll, isDownloading }) {
  const display = getDisplayLabel(label);
  return (
    <div
      className="folder-card gs-reveal"
      onClick={() => onClick(label)}
      style={{
        background: 'var(--surface-panel)', border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)', padding: 'var(--space-20)',
        display: 'flex', flexDirection: 'column', gap: 'var(--space-12)',
        cursor: 'pointer', transition: 'all 0.2s ease',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = 'var(--text-muted)';
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = 'var(--border-subtle)';
        e.currentTarget.style.transform = 'none';
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{
          width: 40, height: 40, borderRadius: 'var(--radius-md)',
          background: 'rgba(88,166,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#58a6ff'
        }}>
          <Folder size={20} fill="currentColor" fillOpacity={0.2} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: 'var(--font-body)', color: 'var(--text-primary)' }}>
            {display}
          </div>
          <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)' }}>
            {count} video{count !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {/* Download-all button row */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button
          className="btn"
          style={{
            fontSize: 'var(--font-meta)', padding: '4px 10px',
            opacity: isDownloading ? 0.6 : 1,
            display: 'flex', alignItems: 'center', gap: 4,
          }}
          disabled={isDownloading}
          title={`Download all ${display} videos as ZIP`}
          onClick={e => { e.stopPropagation(); onDownloadAll(label); }}
        >
          {isDownloading
            ? <RefreshCw size={12} style={{ animation: 'spin 1s linear infinite' }} />
            : <FolderDown size={12} />}
          {isDownloading ? 'Preparing…' : 'Download All'}
        </button>
      </div>
    </div>
  );
}

/* ── Video card ── */
function VideoCard({ doc, selected, onSelect, onPreview, onDownload, showMeta }) {
  const [isHovering, setIsHovering] = useState(false);
  const date = doc.created_at
    ? new Date(doc.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    : '—';
  const isDup = doc.status === 'duplicate';

  // Compute thumbnail URL
  const videoUrl = doc.cloudinary_url;
  const thumbnailUrl = videoUrl ? videoUrl.replace(/\.(mp4|mov|mkv|avi)$/i, '.jpg') : '';

  return (
    <div
      className="video-card gs-reveal tour-video-card"
      style={{
        background: 'var(--surface-panel)',
        border: `1px solid ${selected ? 'var(--accent)' : 'var(--border-subtle)'}`,
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-16)', // Adjusted padding
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-12)',
        transition: 'border-color 0.18s, box-shadow 0.18s',
        boxShadow: selected ? '0 0 0 2px rgba(88,166,255,0.2)' : 'none',
        cursor: 'pointer',
        position: 'relative',
        overflow: 'hidden'
      }}
      onClick={() => onSelect(doc.id)}
      onMouseEnter={e => { 
        e.currentTarget.style.borderColor = selected ? 'var(--accent)' : 'var(--border-default)'; 
        setIsHovering(true);
      }}
      onMouseLeave={e => { 
        e.currentTarget.style.borderColor = selected ? 'var(--accent)' : 'var(--border-subtle)';
        setIsHovering(false);
      }}
    >
      {/* Thumbnail / Video Player Area */}
      {videoUrl && (
        <div 
          onClick={e => { e.stopPropagation(); onPreview(doc); }}
          style={{
            width: 'calc(100% + 32px)', // stretch across parent padding
            margin: '-16px -16px 0 -16px',
            aspectRatio: '16/9',
            background: 'var(--bg-color)',
            position: 'relative',
            borderBottom: '1px solid var(--border-subtle)'
        }}>
          {/* Always render thumbnail as base */}
          <img 
             src={thumbnailUrl} 
             alt={doc.display_name}
             style={{
               width: '100%', height: '100%', objectFit: 'cover',
               position: 'absolute', top: 0, left: 0, zIndex: 1
             }}
             onError={(e) => { e.target.style.display = 'none'; }}
          />
          
          {/* Play Icon overlay */}
          <div style={{
             position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 2,
             display: 'flex', alignItems: 'center', justifyContent: 'center',
             background: isHovering ? 'rgba(0,0,0,0.3)' : 'transparent',
             transition: 'background 0.2s',
          }}>
             {isHovering && <PlayCircle size={48} color="#fff" strokeWidth={1.5} style={{ opacity: 0.9 }} />}
          </div>
          
          {/* Overlay Checkbox inside thumbnail */}
          <div
            style={{
              position: 'absolute', top: 12, right: 12,
              width: 20, height: 20, borderRadius: 6,
              border: `2px solid ${selected ? 'var(--accent)' : 'rgba(255,255,255,0.7)'}`,
              background: selected ? 'var(--accent)' : 'rgba(0,0,0,0.4)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.15s',
              zIndex: 10,
              boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
            }}
            onClick={e => { e.stopPropagation(); onSelect(doc.id); }}
          >
            {selected && <CheckCircle size={12} color="#0d1117" strokeWidth={3} />}
          </div>
        </div>
      )}

      {/* Fallback Checkbox (if no video URL) */}
      {!videoUrl && (
        <div
          style={{
            position: 'absolute', top: 14, right: 14,
            width: 18, height: 18, borderRadius: 4,
            border: `2px solid ${selected ? 'var(--accent)' : 'var(--border-strong)'}`,
            background: selected ? 'var(--accent)' : 'transparent',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.15s',
            zIndex: 10
          }}
          onClick={e => { e.stopPropagation(); onSelect(doc.id); }}
        >
          {selected && <CheckCircle size={11} color="#0d1117" strokeWidth={3} />}
        </div>
      )}

      {/* Header row */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', paddingRight: videoUrl ? 0 : 28 }}>
        <LabelBadge label={doc.dominant_label || 'other'} />
        {isDup && <DupBadge />}
      </div>

      {/* Name */}
      <div style={{ fontWeight: 600, fontSize: 'var(--font-body)', color: 'var(--text-primary)', lineHeight: 1.3, wordBreak: 'break-word', marginTop: 4 }}>
        {doc.display_name || doc.original_filename}
      </div>

      <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginTop: -6 }}>
        {doc.original_filename}
      </div>

      {/* Inline metadata */}
      {showMeta && <MetadataStrip ai={doc.ai_metadata} />}

      {/* File hash snippet */}
      {showMeta && doc.file_hash && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          <Hash size={9} /> {doc.file_hash.substring(0, 12)}…
        </div>
      )}

      {/* Footer row */}
      <div style={{ marginTop: 'auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, paddingTop: 8 }}>
        <span style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)' }}>{date}</span>
        <button
          className="btn"
          style={{ padding: '4px 12px', fontSize: 'var(--font-meta)', opacity: isDup ? 0.6 : 1 }}
          title={isDup ? 'Reuses original asset' : 'Download'}
          onClick={e => { e.stopPropagation(); onDownload(doc); }}
        >
          <Download size={13} />
        </button>
      </div>
    </div>
  );
}


/* ── Processing Logs Panel ── */
function LogsPanel({ currentFolder, search }) {
  const toast = useToast();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [expandedId, setExpandedId] = useState(null);
  const limit = 20;

  const fetchLogs = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: p, limit });
      if (currentFolder) params.set('label', currentFolder);
      if (search) params.set('search', search);
      const res = await api.get(`/organized-videos/logs?${params}`);
      setLogs(res.data.logs || []);
      setTotal(res.data.total || 0);
      setPage(p);
    } catch (err) {
      toast.error('Failed to load processing logs');
    } finally {
      setLoading(false);
    }
  }, [currentFolder, search, toast]);

  useEffect(() => { fetchLogs(1); }, [fetchLogs]);

  const totalPages = Math.ceil(total / limit);

  const formatDuration = (secs) => {
    if (secs == null) return '—';
    if (secs < 60) return `${secs}s`;
    return `${Math.floor(secs / 60)}m ${Math.round(secs % 60)}s`;
  };

  const formatDate = (iso) => {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleString(undefined, {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
      });
    } catch { return iso; }
  };

  if (loading) return <LoadingState message="Loading logs…" />;

  if (logs.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 'var(--space-40) var(--space-24)', color: 'var(--text-muted)' }}>
        <FileText size={32} style={{ opacity: 0.3, marginBottom: 12 }} />
        <div style={{ fontWeight: 500 }}>No processing logs found</div>
      </div>
    );
  }

  return (
    <div>
      {/* Logs table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-small)' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
              {['Video', 'Label', 'Status', 'Task', 'Duration', 'Progress', 'Processed At', ''].map(h => (
                <th key={h} style={{
                  padding: '10px 12px', textAlign: 'left', fontWeight: 600,
                  color: 'var(--text-muted)', fontSize: 'var(--font-meta)',
                  textTransform: 'uppercase', letterSpacing: '0.06em',
                  whiteSpace: 'nowrap', background: 'rgba(255,255,255,0.02)',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {logs.map(log => (
              <React.Fragment key={log.id}>
                <tr
                  style={{
                    borderBottom: '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                    transition: 'background 0.15s',
                  }}
                  onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--hover-surface)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <td style={{ padding: '10px 12px', maxWidth: 200 }}>
                    <div style={{ fontWeight: 500, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {log.video_name}
                    </div>
                    <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      <Hash size={8} style={{ display: 'inline', verticalAlign: 'middle' }} /> {log.file_hash}
                    </div>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <LabelBadge label={log.dominant_label} />
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{
                      fontSize: '0.7rem', fontWeight: 600, padding: '2px 8px', borderRadius: 20,
                      background: log.status === 'duplicate' ? 'rgba(218,54,51,0.12)' : 'rgba(35,134,54,0.12)',
                      color: log.status === 'duplicate' ? 'var(--danger)' : 'var(--success)',
                      border: `1px solid ${log.status === 'duplicate' ? 'rgba(218,54,51,0.3)' : 'rgba(35,134,54,0.3)'}`,
                      textTransform: 'uppercase',
                    }}>{log.status}</span>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <StatusBadge status={log.task_status} />
                  </td>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontSize: 'var(--font-meta)', whiteSpace: 'nowrap' }}>
                    <Clock size={10} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
                    {formatDuration(log.processing_seconds)}
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)' }}>
                    {log.task_progress || '—'}
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: 'var(--font-meta)', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {formatDate(log.created_at)}
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    {expandedId === log.id ? <ChevronUp size={14} color="var(--text-muted)" /> : <ChevronDown size={14} color="var(--text-muted)" />}
                  </td>
                </tr>

                {/* Expanded detail row */}
                {expandedId === log.id && (
                  <tr>
                    <td colSpan={8} style={{ padding: 0 }}>
                      <div style={{
                        background: 'rgba(88,166,255,0.03)',
                        borderBottom: '2px solid rgba(88,166,255,0.12)',
                        padding: '16px 24px',
                        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16,
                        animation: 'fadeIn 0.2s ease',
                      }}>
                        {/* AI Metadata panel */}
                        <div>
                          <div style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.1em', color: 'var(--accent)', textTransform: 'uppercase', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                            <Brain size={10} /> AI Metadata
                          </div>
                          {log.ai_metadata && Object.keys(log.ai_metadata).length > 0 ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                              {log.ai_metadata.average_confidence != null && (
                                <div style={metaRowStyle}>
                                  <span style={metaKeyStyle}>Confidence</span>
                                  <span style={metaValStyle}>{Math.round(log.ai_metadata.average_confidence * 100)}%</span>
                                </div>
                              )}
                              {log.ai_metadata.total_scenes_detected != null && (
                                <div style={metaRowStyle}>
                                  <span style={metaKeyStyle}>Scenes</span>
                                  <span style={metaValStyle}>{log.ai_metadata.total_scenes_detected} cuts</span>
                                </div>
                              )}
                              {log.ai_metadata.dominant_emotion && (
                                <div style={metaRowStyle}>
                                  <span style={metaKeyStyle}>Emotion</span>
                                  <span style={{ ...metaValStyle, textTransform: 'capitalize' }}>{log.ai_metadata.dominant_emotion}</span>
                                </div>
                              )}
                              {log.ai_metadata.dominant_emotion_confidence != null && (
                                <div style={metaRowStyle}>
                                  <span style={metaKeyStyle}>Emotion Conf.</span>
                                  <span style={metaValStyle}>{Math.round(log.ai_metadata.dominant_emotion_confidence)}%</span>
                                </div>
                              )}
                              {log.ai_metadata.has_faces != null && (
                                <div style={metaRowStyle}>
                                  <span style={metaKeyStyle}>Faces</span>
                                  <span style={metaValStyle}>{log.ai_metadata.has_faces ? 'Detected' : 'None'}</span>
                                </div>
                              )}
                              {log.ai_metadata.action_taken && (
                                <div style={metaRowStyle}>
                                  <span style={metaKeyStyle}>Action</span>
                                  <span style={{ ...metaValStyle, color: 'var(--success)' }}>{String(log.ai_metadata.action_taken).replace(/_/g, ' ')}</span>
                                </div>
                              )}
                            </div>
                          ) : (
                            <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)' }}>No AI metadata</div>
                          )}
                        </div>

                        {/* Label Distribution */}
                        {log.ai_metadata?.label_distribution && Object.keys(log.ai_metadata.label_distribution).length > 0 && (
                          <div>
                            <div style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.1em', color: 'var(--accent)', textTransform: 'uppercase', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                              <Activity size={10} /> Category Distribution
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                              {Object.entries(log.ai_metadata.label_distribution)
                                .sort((a, b) => b[1] - a[1])
                                .map(([key, val]) => (
                                  <div key={key} style={metaRowStyle}>
                                    <span style={{ ...metaKeyStyle, textTransform: 'capitalize' }}>{getDisplayLabel(key)}</span>
                                    <span style={metaValStyle}>{val} scene{val !== 1 ? 's' : ''}</span>
                                  </div>
                                ))}
                            </div>
                          </div>
                        )}

                        {/* Task details */}
                        <div>
                          <div style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.1em', color: 'var(--accent)', textTransform: 'uppercase', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                            <Clock size={10} /> Task Details
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                            <div style={metaRowStyle}>
                              <span style={metaKeyStyle}>Task ID</span>
                              <span style={{ ...metaValStyle, maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis' }}>{log.batch_id || '—'}</span>
                            </div>
                            <div style={metaRowStyle}>
                              <span style={metaKeyStyle}>Started</span>
                              <span style={metaValStyle}>{formatDate(log.task_created_at)}</span>
                            </div>
                            <div style={metaRowStyle}>
                              <span style={metaKeyStyle}>Finished</span>
                              <span style={metaValStyle}>{formatDate(log.task_updated_at)}</span>
                            </div>
                            <div style={metaRowStyle}>
                              <span style={metaKeyStyle}>Duration</span>
                              <span style={metaValStyle}>{formatDuration(log.processing_seconds)}</span>
                            </div>
                            {log.task_error && (
                              <div style={{ marginTop: 6, padding: '8px 10px', background: 'rgba(218,54,51,0.08)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(218,54,51,0.2)' }}>
                                <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: 4, marginBottom: 4 }}>
                                  <AlertTriangle size={10} /> Error
                                </div>
                                <div style={{ fontSize: 'var(--font-meta)', color: 'var(--danger)', fontFamily: 'var(--font-mono)', wordBreak: 'break-all' }}>
                                  {log.task_error}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', gap: 'var(--space-8)', justifyContent: 'center', marginTop: 'var(--space-20)', flexWrap: 'wrap' }}>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
            <button
              key={p}
              className={`btn${p === page ? ' btn-primary' : ''}`}
              style={{ minWidth: 36, padding: '4px 10px' }}
              onClick={() => fetchLogs(p)}
            >{p}</button>
          ))}
        </div>
      )}

      <div style={{ textAlign: 'center', marginTop: 'var(--space-12)', fontSize: 'var(--font-meta)', color: 'var(--text-muted)' }}>
        {total} log entr{total !== 1 ? 'ies' : 'y'}
      </div>
    </div>
  );
}

/* ── Main page ── */
export default function OrganizedVideos() {
  const toast = useToast();
  
  // Navigation State
  const [currentFolder, setCurrentFolder] = useState(null);
  const [folderStats, setFolderStats]     = useState({});
  const [statsLoading, setStatsLoading]   = useState(true);

  // Video List State
  const [videos, setVideos]       = useState([]);
  const [total, setTotal]         = useState(0);
  const [loading, setLoading]     = useState(false);
  const [page, setPage]           = useState(1);
  const [selected, setSelected]   = useState(new Set());
  const [previewDoc, setPreviewDoc] = useState(null); // Preview modal state

  // Filters & toggles
  const [search, setSearch]         = useState('');
  const [filterDup, setFilterDup]   = useState('');   // '' | 'true' | 'false'
  const [showMeta, setShowMeta]     = useState(true);
  const [showLogs, setShowLogs]     = useState(false);

  const limit = 24;

  // Track which category folder is currently generating a ZIP
  const [downloadingCategory, setDownloadingCategory] = useState(null);



  const fetchStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const res = await api.get('/organized-videos/stats');
      setFolderStats(res.data || {});
    } catch (err) {
      toast.error('Failed to load folder structure');
    } finally {
      setStatsLoading(false);
    }
  }, [toast]);

  const fetchVideos = useCallback(async (p = 1) => {
    if (currentFolder === null) return;
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: p, limit, label: currentFolder });
      if (search)      params.set('search', search);
      if (filterDup)   params.set('is_duplicate', filterDup);
      // NOTE: no uploader param – server scopes results to logged-in user automatically
      const res = await api.get(`/organized-videos?${params}`);
      setVideos(res.data.videos || []);
      setTotal(res.data.total || 0);
      setPage(p);
    } catch (err) {
      toast.error(err.friendlyMessage || 'Failed to load organized videos');
    } finally {
      setLoading(false);
    }
  }, [search, filterDup, currentFolder, toast]);

  // GSAP Batch entrance effect
  const mainRef = React.useRef(null);

  React.useLayoutEffect(() => {
    if (loading || statsLoading) return;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    let t = setTimeout(() => {
      const ctx = gsap.context(() => {
        ScrollTrigger.batch('.gs-reveal', {
          onEnter: elements => {
            gsap.fromTo(elements,
              { opacity: 0, y: 30 },
              { opacity: 1, y: 0, stagger: 0.05, duration: 0.5, ease: 'power2.out', overwrite: true }
            );
          },
          once: true
        });
        ScrollTrigger.refresh();
      }, mainRef);

      return () => ctx.revert();
    }, 50); // slight delay to allow React to paint DOM elements

    return () => clearTimeout(t);
  }, [loading, statsLoading, videos, folderStats]);

  // Load stats or videos depending on folder state
  useEffect(() => { 
    if (currentFolder === null) {
      fetchStats();
      setVideos([]);  // Clear videos when going back to folders
      setSelected(new Set()); // clear selection
      setSearch(''); // clear search
      setShowLogs(false); // close logs when going back
    } else {
      fetchVideos(1); 
    }
  }, [currentFolder, fetchStats, fetchVideos]);

  const toggleSelect = useCallback((id) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }, []);

  const selectAll = () => setSelected(new Set(videos.map(v => v.id)));
  const clearAll  = () => setSelected(new Set());

  const handleSingleDownload = async (doc) => {
    try {
      const res = await api.post('/organized-videos/download', { id: doc.id });
      if (res.data.url) {
        // Trigger direct download via attachment URL
        window.location.href = res.data.url;
        toast.success(`Starting download: ${doc.display_name}`);
      }
    } catch (err) {
      toast.error(err.friendlyMessage || 'Download failed');
    }
  };

  const handleBatchDownload = async () => {
    const ids = Array.from(selected);
    if (ids.length === 0) { toast.error('Select at least one video'); return; }
    if (ids.length > BATCH_MAX) { toast.error(`Batch limit is ${BATCH_MAX} files`); return; }
    
    setLoading(true);
    try {
      const res = await api.post('/organized-videos/download-batch', { ids });
      if (res.data.url) {
        window.location.href = res.data.url;
        toast.success(res.data.message || 'Generating ZIP…');
        clearAll();
      }
    } catch (err) {
      toast.error(err.friendlyMessage || 'Failed to generate batch download');
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryDownload = async (label) => {
    setDownloadingCategory(label);
    try {
      const res = await api.post('/organized-videos/download-category', { label });
      if (res.data.url) {
        window.location.href = res.data.url;
        const msg = res.data.capped
          ? `ZIP ready (first 50 of ${folderStats[label]} videos)`
          : res.data.message || `ZIP ready for ${res.data.count} videos`;
        toast.success(msg);
      }
    } catch (err) {
      toast.error(err.friendlyMessage || `Failed to download ${getDisplayLabel(label)} category`);
    } finally {
      setDownloadingCategory(null);
    }
  };

  // Batch polling removed - now instant via Cloudinary

  const totalPages = Math.ceil(total / limit);
  const selCount   = selected.size;

  return (
    <div ref={mainRef}>

      <PageHeader
        title="Organized Videos"
        description="Videos classified and organized intelligently. Select a category below to browse files."
      />

      {/* ── Breadcrumb / Folder Navigation ── */}
      {currentFolder && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 'var(--space-24)' }}>
          <button className="btn" onClick={() => setCurrentFolder(null)} style={{ padding: '6px 12px' }}>
            <ChevronLeft size={16} /> <span style={{ fontWeight: 600 }}>Folders</span>
          </button>
          <div style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            / {getDisplayLabel(currentFolder)}
          </div>
        </div>
      )}

      {/* ── Toolbar (Only visible inside a folder) ── */}
      {currentFolder && (
        <div className="tour-toolbar" style={{
          display: 'flex', flexWrap: 'wrap', gap: 'var(--space-12)',
          marginBottom: 'var(--space-24)', alignItems: 'center',
        }}>
          {/* Search */}
          <div style={{ position: 'relative', flex: '1 1 220px' }}>
            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
            <input
              type="text"
              placeholder="Search by filename…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{
                width: '100%', paddingLeft: 32, paddingRight: 10,
                height: 36, background: 'var(--surface-panel)',
                border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)', fontSize: 'var(--font-small)',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Duplicate filter */}
          <select
            value={filterDup}
            onChange={e => setFilterDup(e.target.value)}
            style={{
              height: 36, padding: '0 12px',
              background: 'var(--surface-panel)', border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)', color: 'var(--text-primary)',
              fontSize: 'var(--font-small)', appearance: 'none', cursor: 'pointer',
            }}
          >
            <option value="">All statuses</option>
            <option value="false">Originals only</option>
            <option value="true">Duplicates only</option>
          </select>

          {/* Metadata toggle */}
          <button
            className={`btn${showMeta ? ' btn-primary' : ''} tour-meta-toggle`}
            style={{ height: 36, padding: '0 12px', fontSize: 'var(--font-meta)', gap: 4 }}
            onClick={() => setShowMeta(!showMeta)}
            title={showMeta ? 'Hide metadata' : 'Show metadata'}
          >
            <Brain size={13} /> Meta
          </button>

          {/* Logs toggle */}
          <button
            className={`btn${showLogs ? ' btn-primary' : ''} tour-logs-toggle`}
            style={{ height: 36, padding: '0 12px', fontSize: 'var(--font-meta)', gap: 4 }}
            onClick={() => setShowLogs(!showLogs)}
            title={showLogs ? 'Hide logs' : 'Show processing logs'}
          >
            <FileText size={13} /> Logs
          </button>

          {/* Refresh */}
          <button
            className="btn" style={{ height: 36, padding: '0 10px' }}
            onClick={() => fetchVideos(page)} title="Refresh"
          >
            <RefreshCw size={14} />
          </button>


        </div>
      )}

      {/* ── Processing Logs Panel ── */}
      {currentFolder && showLogs && (
        <div style={{
          background: 'var(--surface-panel)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
          marginBottom: 'var(--space-24)',
          overflow: 'hidden',
        }}>
          <div style={{
            padding: '14px 20px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            background: 'rgba(88,166,255,0.04)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileText size={16} color="var(--accent)" />
              <span style={{ fontWeight: 600, fontSize: 'var(--font-body)', color: 'var(--text-primary)' }}>
                Processing Logs
              </span>
              <span style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)' }}>
                — {getDisplayLabel(currentFolder)}
              </span>
            </div>
            <button
              className="btn"
              style={{ padding: '4px 8px' }}
              onClick={() => setShowLogs(false)}
            >
              <X size={14} />
            </button>
          </div>
          <div style={{ padding: '12px 0' }}>
            <LogsPanel currentFolder={currentFolder} search={search} />
          </div>
        </div>
      )}

      {/* ── Selection bar ── */}
      {currentFolder && videos.length > 0 && !showLogs && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 'var(--space-12)',
          marginBottom: 'var(--space-20)', flexWrap: 'wrap',
        }}>
          <button className="btn" style={{ fontSize: 'var(--font-meta)', padding: '4px 10px' }} onClick={selectAll}>
            Select all ({videos.length})
          </button>
          {selCount > 0 && (
            <>
              <button className="btn" style={{ fontSize: 'var(--font-meta)', padding: '4px 10px' }} onClick={clearAll}>
                <X size={11} /> Clear
              </button>
              <span style={{ fontSize: 'var(--font-meta)', color: 'var(--text-secondary)' }}>
                {selCount} selected
                {selCount > BATCH_MAX && <span style={{ color: 'var(--danger)', marginLeft: 6 }}>⚑ max {BATCH_MAX}</span>}
              </span>
              <button
                className="btn btn-primary"
                style={{ fontSize: 'var(--font-meta)', padding: '4px 14px', marginLeft: 'auto' }}
                onClick={handleBatchDownload}
                disabled={loading || selCount > BATCH_MAX}
              >
                <Archive size={12} /> Download ZIP ({selCount})
              </button>
            </>
          )}
        </div>
      )}

      {/* ── Content Area ── */}
      {!showLogs && (
        currentFolder === null ? (
        /* Folders Grid */
        statsLoading ? (
          <LoadingState message="Loading folders…" />
        ) : Object.keys(folderStats).length === 0 ? (
          <div style={{ textAlign: 'center', padding: 'var(--space-64) var(--space-24)' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-16)' }}>🗂️</div>
            <div style={{ fontWeight: 600, fontSize: 'var(--font-title-card)', marginBottom: 'var(--space-8)' }}>
              No categories found
            </div>
            <div style={{ color: 'var(--text-secondary)', maxWidth: 340, margin: '0 auto' }}>
              Upload footage and run Auto-Organize. Folders will appear here automatically.
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 'var(--space-16)' }}>
            {Object.entries(folderStats)
              .sort(([a], [b]) => getDisplayLabel(a).localeCompare(getDisplayLabel(b)))
              .map(([label, count]) => (
                <FolderCard
                  key={label}
                  label={label}
                  count={count}
                  onClick={setCurrentFolder}
                  onDownloadAll={handleCategoryDownload}
                  isDownloading={downloadingCategory === label}
                />
              ))}
          </div>
        )
      ) : (
        /* Videos Grid inside Folder */
        loading ? (
          <LoadingState message="Loading videos…" />
        ) : videos.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 'var(--space-64) var(--space-24)' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-16)' }}>🎬</div>
            <div style={{ fontWeight: 600, fontSize: 'var(--font-title-card)', marginBottom: 'var(--space-8)' }}>
              No videos found in this folder
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 'var(--space-16)' }}>
            {videos.map(doc => (
              <VideoCard 
                key={doc.id} 
                doc={doc} 
                selected={selected.has(doc.id)} 
                onSelect={toggleSelect} 
                onPreview={setPreviewDoc} 
                onDownload={handleSingleDownload}
                showMeta={showMeta}
              />
            ))}
          </div>
        )
      ))}

      {/* ── Pagination (Only in folder view) ── */}
      {currentFolder && !showLogs && totalPages > 1 && (
        <div style={{ display: 'flex', gap: 'var(--space-8)', justifyContent: 'center', marginTop: 'var(--space-32)', flexWrap: 'wrap' }}>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
            <button
              key={p}
              className={`btn${p === page ? ' btn-primary' : ''}`}
              style={{ minWidth: 36, padding: '4px 10px' }}
              onClick={() => fetchVideos(p)}
            >{p}</button>
          ))}
        </div>
      )}

      {/* ── Count footer ── */}
      {currentFolder && !showLogs && total > 0 && (
        <div style={{ textAlign: 'center', marginTop: 'var(--space-20)', fontSize: 'var(--font-meta)', color: 'var(--text-muted)' }}>
          {total.toLocaleString()} video{total !== 1 ? 's' : ''} in {getDisplayLabel(currentFolder)}
        </div>
      )}

      {/* ── Preview Modal ── */}
      {previewDoc && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.85)', zIndex: 9999,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(4px)'
        }} onClick={() => setPreviewDoc(null)}>
          <div style={{
            background: 'var(--surface)', padding: 'var(--space-16)',
            borderRadius: 'var(--radius-lg)', maxWidth: '90vw', maxHeight: '90vh',
            display: 'flex', flexDirection: 'column', gap: 'var(--space-12)'
          }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontWeight: 600, fontSize: 'var(--font-body)', color: 'var(--text-primary)' }}>
                {previewDoc.display_name || previewDoc.original_filename}
              </div>
              <button 
                onClick={() => setPreviewDoc(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'row', gap: 'var(--space-16)', flexWrap: 'wrap' }}>
              <div style={{ flex: '1 1 600px', background: '#000', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
                 <video 
                    src={previewDoc.cloudinary_url}
                    controls 
                    autoPlay 
                    style={{
                      width: '100%', maxHeight: '70vh', objectFit: 'contain', display: 'block'
                    }}
                 />
              </div>

              {previewDoc.ai_metadata && Object.keys(previewDoc.ai_metadata).length > 0 && (
                <div style={{ 
                  flex: '0 0 300px', 
                  background: 'var(--surface-base)', 
                  border: '1px solid var(--border-subtle)', 
                  borderRadius: 'var(--radius-md)', 
                  padding: 'var(--space-20)',
                  display: 'flex', flexDirection: 'column', gap: 'var(--space-12)',
                  overflowY: 'auto', maxHeight: '70vh'
                }}>
                  <div style={{ fontWeight: 600, fontSize: 'var(--font-title-card)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: 'var(--space-12)', marginBottom: 'var(--space-4)' }}>
                    AI Neural Matrix Logs
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>Dominant Emotion</span>
                    <span style={{ fontWeight: 500, fontSize: 'var(--font-small)', textTransform: 'capitalize', color: 'var(--text-primary)' }}>{previewDoc.ai_metadata.dominant_emotion || 'None'}</span>
                  </div>

                  {previewDoc.ai_metadata.dominant_emotion_confidence != null && (
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>Emotion Confidence</span>
                      <span style={{ fontWeight: 500, fontSize: 'var(--font-small)' }}>
                        {Math.round(previewDoc.ai_metadata.dominant_emotion_confidence)}%
                      </span>
                    </div>
                  )}
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>AI Matching Confidence</span>
                    <span style={{ fontWeight: 500, fontSize: 'var(--font-small)' }}>{Math.round((previewDoc.ai_metadata.average_confidence || 0) * 100)}%</span>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>Demographics Found</span>
                    <span style={{ fontWeight: 500, fontSize: 'var(--font-small)' }}>{previewDoc.ai_metadata.has_faces ? 'Face Activity' : 'No Faces'}</span>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>Total Scenes Tracked</span>
                    <span style={{ fontWeight: 500, fontSize: 'var(--font-small)' }}>{previewDoc.ai_metadata.total_scenes_detected} cuts</span>
                  </div>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)', marginTop: 'var(--space-12)' }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>Category Output Matrix</span>
                    <div style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border-subtle)', borderRadius: 6, padding: '12px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {Object.entries(previewDoc.ai_metadata.label_distribution || {})
                          .sort((a,b) => b[1] - a[1])
                          .map(([key, val]) => (
                        <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--font-meta)' }}>
                          <span style={{ textTransform: 'capitalize', fontWeight: 500 }}>{getDisplayLabel(key)}</span>
                          <span style={{ color: 'var(--text-muted)' }}>{val} scene{val !== 1 ? 's' : ''}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* File hash in preview */}
                  {previewDoc.file_hash && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-8)' }}>
                      <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-small)', display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Hash size={12} /> File Hash
                      </span>
                      <span style={{ fontWeight: 500, fontSize: 'var(--font-meta)', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        {previewDoc.file_hash.substring(0, 16)}…
                      </span>
                    </div>
                  )}

                  <div style={{ marginTop: 'auto', paddingTop: 'var(--space-16)', borderTop: '1px solid var(--border-subtle)', fontSize: 'var(--font-meta)', color: 'var(--success)' }}>
                    ✓ Agent Action: {String(previewDoc.ai_metadata.action_taken || 'auto_organized').replace(/_/g, ' ')}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
