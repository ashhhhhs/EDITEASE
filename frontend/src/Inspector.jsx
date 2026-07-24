import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, CheckSquare, Search, Save, Settings2, Video, Square, CheckSquare as CheckSquareIcon, ListFilter, Send, ShieldCheck, XCircle, UserPlus, Activity } from 'lucide-react';
import { SCENE_LABELS, EMOTIONS, emotionColors } from './constants';
import PageHeader from './components/PageHeader';
import LoadingState from './components/LoadingState';
import EmptyState from './components/EmptyState';
import { API_BASE } from './config';
import api from './lib/api';
import { useToast } from './hooks/useToast.jsx';

const notifyReviewRequestsChanged = () => {
  window.dispatchEvent(new Event('review-requests-changed'));
};

const formatAuditAction = (action = '') => action
  .split('_')
  .filter(Boolean)
  .map(part => part.charAt(0).toUpperCase() + part.slice(1))
  .join(' ');

// Compact per-clip emotion readout: the scene's dominant emotion, a mid-clip shift badge when
// the expression changes partway through, and a segmented strip of the per-frame samples so a
// reviewer can see the arc a single label can't represent.
function EmotionTimeline({ clip }) {
  const timeline = Array.isArray(clip.emotion_timeline) ? clip.emotion_timeline : [];
  const dominant = clip.dominant_emotion_overall;
  const shift = clip.emotion_shift;

  if (timeline.length === 0 && !dominant && !shift?.shifted) return null;

  const colorFor = (emo) => (emo && emotionColors[emo]) || emotionColors._none;

  return (
    <div className="emotion-block">
      <div className="emotion-head">
        {dominant ? (
          <span className="emotion-dom">
            <span className="emotion-dot" style={{ background: colorFor(dominant) }} />
            {dominant}
          </span>
        ) : (
          <span className="emotion-dom muted">no emotion</span>
        )}
        {shift?.shifted && (
          <span
            className="badge warning emotion-shift-badge"
            title={`Expression changes mid-clip: ${shift.from} → ${shift.to}`}
          >
            <Activity size={11} /> {shift.from} → {shift.to}
          </span>
        )}
      </div>
      {timeline.length > 0 && (
        <div className="emotion-strip" aria-hidden="true">
          {timeline.map((f, i) => {
            const emo = f.face_detected ? f.emotion : null;
            const title = emo
              ? `${emo}${f.confidence != null ? ` · ${Math.round(f.confidence)}%` : ''}`
              : 'no face';
            return (
              <span
                key={i}
                className="emotion-seg"
                style={{ background: colorFor(emo) }}
                title={title}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function Inspector({ currentUser }) {
  const toast = useToast();
  const [searchParams] = useSearchParams();
  const [clips, setClips] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 24;
  const [loading, setLoading] = useState(true);

  const [fLabel, setFLabel] = useState('');
  const [fEmotion, setFEmotion] = useState('');
  const [fReviewed, setFReviewed] = useState(() => searchParams.has('reviewed') ? searchParams.get('reviewed') || '' : 'false');
  const [fUncertain, setFUncertain] = useState('');
  const [fRequest, setFRequest] = useState(() => searchParams.get('request') || '');
  const [fAssignedToMe, setFAssignedToMe] = useState(() => searchParams.get('assigned_to_me') || '');
  const [fRequestedByMe, setFRequestedByMe] = useState(() => searchParams.get('requested_by_me') || '');

  const [selectedKeys, setSelectedKeys] = useState(new Set());
  const [bLabel, setBLabel] = useState('');
  const [bEmotion, setBEmotion] = useState('');
  const [bReviewed, setBReviewed] = useState('');
  const [bUncertain, setBUncertain] = useState('');
  const [bulkLoading, setBulkLoading] = useState(false);
  const [requestReason, setRequestReason] = useState('');
  const [requestLoading, setRequestLoading] = useState(false);
  const [reviewAssignees, setReviewAssignees] = useState([]);
  const [selectedAssignee, setSelectedAssignee] = useState('');
  const [selectedPeerAssignee, setSelectedPeerAssignee] = useState('');
  const [assignmentNote, setAssignmentNote] = useState('');
  const [peerReason, setPeerReason] = useState('');

  useEffect(() => {
    if (!['admin', 'editor'].includes(currentUser?.role)) return;
    api.get('/review/assignees')
      .then(res => setReviewAssignees(res.data.users || []))
      .catch(err => toast.error(err.friendlyMessage || 'Failed to load reviewers'));
  }, [currentUser?.id, currentUser?.role, toast]);

  useEffect(() => {
    setFRequest(searchParams.get('request') || '');
    setFAssignedToMe(searchParams.get('assigned_to_me') || '');
    setFRequestedByMe(searchParams.get('requested_by_me') || '');
    setFReviewed(searchParams.has('reviewed') ? searchParams.get('reviewed') || '' : 'false');
  }, [searchParams]);

  const buildSearchUrl = (overrides = {}) => {
    const filters = {
      page,
      fLabel,
      fEmotion,
      fReviewed,
      fUncertain,
      fRequest,
      fAssignedToMe,
      fRequestedByMe,
      ...overrides,
    };
    const params = new URLSearchParams({
      page: String(filters.page),
      limit: String(limit),
    });

    if (filters.fLabel) params.set('scene_label', filters.fLabel);
    if (filters.fEmotion) params.set('emotion', filters.fEmotion);
    if (filters.fReviewed) params.set('reviewed', filters.fReviewed);
    if (filters.fUncertain) params.set('uncertain', filters.fUncertain);
    if (filters.fRequest) params.set('review_request_status', filters.fRequest);
    if (filters.fAssignedToMe) params.set('assigned_to_me', filters.fAssignedToMe);
    if (filters.fRequestedByMe) params.set('requested_by_me', filters.fRequestedByMe);

    return `/search?${params.toString()}`;
  };

  const fetchClips = async (overrides = {}) => {
    setLoading(true);
    try {
      const res = await api.get(buildSearchUrl(overrides));
      setClips(res.data.results || []);
      setTotal(res.data.total || 0);
      setSelectedKeys(new Set());
    } catch (err) {
      toast.error(err.friendlyMessage || 'Failed to load clips');
    }
    setLoading(false);
  };

  useEffect(() => { fetchClips(); }, [page]);

  useEffect(() => {
    if (page === 1) fetchClips();
    else setPage(1);
  }, [fRequest, fAssignedToMe, fRequestedByMe, fReviewed]);

  const handleSearchClick = () => {
    setPage(1);
    fetchClips({ page: 1 });
  };

  const resetFilters = () => {
    const reset = {
      page: 1,
      fLabel: '',
      fEmotion: '',
      fReviewed: '',
      fUncertain: '',
      fRequest: '',
      fAssignedToMe: '',
      fRequestedByMe: '',
    };
    setFLabel('');
    setFEmotion('');
    setFReviewed('');
    setFUncertain('');
    setFRequest('');
    setFAssignedToMe('');
    setFRequestedByMe('');
    setPage(1);
    fetchClips(reset);
  };

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
      notifyReviewRequestsChanged();
      fetchClips();
    } catch (err) {
      toast.error(err.friendlyMessage || 'Bulk update failed');
    }
    setBulkLoading(false);
  };

  const handleRequestAdminReview = async () => {
    if (selectedKeys.size === 0) { toast.warning('No clips selected'); return; }
    if (!requestReason.trim()) { toast.warning('Add a reason for admin review'); return; }

    setRequestLoading(true);
    try {
      const res = await api.post('/review/request-admin', {
        scene_keys: Array.from(selectedKeys),
        reason: requestReason.trim(),
      });
      toast.success(`Requested admin review for ${res.data.requested_count || selectedKeys.size} clips`);
      setRequestReason('');
      notifyReviewRequestsChanged();
      fetchClips();
    } catch (err) {
      toast.error(err.friendlyMessage || 'Failed to request admin review');
    }
    setRequestLoading(false);
  };

  const handleResolveRequests = async (status) => {
    if (selectedKeys.size === 0) { toast.warning('No clips selected'); return; }

    setRequestLoading(true);
    try {
      const res = await api.post('/review/requests/resolve', {
        scene_keys: Array.from(selectedKeys),
        status,
      });
      toast.success(`${status === 'resolved' ? 'Resolved' : 'Dismissed'} ${res.data.resolved_count || 0} requests`);
      notifyReviewRequestsChanged();
      fetchClips();
    } catch (err) {
      toast.error(err.friendlyMessage || 'Failed to update review requests');
    }
    setRequestLoading(false);
  };

  const handleAssignRequests = async () => {
    if (selectedKeys.size === 0) { toast.warning('No clips selected'); return; }
    if (!selectedAssignee) { toast.warning('Choose an editor or reviewer'); return; }

    setRequestLoading(true);
    try {
      const res = await api.post('/review/requests/assign', {
        scene_keys: Array.from(selectedKeys),
        assignee_id: selectedAssignee,
        note: assignmentNote.trim(),
      });
      const assigneeName = res.data.assignee?.name || res.data.assignee?.email || 'selected reviewer';
      toast.success(`Assigned ${res.data.assigned_count || 0} request${res.data.assigned_count === 1 ? '' : 's'} to ${assigneeName}`);
      setAssignmentNote('');
      notifyReviewRequestsChanged();
      fetchClips();
    } catch (err) {
      toast.error(err.friendlyMessage || 'Failed to assign review requests');
    }
    setRequestLoading(false);
  };

  const handleRequestPeerReview = async () => {
    if (selectedKeys.size === 0) { toast.warning('No clips selected'); return; }
    if (!selectedPeerAssignee) { toast.warning('Choose an editor or reviewer'); return; }
    if (!peerReason.trim()) { toast.warning('Add a reason for peer review'); return; }

    setRequestLoading(true);
    try {
      const res = await api.post('/review/request-peer', {
        scene_keys: Array.from(selectedKeys),
        assignee_id: selectedPeerAssignee,
        reason: peerReason.trim(),
      });
      const assigneeName = res.data.assignee?.name || res.data.assignee?.email || 'selected reviewer';
      toast.success(`Requested peer review from ${assigneeName}`);
      setPeerReason('');
      notifyReviewRequestsChanged();
      fetchClips();
    } catch (err) {
      toast.error(err.friendlyMessage || 'Failed to request peer review');
    }
    setRequestLoading(false);
  };

  const totalPages = Math.ceil(total / limit) || 1;
  const selectedCount = selectedKeys.size;
  const hasSelection = selectedCount > 0;
  const thumbUrl = (clip) => clip?._id ? `${API_BASE}/thumbnail/${clip._id}` : null;

  return (
    <div className="review-page">
      <PageHeader
        title="Moderation Queue"
        eyebrow="REVIEW / QUEUE"
        description="Filter, assign, and batch-classify extracted scenes with a clear review trail."
      />

      <div className="review-shell">
        <aside className="review-rail">
          <section className="review-panel">
            <div className="review-section-header">
              <div>
                <div className="mono-caps">Browse</div>
                <h3><ListFilter size={16} /> Filters</h3>
              </div>
              <button className="btn btn-sm" onClick={resetFilters}>Reset</button>
            </div>

            <div className="review-control-group">
              <label>Review Status</label>
              <div className="filter-chips compact">
                {[['', 'All'], ['true', 'Reviewed'], ['false', 'Unreviewed']].map(([v, l]) => (
                  <button key={v} className={`chip${fReviewed === v ? ' active' : ''}`} onClick={() => setFReviewed(v)}>{l}</button>
                ))}
              </div>
            </div>

            <div className="review-control-group">
              <label>Uncertainty</label>
              <div className="filter-chips compact">
                {[['', 'All'], ['true', 'Uncertain'], ['false', 'Confident']].map(([v, l]) => (
                  <button key={v} className={`chip${fUncertain === v ? ' active' : ''}`} onClick={() => setFUncertain(v)}>{l}</button>
                ))}
              </div>
            </div>

            <div className="review-control-group">
              <label>Request Status</label>
              <div className="filter-chips compact">
                {[['', 'All'], ['open', 'Open'], ['assigned', 'Assigned'], ['resolved', 'Resolved'], ['dismissed', 'Dismissed'], ['__NONE__', 'None']].map(([v, l]) => (
                  <button key={v} className={`chip${fRequest === v ? ' active' : ''}`} onClick={() => setFRequest(v)}>{l}</button>
                ))}
              </div>
            </div>

            <div className="review-two-col">
              <div className="review-control-group">
                <label>Assignment</label>
                <div className="filter-chips compact">
                  {[['', 'All'], ['true', 'Mine']].map(([v, l]) => (
                    <button key={v} className={`chip${fAssignedToMe === v ? ' active' : ''}`} onClick={() => setFAssignedToMe(v)}>{l}</button>
                  ))}
                </div>
              </div>
              <div className="review-control-group">
                <label>Requester</label>
                <div className="filter-chips compact">
                  {[['', 'All'], ['true', 'Mine']].map(([v, l]) => (
                    <button key={v} className={`chip${fRequestedByMe === v ? ' active' : ''}`} onClick={() => setFRequestedByMe(v)}>{l}</button>
                  ))}
                </div>
              </div>
            </div>

            <div className="review-control-group">
              <label>Scene Type</label>
              <select value={fLabel} onChange={e => setFLabel(e.target.value)}>
                <option value="">All Types</option>
                {SCENE_LABELS.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>

            <div className="review-control-group">
              <label>Emotion</label>
              <select value={fEmotion} onChange={e => setFEmotion(e.target.value)}>
                <option value="">All Emotions</option>
                {EMOTIONS.map(e => <option key={e} value={e}>{e === 'null' ? 'None' : e}</option>)}
              </select>
            </div>

            <button className="btn btn-primary review-full-btn" onClick={handleSearchClick}>
              <Search size={14} /> Apply Filters
            </button>
          </section>

          <section className={`review-panel review-action-panel${hasSelection ? '' : ' is-disabled'}`}>
            <div className="review-section-header">
              <div>
                <div className="mono-caps">Selected Clips</div>
                <h3><Settings2 size={16} /> Batch Actions</h3>
              </div>
              <span className={`badge ${hasSelection ? 'info' : ''}`}>{selectedCount}</span>
            </div>

            <div className="review-two-col">
              <div className="review-control-group">
                <label>Status</label>
                <select value={bReviewed} onChange={e => setBReviewed(e.target.value)} disabled={!hasSelection}>
                  <option value="">No Change</option>
                  <option value="true">Mark Reviewed</option>
                  <option value="false">Mark Unreviewed</option>
                </select>
              </div>
              <div className="review-control-group">
                <label>Confidence</label>
                <select value={bUncertain} onChange={e => setBUncertain(e.target.value)} disabled={!hasSelection}>
                  <option value="">No Change</option>
                  <option value="true">Flag Uncertain</option>
                  <option value="false">Remove Flag</option>
                </select>
              </div>
            </div>

            <div className="review-control-group">
              <label>Scene Type</label>
              <select value={bLabel} onChange={e => setBLabel(e.target.value)} disabled={!hasSelection}>
                <option value="">No Change</option>
                {SCENE_LABELS.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>

            <div className="review-control-group">
              <label>Emotion</label>
              <select value={bEmotion} onChange={e => setBEmotion(e.target.value)} disabled={!hasSelection}>
                <option value="">No Change</option>
                {EMOTIONS.map(e => <option key={e} value={e}>{e === 'null' ? 'None' : e}</option>)}
              </select>
            </div>

            <button className="btn btn-primary review-full-btn" onClick={handleBulkUpdate} disabled={!hasSelection || bulkLoading}>
              <Save size={14} /> {bulkLoading ? 'Applying...' : 'Execute Batch'}
            </button>
          </section>

          <section className={`review-panel review-action-panel${hasSelection ? '' : ' is-disabled'}`}>
            <div className="review-section-header">
              <div>
                <div className="mono-caps">Workflow</div>
                <h3><Send size={16} /> Review Requests</h3>
              </div>
            </div>

            {currentUser?.role === 'admin' ? (
              <>
                <div className="review-control-group">
                  <label>Forward To</label>
                  <select value={selectedAssignee} onChange={e => setSelectedAssignee(e.target.value)} disabled={!hasSelection}>
                    <option value="">Choose editor/reviewer...</option>
                    {reviewAssignees.map(user => (
                      <option key={user._id || user.id} value={user._id || user.id}>
                        {user.name || user.username || user.email} ({user.role})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="review-control-group">
                  <label>Note</label>
                  <textarea
                    value={assignmentNote}
                    onChange={e => setAssignmentNote(e.target.value)}
                    maxLength={500}
                    placeholder="Optional note for the reviewer/editor"
                    rows={3}
                    disabled={!hasSelection}
                  />
                </div>
                <button className="btn btn-primary review-full-btn" onClick={handleAssignRequests} disabled={!hasSelection || requestLoading || !selectedAssignee}>
                  <UserPlus size={14} /> {requestLoading ? 'Assigning...' : 'Assign Selected'}
                </button>
                <div className="review-button-row">
                  <button className="btn" onClick={() => handleResolveRequests('resolved')} disabled={!hasSelection || requestLoading}>
                    <ShieldCheck size={14} /> Resolve
                  </button>
                  <button className="btn" onClick={() => handleResolveRequests('dismissed')} disabled={!hasSelection || requestLoading}>
                    <XCircle size={14} /> Dismiss
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="review-control-group">
                  <label>Ask Admin To Review</label>
                  <textarea
                    value={requestReason}
                    onChange={e => setRequestReason(e.target.value)}
                    maxLength={500}
                    placeholder="Why should admin check these clips?"
                    rows={4}
                    disabled={!hasSelection}
                  />
                </div>
                <button className="btn review-full-btn" onClick={handleRequestAdminReview} disabled={!hasSelection || requestLoading || !requestReason.trim()}>
                  <Send size={14} /> {requestLoading ? 'Requesting...' : 'Request Admin Review'}
                </button>
                {currentUser?.role === 'editor' && (
                  <div className="review-subsection">
                    <div className="review-control-group">
                      <label>Ask Editor/Reviewer</label>
                      <select value={selectedPeerAssignee} onChange={e => setSelectedPeerAssignee(e.target.value)} disabled={!hasSelection}>
                        <option value="">Choose editor/reviewer...</option>
                        {reviewAssignees.map(user => (
                          <option key={user._id || user.id} value={user._id || user.id}>
                            {user.name || user.username || user.email} ({user.role})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="review-control-group">
                      <label>Reason</label>
                      <textarea
                        value={peerReason}
                        onChange={e => setPeerReason(e.target.value)}
                        maxLength={500}
                        placeholder="Why should this teammate review these clips?"
                        rows={4}
                        disabled={!hasSelection}
                      />
                    </div>
                    <button className="btn btn-primary review-full-btn" onClick={handleRequestPeerReview} disabled={!hasSelection || requestLoading || !selectedPeerAssignee || !peerReason.trim()}>
                      <UserPlus size={14} /> {requestLoading ? 'Requesting...' : 'Request Peer Review'}
                    </button>
                  </div>
                )}
              </>
            )}
          </section>
        </aside>

        <main className="review-main">
          <div className="review-toolbar">
            <div className="review-toolbar-left">
              <button className="review-select-btn" onClick={toggleAll}>
                {selectedKeys.size === clips.length && clips.length > 0
                  ? <CheckSquareIcon size={18} color="var(--accent)" />
                  : <Square size={18} color="var(--text-secondary)" />
                }
                Select visible
              </button>
              <span className="review-count">{total} clips</span>
              {hasSelection && <span className="badge info">{selectedCount} selected</span>}
            </div>
            <div className="review-pagination">
              <button className="btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft size={16} /> Prev</button>
              <span>Page {page} / {totalPages}</span>
              <button className="btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next <ChevronRight size={16} /></button>
            </div>
          </div>

          <div className="review-grid-scroll">
            {loading ? (
              <LoadingState type="grid" />
            ) : clips.length === 0 ? (
              <EmptyState
                icon={Search}
                title="No Clips Found"
                message="Adjust your filters or reset to browse all clips."
                action={<button className="btn btn-primary" onClick={resetFilters}>Reset Filters</button>}
              />
            ) : (
              <div className="review-clip-grid">
                {clips.map(clip => {
                  const key = `${clip.video}::${clip.scene_id}`;
                  const isSelected = selectedKeys.has(key);
                  const thumb = thumbUrl(clip);
                  const auditTrail = Array.isArray(clip.audit_trail) ? clip.audit_trail : [];
                  const lastAudit = auditTrail[auditTrail.length - 1];
                  return (
                    <button
                      key={key}
                      type="button"
                      className={`review-clip-card stagger-item${isSelected ? ' selected' : ''}`}
                      onClick={() => toggleSelect(key)}
                    >
                      <div className="review-card-media">
                        <span className="review-check" aria-hidden="true">
                          {isSelected ? <CheckSquareIcon size={18} /> : <Square size={18} />}
                        </span>
                        {thumb ? (
                          <img src={thumb} alt={key} className="review-card-thumb" loading="lazy" />
                        ) : (
                          <span className="review-card-thumb empty"><Video size={32} /></span>
                        )}
                      </div>

                      <div className="review-card-body">
                        <div className="review-card-title">{clip.video}</div>
                        <div className="review-card-meta">
                          <span>Scene {clip.scene_id}</span>
                          <span>{clip.duration_sec?.toFixed(1)}s</span>
                        </div>
                        <div className="review-badges">
                          <span className="badge">{clip.scene_label || 'other'}</span>
                          <span className={`badge ${clip.reviewed ? 'success' : 'danger'}`}>{clip.reviewed ? 'Reviewed' : 'Pending'}</span>
                          {clip.uncertain && <span className="badge warning">Uncertain</span>}
                          {clip.review_request_status === 'open' && <span className="badge info">Admin Requested</span>}
                          {clip.review_request_status === 'assigned' && <span className="badge warning">Assigned Review</span>}
                          {clip.review_request_status === 'resolved' && <span className="badge success">Request Resolved</span>}
                        </div>
                        <EmotionTimeline clip={clip} />
                        {(clip.review_request_status === 'open' || clip.review_request_status === 'assigned') && (
                          <div className="review-card-note">
                            {clip.review_request_reason || 'Admin review requested'}
                            {clip.review_request_status === 'assigned' && clip.review_assigned_to_name && (
                              <div>Forwarded to {clip.review_assigned_to_name}</div>
                            )}
                          </div>
                        )}
                        {lastAudit && (
                          <div className="review-audit-line">
                            {formatAuditAction(lastAudit.action)} by {lastAudit.actor?.name || lastAudit.actor?.email || lastAudit.actor?.role || 'system'}
                          </div>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
