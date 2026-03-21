import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ChevronLeft, ChevronRight, CheckSquare, Search, Save, Settings2, Video, Square, CheckSquare as CheckSquareIcon, ListFilter } from 'lucide-react';
import { API_BASE } from './config';
import { SCENE_LABELS, EMOTIONS } from './constants';
import PageHeader from './components/PageHeader';
import LoadingState from './components/LoadingState';
import EmptyState from './components/EmptyState';

export default function Inspector() {
  const [clips, setClips] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 24;
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [fLabel, setFLabel] = useState('');
  const [fEmotion, setFEmotion] = useState('');
  const [fReviewed, setFReviewed] = useState('false'); // default to unreviewed
  const [fUncertain, setFUncertain] = useState('');
  
  // Selection
  const [selectedKeys, setSelectedKeys] = useState(new Set());
  
  // Bulk Actions form
  const [bLabel, setBLabel] = useState('');
  const [bEmotion, setBEmotion] = useState('');
  const [bReviewed, setBReviewed] = useState('');
  const [bUncertain, setBUncertain] = useState('');

  const fetchClips = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/search?page=${page}&limit=${limit}`;
      if (fLabel) url += `&scene_label=${fLabel}`;
      if (fEmotion) url += `&emotion=${fEmotion}`;
      if (fReviewed) url += `&reviewed=${fReviewed}`;
      if (fUncertain) url += `&uncertain=${fUncertain}`;

      const res = await axios.get(url);
      setClips(res.data.results || []);
      setTotal(res.data.total || 0);
      setSelectedKeys(new Set());
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  useEffect(() => { fetchClips(); }, [page]);

  const handleSearchClick = () => {
      setPage(1);
      fetchClips();
  };

  const toggleSelect = (key) => {
    const newKeys = new Set(selectedKeys);
    if (newKeys.has(key)) newKeys.delete(key);
    else newKeys.add(key);
    setSelectedKeys(newKeys);
  };
  
  const toggleAll = () => {
    if (selectedKeys.size === clips.length && clips.length > 0) {
        setSelectedKeys(new Set());
    } else {
        setSelectedKeys(new Set(clips.map(c => `${c.video}::${c.scene_id}`)));
    }
  };

  const handleBulkUpdate = async () => {
      if (selectedKeys.size === 0) return alert('No clips selected');
      const updateData = {};
      if (bLabel) updateData.scene_label = bLabel;
      if (bEmotion) updateData.dominant_emotion_overall = bEmotion === 'null' ? null : bEmotion;
      if (bReviewed) updateData.reviewed = bReviewed === 'true';
      if (bUncertain) updateData.uncertain = bUncertain === 'true';
      
      if (Object.keys(updateData).length === 0) return alert('Select an action to apply');
      
      try {
          await axios.post(`${API_BASE}/review/bulk-update`, {
              scene_keys: Array.from(selectedKeys),
              update_data: updateData
          });
          setBLabel(''); setBEmotion(''); setBReviewed(''); setBUncertain('');
          fetchClips();
      } catch (err) {
          alert('Bulk update failed: ' + (err.response?.data?.error || err.message));
      }
  };

  const totalPages = Math.ceil(total / limit) || 1;
  const thumbUrl = (clip) => clip?._id ? `${API_BASE}/thumbnail/${clip._id}` : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <PageHeader 
        title="Moderation Queue" 
        description="Filter entirely through extracted scenes to classify, approve, or mark uncertain batches of data directly from the system."
      />

      <div style={{ display: 'flex', gap: 'var(--space-32)', flex: 1, overflow: 'hidden' }}>
        
        {/* Sidebar Controls */}
        <div className="panel" style={{ width: '320px', padding: 'var(--space-24)', display: 'flex', flexDirection: 'column', gap: 'var(--space-32)', flexShrink: 0, overflowY: 'auto' }}>
            
            {/* Filters Section */}
            <div>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', marginBottom: 'var(--space-16)', fontSize: 'var(--font-body)', fontWeight: 600 }}><ListFilter size={18} color="var(--text-secondary)" /> Search Filters</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
                    <div>
                        <label style={{ display: 'block', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>Review Status</label>
                        <select className="styled-input" value={fReviewed} onChange={e => setFReviewed(e.target.value)}>
                            <option value="">All</option>
                            <option value="true">Reviewed</option>
                            <option value="false">Unreviewed (Pending)</option>
                        </select>
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>Uncertainty</label>
                        <select className="styled-input" value={fUncertain} onChange={e => setFUncertain(e.target.value)}>
                            <option value="">All</option>
                            <option value="true">Flagged Uncertain</option>
                            <option value="false">Confident</option>
                        </select>
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>Scene Type</label>
                        <select className="styled-input" value={fLabel} onChange={e => setFLabel(e.target.value)}>
                            <option value="">All Types</option>
                            {SCENE_LABELS.map(l => <option key={l} value={l}>{l}</option>)}
                        </select>
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>Emotion</label>
                        <select className="styled-input" value={fEmotion} onChange={e => setFEmotion(e.target.value)}>
                            <option value="">All Emotions</option>
                            {EMOTIONS.map(e => <option key={e} value={e}>{e === 'null' ? 'None' : e}</option>)}
                        </select>
                    </div>
                    <button className="btn btn-primary" onClick={handleSearchClick} style={{ marginTop: 'var(--space-8)' }}><Search size={16} /> Apply Filters</button>
                </div>
            </div>

            <hr style={{ border: 0, borderTop: '1px solid var(--border-subtle)', margin: 0 }} />

            {/* Bulk Actions Section */}
            <div style={{ opacity: selectedKeys.size > 0 ? 1 : 0.5, pointerEvents: selectedKeys.size > 0 ? 'auto' : 'none', transition: 'opacity 0.2s' }}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', marginBottom: 'var(--space-16)', fontSize: 'var(--font-body)', fontWeight: 600, color: selectedKeys.size > 0 ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                    <Settings2 size={18} /> Batch Actions {selectedKeys.size > 0 && <span className="badge info" style={{ padding: '2px 6px', fontSize: '0.65rem' }}>{selectedKeys.size}</span>}
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-12)' }}>
                    <div>
                        <label style={{ display: 'block', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>Override Status</label>
                        <select className="styled-input" value={bReviewed} onChange={e => setBReviewed(e.target.value)}>
                            <option value="">-- No Change --</option>
                            <option value="true">Mark as Reviewed</option>
                            <option value="false">Mark as Unreviewed</option>
                        </select>
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>Override Uncertainty</label>
                        <select className="styled-input" value={bUncertain} onChange={e => setBUncertain(e.target.value)}>
                            <option value="">-- No Change --</option>
                            <option value="true">Flag as Uncertain</option>
                            <option value="false">Remove Flag</option>
                        </select>
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>Assign Scene Type</label>
                        <select className="styled-input" value={bLabel} onChange={e => setBLabel(e.target.value)}>
                            <option value="">-- No Change --</option>
                            {SCENE_LABELS.map(l => <option key={l} value={l}>{l}</option>)}
                        </select>
                    </div>
                    <button className="styled-button" onClick={handleBulkUpdate} style={{ marginTop: 'var(--space-8)', background: 'var(--accent)', color: '#fff', borderColor: 'transparent' }}>
                        <Save size={16} /> Execute Batch Update
                    </button>
                </div>
            </div>

        </div>

        {/* Main Grid Area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-20)', paddingBottom: 'var(--space-16)', borderBottom: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-16)' }}>
                    <button onClick={toggleAll} style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 'var(--space-8)', fontWeight: 500 }}>
                        {selectedKeys.size === clips.length && clips.length > 0 ? <CheckSquareIcon size={20} color="var(--accent)" /> : <Square size={20} color="var(--text-secondary)" />} Select All
                    </button>
                    <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>{total} results found</span>
                </div>
                
                <div style={{ display: 'flex', gap: 'var(--space-16)', alignItems: 'center' }}>
                    <button className="btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                        <ChevronLeft size={16} /> Prev
                    </button>
                    <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>Page {page} of {totalPages}</span>
                    <button className="btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
                        Next <ChevronRight size={16} />
                    </button>
                </div>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', paddingRight: 'var(--space-8)', paddingBottom: 'var(--space-32)' }}>
                {loading ? (
                    <LoadingState type="grid" />
                ) : clips.length === 0 ? (
                    <EmptyState icon={Search} title="No Clips Found" message="Try adjusting your filters or search terms." />
                ) : (
                    <div className="clip-grid">
                        {clips.map(clip => {
                            const key = `${clip.video}::${clip.scene_id}`;
                            const isSelected = selectedKeys.has(key);
                            const thumb = thumbUrl(clip);
                            
                            return (
                                <div 
                                    key={key} 
                                    className={`clip-card ${isSelected ? 'selected' : ''}`}
                                    onClick={() => toggleSelect(key)}
                                >
                                    <div style={{ position: 'absolute', top: 'var(--space-8)', left: 'var(--space-8)', zIndex: 10 }}>
                                        {isSelected ? <CheckSquareIcon size={22} color="var(--accent)" fill="var(--surface-base)" /> : <Square size={22} color="#fff" style={{filter: 'drop-shadow(0 0 2px rgba(0,0,0,0.8))'}} />}
                                    </div>
                                    {thumb ? (
                                        <img src={thumb} alt={key} className="clip-thumb" loading="lazy" />
                                    ) : (
                                        <div className="clip-thumb" style={{display: 'flex', alignItems: 'center', justifyContent:'center', color: 'var(--text-muted)'}}><Video size={32} /></div>
                                    )}
                                    <div className="clip-info">
                                        <div className="clip-title">{clip.video}</div>
                                        <div className="clip-meta" style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-4)' }}>
                                            <span>Scene {clip.scene_id}</span>
                                            <span>{clip.duration_sec?.toFixed(1)}s</span>
                                        </div>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', marginTop: 'var(--space-12)' }}>
                                            <span className="badge" style={{ padding: '2px 8px', fontSize: '0.65rem' }}>{clip.scene_label || 'other'}</span>
                                            {clip.reviewed ? (
                                                <span className="badge success" style={{ padding: '2px 8px', fontSize: '0.65rem' }}>Reviewed</span>
                                            ) : (
                                                <span className="badge danger" style={{ padding: '2px 8px', fontSize: '0.65rem' }}>Pending</span>
                                            )}
                                            {clip.uncertain && (
                                                <span className="badge warning" style={{ padding: '2px 8px', fontSize: '0.65rem' }}>Uncertain</span>
                                            )}
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
