import React, { useEffect, useState } from 'react';
import { BarChart3, CheckCircle, AlertCircle, Film, Users, Video, Scissors, CheckSquare, Activity, XOctagon, TrendingUp, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import PageHeader from './components/PageHeader';
import LoadingState from './components/LoadingState';
import api from './lib/api';
import { useToast } from './hooks/useToast.jsx';

const MIN_PER_CLASS = 50;

/* ── Animated counter ── */
function AnimatedNumber({ target }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    if (!target) return;
    let start = 0;
    const step = Math.ceil(target / 30);
    const id = setInterval(() => {
      start = Math.min(start + step, target);
      setDisplay(start);
      if (start >= target) clearInterval(id);
    }, 25);
    return () => clearInterval(id);
  }, [target]);
  return <span className="stat-value-anim">{display.toLocaleString()}</span>;
}

/* ── Bento card with optional accent bar ── */
function BentoCard({ children, span = 1, accent, style = {} }) {
  return (
    <div style={{
      background: 'var(--surface-panel)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-lg)',
      padding: 'var(--space-24)',
      gridColumn: span > 1 ? `span ${span}` : undefined,
      position: 'relative',
      overflow: 'hidden',
      transition: 'border-color 0.2s, box-shadow 0.2s',
      ...style,
    }}
    onMouseEnter={e => { e.currentTarget.style.borderColor = accent || 'var(--border-default)'; e.currentTarget.style.boxShadow = `var(--shadow-hover), 0 0 32px ${accent ? accent + '22' : 'transparent'}`; }}
    onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-subtle)'; e.currentTarget.style.boxShadow = 'none'; }}
    >
      {accent && <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: accent, borderRadius: '2px 2px 0 0' }} />}
      {children}
    </div>
  );
}

function StatLabel({ children }) {
  return <div style={{ fontSize: 'var(--font-meta)', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 'var(--space-4)' }}>{children}</div>;
}
function StatValue({ value, color }) {
  return <div style={{ fontSize: '2.5rem', fontWeight: 700, lineHeight: 1.1, color: color || 'var(--text-primary)', margin: 'var(--space-8) 0' }}>
    <AnimatedNumber target={value || 0} />
  </div>;
}

/* ─────────── ADMIN VIEW ─────────── */
function AdminOverview() {
  const toast = useToast();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/admin/overview')
      .then(res => { setStats(res.data); setLoading(false); })
      .catch(err => { toast.error(err.friendlyMessage || 'Failed to load stats'); setLoading(false); });
  }, []);

  if (loading) return <LoadingState message="Loading system telemetry..." />;

  const hasFailures = (stats?.tasks_failed || 0) > 0;
  const isRunning = (stats?.tasks_running || 0) > 0;

  return (
    <div>
      <PageHeader title="System Dashboard" description="Real-time operational overview of the EditEase platform." />

      {/* ── Bento Grid ── */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 'var(--space-20)',
        marginBottom: 'var(--space-24)'
      }}>

        {/* Wide: Total Clips — primary metric */}
        <BentoCard span={2} accent="var(--accent)">
          <StatLabel><Scissors size={13} style={{verticalAlign:'middle',marginRight:4}} /> Clips Extracted</StatLabel>
          <StatValue value={stats?.total_clips} color="var(--accent)" />
          <div style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 'var(--space-8)' }}>
            <TrendingUp size={14} color="var(--success)" />
            <span>from {stats?.total_videos || 0} source videos</span>
          </div>
        </BentoCard>

        {/* Pending Review */}
        <BentoCard accent="var(--warning)">
          <StatLabel><CheckSquare size={13} style={{verticalAlign:'middle',marginRight:4}} /> Pending Review</StatLabel>
          <StatValue value={stats?.pending_review} color="var(--warning)" />
          {stats?.uncertain_clips > 0 && (
            <div style={{ fontSize: 'var(--font-meta)', color: 'var(--warning)', display: 'flex', gap: 4 }}>
              ⚑ {stats.uncertain_clips} uncertain
            </div>
          )}
        </BentoCard>

        {/* Tasks */}
        <BentoCard accent={hasFailures ? 'var(--danger)' : isRunning ? 'var(--accent)' : 'var(--border-subtle)'}>
          <StatLabel>
            <Activity size={13} style={{verticalAlign:'middle',marginRight:4}} /> Active Tasks
          </StatLabel>
          <StatValue value={stats?.tasks_running} color={isRunning ? 'var(--accent)' : 'var(--text-muted)'} />
          {hasFailures && (
            <div style={{ fontSize: 'var(--font-meta)', color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: 4 }}>
              <XOctagon size={12} /> {stats.tasks_failed} failed
            </div>
          )}
          {isRunning && !hasFailures && <span className="pulse-dot" style={{ marginTop: 4 }} />}
        </BentoCard>

        {/* Users */}
        <BentoCard>
          <StatLabel><Users size={13} style={{verticalAlign:'middle',marginRight:4}} /> Total Users</StatLabel>
          <StatValue value={stats?.total_users} />
          <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-secondary)' }}>{stats?.active_users} active</div>
        </BentoCard>

        {/* Videos */}
        <BentoCard>
          <StatLabel><Video size={13} style={{verticalAlign:'middle',marginRight:4}} /> Videos</StatLabel>
          <StatValue value={stats?.total_videos} />
        </BentoCard>

        {/* Quick Actions — wide */}
        <BentoCard span={2} style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <StatLabel><Clock size={13} style={{verticalAlign:'middle',marginRight:4}} /> Quick Actions</StatLabel>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-12)', marginTop: 'var(--space-16)' }}>
            <Link to="/app/admin/users" className="btn" style={{ flex: 1, minWidth: 120, justifyContent: 'center' }}>Manage Users</Link>
            <Link to="/app/admin/jobs" className="btn" style={{ flex: 1, minWidth: 120, justifyContent: 'center' }}>Job Monitor</Link>
            <Link to="/app/review" className="btn btn-primary" style={{ flex: 1, minWidth: 120, justifyContent: 'center' }}>Review Queue</Link>
          </div>
        </BentoCard>
      </div>
    </div>
  );
}

