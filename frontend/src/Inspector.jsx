import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, CheckSquare, Search, Save, Settings2, Video, Square, CheckSquare as CheckSquareIcon, ListFilter } from 'lucide-react';
import { SCENE_LABELS, EMOTIONS } from './constants';
import PageHeader from './components/PageHeader';
import LoadingState from './components/LoadingState';
import EmptyState from './components/EmptyState';
import api from './lib/api';
import { useToast } from './hooks/useToast.jsx';

export default function Inspector() {
  const toast = useToast();
  const [clips, setClips] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 24;
  const [loading, setLoading] = useState(true);
  
  const [fLabel, setFLabel] = useState('');
  const [fEmotion, setFEmotion] = useState('');
  const [fReviewed, setFReviewed] = useState('false');
  const [fUncertain, setFUncertain] = useState('');
  
  const [selectedKeys, setSelectedKeys] = useState(new Set());
  const [bLabel, setBLabel] = useState('');
  const [bEmotion, setBEmotion] = useState('');
  const [bReviewed, setBReviewed] = useState('');
  const [bUncertain, setBUncertain] = useState('');
  const [bulkLoading, setBulkLoading] = useState(false);

  const fetchClips = async () => {
    setLoading(true);
    try {
      let url = `/search?page=${page}&limit=${limit}`;
      if (fLabel) url += `&scene_label=${fLabel}`;
      if (fEmotion) url += `&emotion=${fEmotion}`;
      if (fReviewed) url += `&reviewed=${fReviewed}`;
      if (fUncertain) url += `&uncertain=${fUncertain}`;
      const res = await api.get(url);
      setClips(res.data.results || []);
      setTotal(res.data.total || 0);
      setSelectedKeys(new Set());
    } catch (err) {
      toast.error(err.friendlyMessage || 'Failed to load clips');
    }
    setLoading(false);
  };

  useEffect(() => { fetchClips(); }, [page]);

  const handleSearchClick = () => { setPage(1); fetchClips(); };

  const toggleSelect = (key) => {
    const newKeys = new Set(selectedKeys);
    if (newKeys.has(key)) newKeys.delete(key); else newKeys.add(key);
    setSelectedKeys(newKeys);
  };
  
  const toggleAll = () => {
    if (selectedKeys.size === clips.length && clips.length > 0) setSelectedKeys(new Set());
    else setSelectedKeys(new Set(clips.map(c => `${c.video}::${c.scene_id}`)));
  };

  const handleBulkUpdate = async () => {
    if (selectedKeys.size === 0) { toast.warning('No clips selected'); return; }
    const updateData = {};
    if (bLabel) updateData.scene_label = bLabel;
    if (bEmotion) updateData.dominant_emotion_overall = bEmotion === 'null' ? null : bEmotion;
    if (bReviewed) updateData.reviewed = bReviewed === 'true';
    if (bUncertain) updateData.uncertain = bUncertain === 'true';
    if (Object.keys(updateData).length === 0) { toast.warning('Select at least one action to apply'); return; }

    setBulkLoading(true);
    try {
      await api.post('/review/bulk-update', { scene_keys: Array.from(selectedKeys), update_data: updateData });
      toast.success(`Updated ${selectedKeys.size} clips successfully`);
      setBLabel(''); setBEmotion(''); setBReviewed(''); setBUncertain('');
      fetchClips();
    } catch (err) {
      toast.error(err.friendlyMessage || 'Bulk update failed');
    }
    setBulkLoading(false);
  };

  const totalPages = Math.ceil(total / limit) || 1;
  const thumbUrl = (clip) => clip?._id ? `${import.meta.env.VITE_API_BASE || ''}/api/thumbnail/${clip._id}` : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <PageHeader 
        title="Moderation Queue"
        description="Filter and batch-classify extracted scenes across all processed videos."
      />

      <div style={{ display: 'flex', gap: 'var(--space-32)', flex: 1, overflow: 'hidden' }}>
        
        {/* Sidebar */}
        <div className="panel" style={{ width: '300px', padding: 'var(--space-24)', display: 'flex', flexDirection: 'column', gap: 'var(--space-24)', flexShrink: 0, overflowY: 'auto' }}>
          
          <div>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', marginBottom: 'var(--space-16)', fontSize: 'var(--font-body)', fontWeight: 600 }}>
              <ListFilter size={16} color="var(--text-secondary)" /> Filters
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-12)' }}>
              {[
                { label: 'Review Status', value: fReviewed, setter: setFReviewed, opts: [['','All'],['true','Reviewed'],['false','Unreviewed']] },
                { label: 'Uncertainty', value: fUncertain, setter: setFUncertain, opts: [['','All'],['true','Uncertain'],['false','Confident']] },
              ].map(({ label, value, setter, opts }) => (
                <div key={label}>
                  <label style={{ display: 'block', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>{label}</label>
                  <select value={value} onChange={e => setter(e.target.value)}>
                    {opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                </div>
              ))}
              <div>
                <label style={{ display: 'block', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>Scene Type</label>
                <select value={fLabel} onChange={e => setFLabel(e.target.value)}>
                  <option value="">All Types</option>
                  {SCENE_LABELS.map(l => <option key={l} value={l}>{l}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>Emotion</label>
                <select value={fEmotion} onChange={e => setFEmotion(e.target.value)}>
                  <option value="">All Emotions</option>
                  {EMOTIONS.map(e => <option key={e} value={e}>{e === 'null' ? 'None' : e}</option>)}
                </select>
              </div>
              <button className="btn btn-primary" onClick={handleSearchClick} style={{ marginTop: 'var(--space-4)' }}>
                <Search size={14} /> Apply Filters
              </button>
            </div>
          </div>

          <hr style={{ border: 0, borderTop: '1px solid var(--border-subtle)' }} />

          <div style={{ opacity: selectedKeys.size > 0 ? 1 : 0.45, pointerEvents: selectedKeys.size > 0 ? 'auto' : 'none', transition: 'opacity 0.2s' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', marginBottom: 'var(--space-16)', fontSize: 'var(--font-body)', fontWeight: 600 }}>
              <Settings2 size={16} color="var(--text-secondary)" /> Batch Actions
              {selectedKeys.size > 0 && <span className="badge info" style={{ padding: '1px 6px', fontSize: '0.65rem' }}>{selectedKeys.size}</span>}
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-12)' }}>
              {[
                { label: 'Override Status', value: bReviewed, setter: setBReviewed, opts: [['','— No Change —'],['true','Mark Reviewed'],['false','Mark Unreviewed']] },
                { label: 'Override Uncertainty', value: bUncertain, setter: setBUncertain, opts: [['','— No Change —'],['true','Flag Uncertain'],['false','Remove Flag']] },
              ].map(({ label, value, setter, opts }) => (
                <div key={label}>
                  <label style={{ display: 'block', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>{label}</label>
                  <select value={value} onChange={e => setter(e.target.value)}>
                    {opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                </div>
              ))}
              <div>
                <label style={{ display: 'block', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>Assign Scene Type</label>
                <select value={bLabel} onChange={e => setBLabel(e.target.value)}>
                  <option value="">— No Change —</option>
                  {SCENE_LABELS.map(l => <option key={l} value={l}>{l}</option>)}
                </select>
              </div>
              <button className="btn btn-primary" onClick={handleBulkUpdate} disabled={bulkLoading} style={{ marginTop: 'var(--space-4)' }}>
                <Save size={14} /> {bulkLoading ? 'Applying...' : 'Execute Batch'}
              </button>
            </div>
          </div>
        </div>

        {/* Main Grid */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-16)', paddingBottom: 'var(--space-16)', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-16)' }}>
              <button onClick={toggleAll} style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 'var(--space-8)', fontWeight: 500, fontSize: 'var(--font-small)' }}>
                {selectedKeys.size === clips.length && clips.length > 0
                  ? <CheckSquareIcon size={18} color="var(--accent)" />
                  : <Square size={18} color="var(--text-secondary)" />
                }
                Select All
              </button>
              <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>{total} clips</span>
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-12)', alignItems: 'center' }}>
              <button className="btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft size={16} /> Prev</button>
              <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)', fontVariantNumeric: 'tabular-nums' }}>Page {page} / {totalPages}</span>
              <button className="btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next <ChevronRight size={16} /></button>
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', paddingBottom: 'var(--space-32)' }}>
            {loading ? (
              <LoadingState type="grid" />
            ) : clips.length === 0 ? (
              <EmptyState icon={Search} title="No Clips Found" message="Adjust your filters or reset to browse all clips." action={<button className="btn btn-primary" onClick={() => { setFLabel(''); setFEmotion(''); setFReviewed(''); setFUncertain(''); setPage(1); fetchClips(); }}>Reset Filters</button>} />
            ) : (
              <div className="clip-grid">
                {clips.map(clip => {
                  const key = `${clip.video}::${clip.scene_id}`;
                  const isSelected = selectedKeys.has(key);
                  const thumb = clip?._id ? `/api/thumbnail/${clip._id}` : null; 
                  return (
                    <div key={key} className={`clip-card stagger-item ${isSelected ? 'selected' : ''}`} onClick={() => toggleSelect(key)}>
                      <div style={{ position: 'absolute', top: 'var(--space-8)', left: 'var(--space-8)', zIndex: 10 }}>
                        {isSelected ? <CheckSquareIcon size={20} color="var(--accent)" style={{ filter: 'drop-shadow(0 0 4px rgba(0,0,0,0.6))' }} /> : <Square size={20} color="#fff" style={{ filter: 'drop-shadow(0 0 2px rgba(0,0,0,0.8))' }} />}
                      </div>
                      {thumb ? <img src={thumb} alt={key} className="clip-thumb" loading="lazy" /> : <div className="clip-thumb" style={{display:'flex',alignItems:'center',justifyContent:'center',color:'var(--text-muted)'}}><Video size={32} /></div>}
                      <div className="clip-info">
                        <div className="clip-title">{clip.video}</div>
                        <div className="clip-meta" style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-4)' }}>
                          <span>Scene {clip.scene_id}</span>
                          <span>{clip.duration_sec?.toFixed(1)}s</span>
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-4)', marginTop: 'var(--space-8)' }}>
                          <span className="badge" style={{ fontSize: '0.65rem' }}>{clip.scene_label || 'other'}</span>
                          <span className={`badge ${clip.reviewed ? 'success' : 'danger'}`} style={{ fontSize: '0.65rem' }}>{clip.reviewed ? 'Reviewed' : 'Pending'}</span>
                          {clip.uncertain && <span className="badge warning" style={{ fontSize: '0.65rem' }}>Uncertain</span>}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
