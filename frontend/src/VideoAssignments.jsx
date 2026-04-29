import React, { useState, useEffect, useCallback } from 'react';
import { Film, RefreshCw, Search, UserX, UserCheck } from 'lucide-react';
import PageHeader from './components/PageHeader';
import ContentSection from './components/ContentSection';
import LoadingState from './components/LoadingState';
import EmptyState from './components/EmptyState';
import { useToast } from './hooks/useToast.jsx';
import api from './lib/api';

/* ── Progress Bar ─────────────────────────────────────────── */
function ProgressBar({ reviewed, total }) {
  const pct = total > 0 ? Math.round((reviewed / total) * 100) : 0;
  const color =
    pct === 100 ? 'var(--success)' : pct > 50 ? 'var(--accent)' : 'var(--warning)';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)' }}>
      <div
        style={{
          flex: 1,
          height: 6,
          background: 'var(--surface-elevated)',
          borderRadius: 99,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            background: color,
            borderRadius: 99,
            transition: 'width 0.35s ease',
          }}
        />
      </div>
      <span
        style={{
          fontSize: 'var(--font-meta)',
          color: 'var(--text-secondary)',
          minWidth: 52,
          textAlign: 'right',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {reviewed}/{total}
      </span>
    </div>
  );
}

/* ── Stat Card ────────────────────────────────────────────── */
function StatCard({ label, value, color }) {
  return (
    <div
      className="panel"
      style={{ padding: 'var(--space-20)', display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}
    >
      <span
        style={{
          fontSize: 'var(--font-meta)',
          color: 'var(--text-secondary)',
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
        }}
      >
        {label}
      </span>
      <span style={{ fontSize: '2rem', fontWeight: 700, color, lineHeight: 1 }}>
        {value}
      </span>
    </div>
  );
}

/* ── Main Component ───────────────────────────────────────── */
export default function VideoAssignments() {
  const toast = useToast();
  const [assignments, setAssignments] = useState([]);
  const [editors, setEditors] = useState([]);   // editors + reviewers
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [saving, setSaving] = useState({});      // { [video]: true } while request in-flight

  /* ── Fetch ── */
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [assignRes, editorsRes, reviewersRes] = await Promise.all([
        api.get('/admin/assignments'),
        api.get('/admin/users?limit=200&role=editor'),
        api.get('/admin/users?limit=200&role=reviewer'),
      ]);
      setAssignments(assignRes.data);
      setEditors([
        ...(editorsRes.data.users || []),
        ...(reviewersRes.data.users || []),
      ]);
    } catch (err) {
      toast.error(err.friendlyMessage || 'Failed to load assignments');
    } finally {
      setLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { fetchData(); }, [fetchData]);

  /* ── Assign / Unassign ── */
  const handleAssign = async (video, userId) => {
    setSaving(prev => ({ ...prev, [video]: true }));
    try {
      await api.post('/admin/assignments/assign', { video, user_id: userId || null });
      setAssignments(prev =>
        prev.map(a => a.video === video ? { ...a, assigned_to: userId || null } : a)
      );
      toast.success(userId ? 'Editor assigned' : 'Assignment removed');
    } catch (err) {
      toast.error(err.friendlyMessage || 'Failed to update assignment');
    } finally {
      setSaving(prev => ({ ...prev, [video]: false }));
    }
  };

  /* ── Derived ── */
  const filtered = assignments.filter(a =>
    !search || a.video.toLowerCase().includes(search.toLowerCase())
  );
  const totalAssigned  = assignments.filter(a => a.assigned_to).length;
  const totalComplete  = assignments.filter(
    a => a.total_clips > 0 && a.reviewed_clips === a.total_clips
  ).length;

  /* ── Helpers ── */
  const getUserLabel = (userId) => {
    if (!userId) return null;
    const u = editors.find(e => (e._id || String(e.id)) === userId);
    if (!u) return null;
    return u.name || u.username || u.email;
  };

  return (
    <div>
      <PageHeader
        title="Video Assignments"
        description="Assign editors or reviewers to videos and track clip review progress."
        actions={
          <button className="btn" onClick={fetchData} disabled={loading}>
            <RefreshCw size={16} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
        }
      />

      {/* ── Stats ── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 'var(--space-16)',
          marginBottom: 'var(--space-24)',
        }}
      >
        <StatCard label="Total Videos"   value={assignments.length} color="var(--accent)"   />
        <StatCard label="Assigned"        value={totalAssigned}      color="var(--warning)"  />
        <StatCard label="Fully Reviewed"  value={totalComplete}      color="var(--success)"  />
      </div>

      {/* ── Table ── */}
      <ContentSection style={{ padding: 0, overflow: 'hidden' }}>
        {/* Toolbar */}
        <div
          style={{
            padding: 'var(--space-16) var(--space-24)',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-12)',
          }}
        >
          <div className="input-group" style={{ flex: 1, position: 'relative', margin: 0 }}>
            <Search
              size={16}
              color="var(--text-muted)"
              style={{ position: 'absolute', left: 12, top: 10, pointerEvents: 'none' }}
            />
            <input
              type="search"
              placeholder="Search videos..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ paddingLeft: 36 }}
            />
          </div>
          <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
            {filtered.length} video{filtered.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Body */}
        {loading ? (
          <LoadingState type="table" />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={Film}
            title="No Videos Found"
            message={search ? 'No videos match your search.' : 'No processed videos available yet.'}
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Video</th>
                  <th style={{ width: 230 }}>Review Progress</th>
                  <th style={{ width: 110, textAlign: 'center' }}>Status</th>
                  <th style={{ width: 260 }}>Assigned To</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(a => {
                  const pct       = a.total_clips > 0 ? Math.round((a.reviewed_clips / a.total_clips) * 100) : 0;
                  const isComplete = pct === 100 && a.total_clips > 0;
                  const inProgress = a.reviewed_clips > 0 && !isComplete;
                  const assignedName = getUserLabel(a.assigned_to);

                  return (
                    <tr key={a.video}>
                      {/* Video name */}
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-10)' }}>
                          <div
                            style={{
                              width: 32,
                              height: 32,
                              borderRadius: 'var(--radius-sm)',
                              background: 'var(--surface-elevated)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              flexShrink: 0,
                            }}
                          >
                            <Film size={14} color="var(--text-muted)" />
                          </div>
                          <div>
                            <div style={{ fontWeight: 600, fontSize: 'var(--font-small)' }}>
                              {a.video}
                            </div>
                            <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-secondary)' }}>
                              {a.total_clips} clip{a.total_clips !== 1 ? 's' : ''}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Progress bar */}
                      <td>
                        <ProgressBar reviewed={a.reviewed_clips} total={a.total_clips} />
                      </td>

                      {/* Status badge */}
                      <td style={{ textAlign: 'center' }}>
                        {isComplete ? (
                          <span className="badge success">Done</span>
                        ) : inProgress ? (
                          <span className="badge warning">In Progress</span>
                        ) : (
                          <span
                            className="badge"
                            style={{ background: 'var(--surface-elevated)', color: 'var(--text-muted)' }}
                          >
                            Pending
                          </span>
                        )}
                      </td>

                      {/* Assign dropdown */}
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)' }}>
                          <select
                            id={`assign-${a.video}`}
                            value={a.assigned_to || ''}
                            onChange={e => handleAssign(a.video, e.target.value || null)}
                            disabled={saving[a.video]}
                            style={{
                              flex: 1,
                              opacity: saving[a.video] ? 0.6 : 1,
                              transition: 'opacity 0.2s',
                            }}
                          >
                            <option value="">— Unassigned —</option>
                            {editors.map(u => (
                              <option key={u._id || u.id} value={u._id || u.id}>
                                {u.name || u.username || u.email} ({u.role})
                              </option>
                            ))}
                          </select>

                          {/* Unassign button — visible when assigned */}
                          {a.assigned_to && (
                            <button
                              onClick={() => handleAssign(a.video, null)}
                              disabled={saving[a.video]}
                              title={`Remove assignment from ${assignedName}`}
                              aria-label="Remove assignment"
                              style={{
                                padding: 'var(--space-8)',
                                border: 'none',
                                borderRadius: 'var(--radius-sm)',
                                cursor: 'pointer',
                                background: 'rgba(218, 54, 51, 0.1)',
                                color: 'var(--danger)',
                                flexShrink: 0,
                                transition: 'background 0.2s',
                              }}
                            >
                              <UserX size={14} />
                            </button>
                          )}

                          {/* Confirmed-assigned indicator */}
                          {a.assigned_to && assignedName && (
                            <UserCheck size={14} color="var(--success)" style={{ flexShrink: 0 }} />
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </ContentSection>
    </div>
  );
}