/* ─────────── EDITOR VIEW ─────────── */
function EditorDashboard() {
  const toast = useToast();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/search?limit=10000')
      .then(res => {
        const results = res.data.results || [];
        const total = results.length;
        const reviewed = results.filter(r => r.reviewed).length;
        const typeCounts = {};
        const reviewedTypeCounts = {};
        results.forEach(r => {
          const t = r.scene_label || 'other';
          typeCounts[t] = (typeCounts[t] || 0) + 1;
          if (r.reviewed) reviewedTypeCounts[t] = (reviewedTypeCounts[t] || 0) + 1;
        });
        const maxCount = Math.max(...Object.values(typeCounts), 1);
        const allClassesReady = Object.values(reviewedTypeCounts).length > 0 &&
          Object.values(reviewedTypeCounts).every(v => v >= MIN_PER_CLASS);
        setStats({ total, reviewed, unreviewed: total - reviewed, typeCounts, reviewedTypeCounts, maxCount, allClassesReady });
        setLoading(false);
      })
      .catch(err => { toast.error(err.friendlyMessage || 'Failed to load stats'); setLoading(false); });
  }, []);

  if (loading) return <LoadingState message="Loading dataset statistics..." />;

  return (
    <div>
      <PageHeader title="Dataset Intelligence" description="Monitor ML readiness and class distributions across your clip library." />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-20)', marginBottom: 'var(--space-24)' }}>
        <BentoCard accent="var(--accent)">
          <StatLabel><Film size={13} style={{verticalAlign:'middle',marginRight:4}} /> Total Clips</StatLabel>
          <StatValue value={stats?.total} />
        </BentoCard>
        <BentoCard accent="var(--success)">
          <StatLabel><CheckCircle size={13} style={{verticalAlign:'middle',marginRight:4}} /> Reviewed</StatLabel>
          <StatValue value={stats?.reviewed} color="var(--success)" />
        </BentoCard>
        <BentoCard accent="var(--danger)">
          <StatLabel><AlertCircle size={13} style={{verticalAlign:'middle',marginRight:4}} /> Unreviewed</StatLabel>
          <StatValue value={stats?.unreviewed} color="var(--danger)" />
        </BentoCard>
      </div>

      <div style={{ background: 'var(--surface-panel)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-24)', marginBottom: 'var(--space-24)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-20)' }}>
          <h2 style={{ margin: 0 }}>Class Distribution</h2>
          {stats?.allClassesReady && <span className="badge success">🎉 ML Ready</span>}
        </div>
        {stats && Object.keys(stats.typeCounts).length > 0 ? (
          Object.entries(stats.typeCounts).sort((a, b) => b[1] - a[1]).map(([label, count]) => {
            const reviewed = stats.reviewedTypeCounts[label] || 0;
            const isReady = reviewed >= MIN_PER_CLASS;
            return (
              <div key={label} style={{ marginBottom: 'var(--space-20)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)' }}>
                  <span style={{ fontWeight: 500, display: 'flex', alignItems: 'center', gap: 'var(--space-8)' }}>
                    {label} {isReady && <CheckCircle size={13} color="var(--success)" />}
                  </span>
                  <span style={{ color: 'var(--text-secondary)' }}>{reviewed}/{count}</span>
                </div>
                <div style={{ width: '100%', height: 10, background: 'var(--surface-base)', borderRadius: 5, overflow: 'hidden', position: 'relative', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ width: `${(count / stats.maxCount) * 100}%`, height: '100%', background: 'rgba(88,166,255,0.25)', position: 'absolute' }} />
                  <div style={{ width: `${(reviewed / stats.maxCount) * 100}%`, height: '100%', background: 'var(--success)', position: 'absolute', transition: 'width 0.5s ease' }} />
                  <div style={{ left: `${Math.min(100, (MIN_PER_CLASS / stats.maxCount) * 100)}%`, position: 'absolute', top: 0, bottom: 0, width: 2, background: 'rgba(218,54,51,0.6)' }} />
                </div>
              </div>
            );
          })
        ) : <p style={{ color: 'var(--text-secondary)' }}>No data. Upload and process videos first.</p>}
      </div>
    </div>
  );
}

export default function Dashboard({ currentUser }) {
  if (currentUser?.role === 'admin') return <AdminOverview />;
  return <EditorDashboard />;
}
