import React, { useEffect, useState, useCallback } from 'react';
import {
  Folder, Download, RefreshCw, Search,
  CheckCircle, Archive, X, ChevronLeft, PlayCircle
} from 'lucide-react';
import api from './lib/api';
import { useToast } from './hooks/useToast.jsx';
import PageHeader from './components/PageHeader';
import LoadingState from './components/LoadingState';

const POLL_INTERVAL_MS = 2500;
const BATCH_MAX = 10;

const LABEL_MAP = {
  testimonial: 'Testimonials',
  presenter: 'Presenters',
  audience_reaction: 'Audience Reactions',
  text_slide: 'Text Slides',
  screen_recording: 'Screen Recordings',
  'b-roll': 'B-Rolls',
  establishing_shot: 'Establishing Shots',
  other: 'Other'
};

const getDisplayLabel = (key) => {
  if (!key) return 'Other';
  if (LABEL_MAP[key]) return LABEL_MAP[key];
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) + 's';
};

/* ── Label badge ── */
function LabelBadge({ label }) {
  const display = getDisplayLabel(label);
  return (
    <span style={{
      background: 'rgba(88,166,255,0.15)', color: '#58a6ff',
      fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em',
      padding: '2px 8px', borderRadius: 20,
      border: `1px solid rgba(88,166,255,0.33)`,
    }}>{display}</span>
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

/* ── Folder card ── */
function FolderCard({ label, count, onClick }) {
  const display = getDisplayLabel(label);
  return (
    <div
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
        <div>
          <div style={{ fontWeight: 600, fontSize: 'var(--font-body)', color: 'var(--text-primary)' }}>
            {display}
          </div>
          <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)' }}>
            {count} video{count !== 1 ? 's' : ''}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Video card ── */
function VideoCard({ doc, selected, onSelect, onPreview, onDownload }) {
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

  // Filters
  const [search, setSearch]         = useState('');
  const [filterDup, setFilterDup]   = useState('');   // '' | 'true' | 'false'

  // Batch download
  const [batchTask, setBatchTask]   = useState(null);  // { id, status, step }
  const [batchPolling, setBatchPolling] = useState(false);

  const limit = 24;

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

  // Load stats or videos depending on folder state
  useEffect(() => { 
    if (currentFolder === null) {
      fetchStats();
      setVideos([]);  // Clear videos when going back to folders
      setSelected(new Set()); // clear selection
      setSearch(''); // clear search
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
    if (!doc.cloudinary_url) { toast.error('No download URL available'); return; }
    try {
      await api.post('/organized-videos/download', { id: doc.id });
    } catch { }
    window.open(doc.cloudinary_url, '_blank', 'noopener');
  };

  const handleBatchDownload = async () => {
    const ids = Array.from(selected);
    if (ids.length === 0) { toast.error('Select at least one video'); return; }
    if (ids.length > BATCH_MAX) { toast.error(`Batch limit is ${BATCH_MAX} files`); return; }
    try {
      const res = await api.post('/organized-videos/download-batch', { ids });
      setBatchTask({ id: res.data.task_id, status: 'PENDING', step: 'queued' });
      setBatchPolling(true);
      toast.info(`Building ZIP for ${ids.length} file${ids.length > 1 ? 's' : ''}…`);
    } catch (err) {
      toast.error(err.friendlyMessage || 'Failed to start batch download');
    }
  };

  // Poll batch ZIP task
  useEffect(() => {
    if (!batchPolling || !batchTask?.id) return;
    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/organized-videos/download-batch/${batchTask.id}`);
        const { status, progress_step } = res.data;
        setBatchTask(t => ({ ...t, status, step: progress_step }));
        if (status === 'SUCCESS') {
          clearInterval(interval);
          setBatchPolling(false);
          const a = document.createElement('a');
          a.href = `${api.defaults.baseURL}/organized-videos/download-batch/${batchTask.id}`;
          a.setAttribute('download', 'organized-videos.zip');
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          toast.success('ZIP ready — downloading');
          setBatchTask(null);
        } else if (status === 'FAILURE') {
          clearInterval(interval);
          setBatchPolling(false);
          toast.error(res.data.error || 'Batch ZIP failed');
          setBatchTask(null);
        }
      } catch {
        clearInterval(interval);
        setBatchPolling(false);
      }
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [batchPolling, batchTask?.id, toast]);

  const totalPages = Math.ceil(total / limit);
  const selCount   = selected.size;

  return (
    <div>
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
        <div style={{
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

          {/* Refresh */}
          <button
            className="btn" style={{ height: 36, padding: '0 10px' }}
            onClick={() => fetchVideos(page)} title="Refresh"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      )}

      {/* ── Selection bar ── */}
      {currentFolder && videos.length > 0 && (
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
                disabled={batchPolling || selCount > BATCH_MAX}
              >
                {batchPolling
                  ? <><RefreshCw size={12} style={{ animation: 'spin 1s linear infinite' }} /> {batchTask?.step || 'Building…'}</>
                  : <><Archive size={12} /> Download ZIP ({selCount})</>
                }
              </button>
            </>
          )}
        </div>
      )}

      {/* ── Content Area ── */}
      {currentFolder === null ? (
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
                <FolderCard key={label} label={label} count={count} onClick={setCurrentFolder} />
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
              />
            ))}
          </div>
        )
      )}

      {/* ── Pagination (Only in folder view) ── */}
      {currentFolder && totalPages > 1 && (
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
      {currentFolder && total > 0 && (
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
