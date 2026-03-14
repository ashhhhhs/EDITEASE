import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ChevronLeft, ChevronRight, Download, Save, Search } from 'lucide-react';
import { API_BASE } from './config';
import { SCENE_LABELS, EMOTIONS } from './constants';

const PAGE_SIZE = 9;

export default function Inspector() {
  const [clips, setClips] = useState([]);
  const [selectedClip, setSelectedClip] = useState(null);
  const [page, setPage] = useState(1);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  // Filters
  const [labelFilter, setLabelFilter] = useState('');
  const [reviewedFilter, setReviewedFilter] = useState('');
  const [videoFilter, setVideoFilter] = useState('');

  // Editing state
  const [editLabel, setEditLabel] = useState('');
  const [editEmotion, setEditEmotion] = useState('');
  const [editReviewed, setEditReviewed] = useState(false);
  const [editNotes, setEditNotes] = useState('');

  const fetchClips = async () => {
    try {
      let url = `${API_BASE}/search?limit=500`;
      if (labelFilter) url += `&scene_label=${labelFilter}`;
      if (reviewedFilter) url += `&reviewed=${reviewedFilter}`;
      if (videoFilter.trim()) url += `&video=${videoFilter.trim()}`;

      const res = await axios.get(url);
      setClips(res.data.results || []);
      setPage(1);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => { fetchClips(); }, []);

  const totalPages = Math.max(1, Math.ceil(clips.length / PAGE_SIZE));
  const pageClips = clips.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const selectClip = (clip) => {
    setSelectedClip(clip);
    setEditLabel(clip.scene_label || 'other');
    setEditEmotion(clip.dominant_emotion_overall || 'null');
    setEditReviewed(clip.reviewed || false);
    setEditNotes(clip.notes || '');
    setSaveSuccess(false);
  };

  const saveClip = async () => {
    if (!selectedClip) return;
    setSaving(true);
    setSaveSuccess(false);
    try {
      const payload = {
        video: selectedClip.video,
        scene_id: selectedClip.scene_id,
        scene_label: editLabel,
        dominant_emotion_overall: editEmotion === 'null' ? null : editEmotion,
        reviewed: editReviewed,
        notes: editNotes
      };
      await axios.post(`${API_BASE}/update_scene`, payload);
      
      setClips(prev => prev.map(c => {
        if (c.video === selectedClip.video && c.scene_id === selectedClip.scene_id) {
          return { ...c, ...payload };
        }
        return c;
      }));
      setSelectedClip({ ...selectedClip, ...payload });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err) {
      console.error(err);
      alert('Save failed: ' + (err.response?.data?.error || err.message));
    }
    setSaving(false);
  };

  const exportClip = async () => {
    if (!selectedClip) return;
    try {
      const res = await axios.post(`${API_BASE}/export`, {
        video: selectedClip.video,
        scene_id: selectedClip.scene_id
      });
      alert(`Exported full video to: ${res.data.output_path}\nDominant scene type: ${res.data.scene_label}`);
    } catch (err) {
      alert('Export failed');
    }
  };

  const handleBulkExport = async () => {
    let query = {};
    if (labelFilter) query.scene_label = labelFilter;
    if (reviewedFilter) query.reviewed = reviewedFilter;
    try {
      const res = await axios.post(`${API_BASE}/export_batch`, query);
      alert(`Export Done! ${res.data.exported_count} success, ${res.data.failed_count} failed.`);
    } catch (err) {
      alert('Export failed.');
    }
  };

  const thumbUrl = (clip) => {
    if (!clip?._id) return null;
    return `${API_BASE}/thumbnail/${clip._id}`;
  };

  const videoUrl = (clip) => {
    if (!clip?._id) return null;
    return `${API_BASE}/video_clip/${clip._id}`;
  };

  return (
    <div className="inspector-layout">
      
      {/* Grid Area */}
      <div className="inspector-grid">
        {/* Filter Bar */}
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '140px' }}>
            <label style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.3rem', display: 'block'}}>Scene Type</label>
            <select value={labelFilter} onChange={e => setLabelFilter(e.target.value)}>
              <option value="">All Types</option>
              {SCENE_LABELS.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: '140px' }}>
            <label style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.3rem', display: 'block'}}>Review Status</label>
            <select value={reviewedFilter} onChange={e => setReviewedFilter(e.target.value)}>
              <option value="">All</option>
              <option value="true">Reviewed</option>
              <option value="false">Unreviewed</option>
            </select>
          </div>
          <div style={{ flex: 1, minWidth: '140px' }}>
            <label style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.3rem', display: 'block'}}>Video Name</label>
            <input value={videoFilter} onChange={e => setVideoFilter(e.target.value)} placeholder="Filter..." />
          </div>
          <button className="btn btn-primary" onClick={fetchClips} style={{height: '38px'}}>
            <Search size={16} /> Search
          </button>
          <button className="btn" onClick={handleBulkExport} style={{height: '38px'}}>
            <Download size={16} /> Export All
          </button>
        </div>

        {/* Stats Bar */}
        <div style={{display: 'flex', gap: '1.5rem', marginBottom: '1rem', color: 'var(--text-muted)', fontSize: '0.85rem'}}>
          <span><strong style={{color: 'var(--text-main)'}}>{clips.length}</strong> clips</span>
          <span><strong style={{color: 'var(--success)'}}>{clips.filter(c => c.reviewed).length}</strong> reviewed</span>
          <span>Page <strong style={{color: 'var(--text-main)'}}>{page}/{totalPages}</strong></span>
        </div>

        {/* Clip Grid */}
        <div className="clip-grid">
          {pageClips.map(clip => {
            const isSelected = selectedClip?.video === clip.video && selectedClip?.scene_id === clip.scene_id;
            const thumb = thumbUrl(clip);
            return (
              <div 
                key={`${clip.video}_${clip.scene_id}`} 
                className={`clip-card ${isSelected ? 'selected' : ''}`}
                onClick={() => selectClip(clip)}
              >
                {thumb ? (
                  <img 
                    src={thumb} 
                    alt={`${clip.video} scene ${clip.scene_id}`} 
                    className="clip-thumb"
                    loading="lazy"
                  />
                ) : (
                  <div className="clip-thumb" style={{display: 'flex', alignItems: 'center', justifyContent:'center', color: '#555', fontSize: '0.85rem'}}>
                    No Thumbnail
                  </div>
                )}
                <div className="clip-info">
                  <div className="clip-title">{clip.video}</div>
                  <div className="clip-meta">Scene {clip.scene_id} • {clip.duration_sec?.toFixed(1)}s</div>
                  {clip.reviewed && <span className="badge reviewed">✓ Reviewed</span>}
                  <span className="badge">{clip.scene_label || 'other'}</span>
                  {clip.dominant_emotion_overall && <span className="badge">{clip.dominant_emotion_overall}</span>}
                </div>
              </div>
            );
          })}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '2rem'}}>
            <button className="btn" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}>
              <ChevronLeft size={18} /> Prev
            </button>
            <span style={{color: 'var(--text-muted)'}}>
              {page} / {totalPages}
            </span>
            <button className="btn" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>
              Next <ChevronRight size={18} />
            </button>
          </div>
        )}
      </div>

      {/* Inspector Panel */}
      <div className="inspector-panel">
        {selectedClip ? (
          <>
            <h3 style={{marginBottom: '0.25rem'}}>{selectedClip.video}</h3>
            <p style={{color: 'var(--text-muted)', marginBottom: '0.75rem', fontSize: '0.9rem'}}>
              Scene {selectedClip.scene_id} • {selectedClip.start_sec?.toFixed(2)}s → {selectedClip.end_sec?.toFixed(2)}s • {selectedClip.duration_sec?.toFixed(1)}s
            </p>

            {/* Thumbnail Preview */}
            {thumbUrl(selectedClip) && (
              <img 
                src={thumbUrl(selectedClip)} 
                alt="Scene thumbnail" 
                style={{width: '100%', borderRadius: '8px', marginBottom: '1rem', border: '1px solid var(--border-color)'}}
              />
            )}

            {/* Video Preview */}
            {videoUrl(selectedClip) && (
              <video 
                src={`${videoUrl(selectedClip)}#t=${selectedClip.start_sec},${selectedClip.end_sec}`}
                controls 
                style={{width: '100%', borderRadius: '8px', marginBottom: '1rem', border: '1px solid var(--border-color)'}}
              />
            )}

            <div className="form-group">
              <label>Scene Type</label>
              <select value={editLabel} onChange={e => setEditLabel(e.target.value)}>
                {SCENE_LABELS.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label>Emotion</label>
              <select value={editEmotion} onChange={e => setEditEmotion(e.target.value)}>
                {EMOTIONS.map(e => <option key={e} value={e}>{e === 'null' ? 'None' : e}</option>)}
              </select>
            </div>

            <div className="form-group" style={{display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer'}}>
              <input 
                type="checkbox" 
                id="rev"
                checked={editReviewed} 
                onChange={e => setEditReviewed(e.target.checked)} 
                style={{width: 'auto'}}
              />
              <label htmlFor="rev" style={{margin: 0, cursor: 'pointer'}}>Reviewed & Approved</label>
            </div>

            <div className="form-group" style={{flex: 1}}>
              <label>Notes</label>
              <textarea 
                value={editNotes} 
                onChange={e => setEditNotes(e.target.value)} 
                style={{height: '80px'}}
                placeholder="Add notes about this scene..."
              />
            </div>

            <div style={{display: 'flex', gap: '0.75rem', marginTop: 'auto'}}>
              <button 
                className={`btn ${saveSuccess ? 'btn-success' : 'btn-primary'}`} 
                onClick={saveClip} 
                disabled={saving}
                style={{flex: 1}}
              >
                <Save size={16} /> {saving ? 'Saving...' : saveSuccess ? 'Saved ✓' : 'Save'}
              </button>
              <button className="btn" onClick={exportClip} style={{flex: 1}}>
                <Download size={16} /> Export Full Video
              </button>
            </div>
          </>
        ) : (
          <div style={{color: 'var(--text-muted)', textAlign: 'center', marginTop: '5rem'}}>
            <p style={{fontSize: '1.1rem', marginBottom: '0.5rem'}}>No clip selected</p>
            <p>Click a card to inspect and review it.</p>
          </div>
        )}
      </div>
    </div>
  );
}
