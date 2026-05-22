import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { BarChart3, CheckCircle, AlertCircle, Film, Users, Video, Scissors, CheckSquare, Activity, XOctagon, TrendingUp, Clock, Library, Copy, Upload, RefreshCw, FileVideo } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer, BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Link } from 'react-router-dom';
import PageHeader from './components/PageHeader';
import SystemHealthBanner from './components/SystemHealthBanner';
import { relativeTime } from './hooks/useRelativeTime';
import LoadingState from './components/LoadingState';
import api from './lib/api';
import { useToast } from './hooks/useToast.jsx';


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
function BentoCard({ children, span = 1, accent, to, style = {} }) {
  const content = (
    <>
      {accent && <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: accent, borderRadius: '2px 2px 0 0' }} />}
      {children}
    </>
  );

  const props = {
    className: "bento-card",
    style: {
      background: 'var(--surface-panel)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-lg)',
      padding: 'var(--space-24)',
      gridColumn: span > 1 ? `span ${span}` : undefined,
      position: 'relative',
      overflow: 'hidden',
      transition: 'border-color 0.2s, box-shadow 0.2s',
      cursor: to ? 'pointer' : undefined,
      display: 'block',
      textDecoration: 'none',
      color: 'inherit',
      ...style,
    },
    onMouseEnter: e => { e.currentTarget.style.borderColor = accent || 'var(--border-default)'; e.currentTarget.style.boxShadow = `var(--shadow-hover), 0 0 32px ${accent ? accent + '22' : 'transparent'}`; },
    onMouseLeave: e => { e.currentTarget.style.borderColor = 'var(--border-subtle)'; e.currentTarget.style.boxShadow = 'none'; }
  };

  if (to) {
    return <Link to={to} {...props}>{content}</Link>;
  }
  return <div {...props}>{content}</div>;
}

function StatLabel({ children }) {
  return <div style={{ fontSize: 'var(--font-meta)', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 'var(--space-4)' }}>{children}</div>;
}
function StatValue({ value, color }) {
  return <div style={{
    fontSize: '2.5rem',
    fontWeight: 700,
    lineHeight: 1.1,
    color: color || 'var(--text-primary)',
    margin: 'var(--space-8) 0',
    fontVariantNumeric: 'tabular-nums',
    letterSpacing: '-0.02em',
  }}>
    <AnimatedNumber target={value || 0} />
  </div>;
}

/* ─────────── ADMIN VIEW ─────────── */
function AdminOverview() {
  const toast = useToast();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState(null);
  const containerRef = useRef(null);

  useLayoutEffect(() => {
    if (loading || !containerRef.current) return;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      gsap.from('.bento-card, .activity-feed', {
        y: 24,
        opacity: 0,
        duration: 0.6,
        stagger: 0.05,
        ease: 'power2.out',
      });
    }, containerRef);
    return () => ctx.revert();
  }, [loading]);

  const fetchStats = () => {
    setLoading(true);
    api.get('/admin/overview')
      .then(res => { setStats(res.data); setLastRefreshed(new Date().toISOString()); setLoading(false); })
      .catch(err => { toast.error(err.friendlyMessage || 'Failed to load stats'); setLoading(false); });
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading && !stats) return <LoadingState message="Loading system telemetry..." />;

  const hasFailures = (stats?.tasks_failed || 0) > 0;
  const isRunning = (stats?.tasks_running || 0) > 0;

  // Recharts data conversions
  const COLORS = ['#58a6ff', '#3fb950', '#8957e5', '#d29922', '#f85149', '#cca700', '#2ea043', '#1f6feb'];

  const labelData = stats?.organized_by_label 
    ? Object.entries(stats.organized_by_label)
        .sort((a,b) => b[1] - a[1])
        .map(([name, value]) => ({ 
          name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()), 
          value 
        }))
    : [];

  const clipStatusData = stats ? [
    { name: 'Reviewed & Sorted', value: Math.max(0, stats.total_clips - stats.pending_review - stats.uncertain_clips) },
    { name: 'Pending Review', value: stats.pending_review },
    { name: 'Uncertain Clips', value: stats.uncertain_clips },
  ].filter(d => d.value > 0) : [];

  const activityFeed = [
    ...(stats?.recent_failures || []).map(job => ({
      id: job._id,
      type: 'failure',
      title: `Job Failure: ${job.type}`,
      description: `failed processing ${job.input_path ? job.input_path.split(/[\/\\]/).pop() : 'video'}`,
      timestamp: job.updated_at,
      path: '/app/admin/jobs',
    })),
    ...(stats?.recent_organized_uploads || []).map(upload => ({
      id: upload.id,
      type: 'organized',
      title: upload.display_name || 'Content Changes',
      description: `was organized as ${upload.dominant_label}` + (upload.uploaded_by ? ` by ${upload.uploaded_by}` : ''),
      timestamp: upload.created_at,
      path: '/app/organized-videos',
    })),
  ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  return (
    <div ref={containerRef}>
      <SystemHealthBanner stats={stats} />
      <PageHeader 
        title="Overview" 
        description="System status and real-time activity." 
        actions={
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)' }}>
            <span style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)' }}>
              Updated {relativeTime(lastRefreshed)}
            </span>
            <button className="btn" onClick={fetchStats} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'spin' : ''} /> {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        }
      />

      {/* ── Bento Grid ── */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: 'var(--space-20)',
        marginBottom: 'var(--space-24)'
      }}>

        {/* Wide: Total Clips — primary metric */}
        <BentoCard span={2} accent="var(--accent)" to="/app/organized-videos">
          <StatLabel><Scissors size={13} style={{verticalAlign:'middle',marginRight:4}} /> Clips Extracted</StatLabel>
          <StatValue value={stats?.total_clips} color="var(--accent)" />
          <div style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 'var(--space-8)' }}>
            <TrendingUp size={14} color="var(--success)" />
            <span>from {stats?.total_videos || 0} source videos</span>
          </div>
        </BentoCard>

        {/* Pending Review */}
        <BentoCard accent="var(--warning)" to="/app/review">
          <StatLabel><CheckSquare size={13} style={{verticalAlign:'middle',marginRight:4}} /> Pending Review</StatLabel>
          <StatValue value={stats?.pending_review} color="var(--warning)" />
        </BentoCard>

        {/* Uncertain Clips */}
        <BentoCard accent={stats?.uncertain_clips > 0 ? "var(--danger)" : "var(--border-subtle)"} to="/app/review">
          <StatLabel><AlertCircle size={13} style={{verticalAlign:'middle',marginRight:4}} /> Uncertain Clips</StatLabel>
          <StatValue value={stats?.uncertain_clips} color={stats?.uncertain_clips > 0 ? "var(--danger)" : "var(--text-muted)"} />
          {stats?.uncertain_clips > 0 && <div style={{ fontSize: 'var(--font-meta)', color: 'var(--danger)' }}>Review recommended</div>}
        </BentoCard>

        {/* Tasks */}
        <BentoCard accent={hasFailures ? 'var(--danger)' : isRunning ? 'var(--accent)' : 'var(--border-subtle)'} to="/app/admin/jobs">
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
        <BentoCard to="/app/admin/users">
          <StatLabel><Users size={13} style={{verticalAlign:'middle',marginRight:4}} /> Total Users</StatLabel>
          <StatValue value={stats?.total_users} />
          <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-secondary)' }}>{stats?.active_users} active</div>
        </BentoCard>

        {/* Organized Videos */}
        <BentoCard accent="var(--success)" to="/app/organized-videos">
          <StatLabel><Library size={13} style={{verticalAlign:'middle',marginRight:4}} /> Organized Videos</StatLabel>
          <StatValue value={stats?.total_organized_videos} color="var(--success)" />
          {(stats?.duplicate_videos || 0) > 0 && (
            <div style={{ fontSize: 'var(--font-meta)', color: 'var(--success)' }}>
              + {stats.duplicate_videos} duplicates linked
            </div>
          )}
        </BentoCard>
      </div>

      {/* ── Recent Activity Feed ── */}
      <h2 style={{ margin: 'var(--space-32) 0 var(--space-16)', fontSize: 'var(--font-title-section)' }}>Recent Activity</h2>
      <div className="activity-feed" style={{ 
        background: 'var(--surface-panel)', 
        border: '1px solid var(--border-subtle)', 
        borderRadius: 'var(--radius-lg)', 
        padding: '0 var(--space-20)',
        marginBottom: 'var(--space-32)'
      }}>
        {activityFeed.length === 0 ? (
          <div style={{ padding: 'var(--space-32) 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 'var(--font-small)' }}>
            No recent activity to display.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {activityFeed.map(item => (
               <Link key={item.id} to={item.path} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)', padding: 'var(--space-16) 0', borderBottom: '1px solid var(--border-subtle)', textDecoration: 'none', color: 'inherit' }}>
                 <div style={{ background: item.type === 'failure' ? 'rgba(218, 54, 51, 0.1)' : 'rgba(35, 134, 54, 0.1)', color: item.type === 'failure' ? 'var(--danger)' : 'var(--success)', padding: 8, borderRadius: '50%' }}>
                   {item.type === 'failure' ? <AlertCircle size={16} /> : <FileVideo size={16} />}
                 </div>
                 <div style={{ flex: 1, fontSize: 'var(--font-small)' }}>
                   <span style={{ fontWeight: item.type === 'failure' ? 600 : 500, color: item.type === 'failure' ? 'var(--danger)' : 'var(--text-primary)' }}>{item.title}</span>
                   <span style={{ color: 'var(--text-muted)', marginLeft: item.type === 'failure' ? 4 : 0 }}>{item.description}</span>
                 </div>
                 <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)' }}>{relativeTime(item.timestamp)}</div>
               </Link>
            ))}
            {/* Remove last border */}
            <style>{`.activity-feed > div > a:last-child { border-bottom: none !important; }`}</style>
          </div>
        )}
      </div>

      {/* ── Figurative Charts ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-20)' }}>
        <BentoCard>
          <h3 style={{ margin: '0 0 var(--space-8) 0', fontSize: 'var(--font-title-card)' }}>Review Pipeline Status</h3>
          <p style={{ margin: '0 0 var(--space-16) 0', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)' }}>Distribution of raw clips by human review state.</p>
          {clipStatusData.length > 0 ? (
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={clipStatusData}
                    cx="50%"
                    cy="45%"
                    innerRadius={70}
                    outerRadius={90}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {clipStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.name.includes('Reviewed') ? 'var(--success)' : entry.name.includes('Pending') ? 'var(--warning)' : 'var(--danger)'} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'var(--surface-elevated)', border: '1px solid var(--border-strong)', borderRadius: 8 }}
                    itemStyle={{ color: 'var(--text-primary)' }}
                  />
                  <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: 'var(--font-small)', color: 'var(--text-primary)' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: 'var(--font-small)', padding: 'var(--space-48) 0', textAlign: 'center' }}>No clip data found.</div>
          )}
        </BentoCard>

        <BentoCard>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-8)' }}>
            <h3 style={{ margin: 0, fontSize: 'var(--font-title-card)' }}>Classification Breakdown</h3>
            <Link to="/app/organized-videos" className="btn" style={{ fontSize: 'var(--font-meta)', padding: '4px 10px' }}>Browse</Link>
          </div>
          <p style={{ margin: '0 0 var(--space-16) 0', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)' }}>Total organized assets by AI detected category.</p>
          {labelData.length > 0 ? (
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <RechartsBarChart data={labelData} layout="vertical" margin={{ top: 0, right: 20, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border-subtle)" />
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" width={110} axisLine={false} tickLine={false} tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} />
                  <Tooltip 
                    cursor={{ fill: 'var(--surface-hover)' }}
                    contentStyle={{ backgroundColor: 'var(--surface-elevated)', border: '1px solid var(--border-strong)', borderRadius: 8 }}
                    itemStyle={{ color: 'var(--accent)' }}
                  />
                  <Bar dataKey="value" name="Count" radius={[0, 4, 4, 0]}>
                    {labelData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </RechartsBarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: 'var(--font-small)', padding: 'var(--space-48) 0', textAlign: 'center' }}>No organized footage.</div>
          )}
        </BentoCard>
      </div>

    </div>
  );
}

/* ─────────── EDITOR VIEW ─────────── */
function EditorDashboard({ currentUser }) {
  const toast = useToast();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const containerRef = useRef(null);

  useLayoutEffect(() => {
    if (loading || !containerRef.current) return;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;
    const ctx = gsap.context(() => {
      gsap.from('.bento-card, .editor-banner, .class-dist-row', {
        y: 20, opacity: 0, duration: 0.5, stagger: 0.04, ease: 'power2.out',
      });
    }, containerRef);
    return () => ctx.revert();
  }, [loading]);

  useEffect(() => {
    // Fetch only THIS user's data — both endpoints are server-scoped to the logged-in user
    Promise.all([
      api.get('/organized-videos/stats'),                      // {label: count}  — organized only
      api.get('/organized-videos?limit=1'),                    // total of all statuses
      api.get('/organized-videos?is_duplicate=true&limit=1'),  // duplicate count
    ])
      .then(([statsRes, totalRes, dupRes]) => {
        const labelCounts = statsRes.data || {};
        const organizedCount = Object.values(labelCounts).reduce((a, b) => a + b, 0);
        const duplicateCount = dupRes.data.total || 0;
        const total = totalRes.data.total || 0;
        const maxCount = Math.max(...Object.values(labelCounts), 1);
        setStats({ total, organized: organizedCount, duplicates: duplicateCount, labelCounts, maxCount });
        setLoading(false);
      })
      .catch(err => { toast.error(err.friendlyMessage || 'Failed to load your stats'); setLoading(false); });
  }, []);

  if (loading) return <LoadingState message="Loading your workspace..." />;

  const hasVideos = stats && stats.total > 0;
  const firstName = currentUser?.name?.split(' ')[0] || 'there';

  return (
    <div ref={containerRef}>
      <PageHeader
        title={`Welcome back, ${firstName}`}
        description="Your personal video library — organised, categorised, and ready to explore."
      />

      {/* ── Duplicate notice banner ── */}
      {stats && stats.duplicates > 0 && (
        <div className="editor-banner" style={{
          background: 'var(--surface-elevated)',
          border: '1px solid var(--border-strong)',
          borderLeft: '3px solid var(--warning)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-20) var(--space-24)',
          marginBottom: 'var(--space-24)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          gap: 'var(--space-16)', flexWrap: 'wrap',
        }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 'var(--font-title-card)', marginBottom: 4 }}>
              {stats.duplicates} duplicate{stats.duplicates !== 1 ? 's' : ''} detected
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-small)' }}>
              These files were already uploaded. They're linked to the originals so you won't lose anything.
            </div>
          </div>
          <Link to="/app/organized-videos" className="btn" style={{ whiteSpace: 'nowrap' }}>View Library →</Link>
        </div>
      )}

      {/* ── Stat cards ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-20)', marginBottom: 'var(--space-24)' }}>
        <BentoCard accent="var(--accent)">
          <StatLabel><Upload size={13} style={{verticalAlign:'middle',marginRight:4}} /> Total Uploaded</StatLabel>
          <StatValue value={stats?.total} />
          <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)' }}>videos in your library</div>
        </BentoCard>
        <BentoCard accent="var(--success)">
          <StatLabel><CheckCircle size={13} style={{verticalAlign:'middle',marginRight:4}} /> Organised</StatLabel>
          <StatValue value={stats?.organized} color="var(--success)" />
          <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)' }}>successfully classified</div>
        </BentoCard>
        <BentoCard accent="var(--warning)">
          <StatLabel><Copy size={13} style={{verticalAlign:'middle',marginRight:4}} /> Duplicates</StatLabel>
          <StatValue value={stats?.duplicates} color="var(--warning)" />
          <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)' }}>linked to originals</div>
        </BentoCard>
      </div>

      {/* ── Your category breakdown ── */}
      <div style={{ background: 'var(--surface-panel)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-24)', marginBottom: 'var(--space-24)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-20)' }}>
          <h2 style={{ margin: 0 }}>Your Categories</h2>
          <Link to="/app/organized-videos" className="btn" style={{ fontSize: 'var(--font-meta)', padding: '4px 10px' }}>Browse →</Link>
        </div>

        {hasVideos && stats && Object.keys(stats.labelCounts).length > 0 ? (
          Object.entries(stats.labelCounts).sort((a, b) => b[1] - a[1]).map(([label, count]) => {
            const displayLabel = label.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            return (
              <div key={label} className="class-dist-row" style={{ marginBottom: 'var(--space-20)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-8)', fontSize: 'var(--font-small)' }}>
                  <span style={{ fontWeight: 500 }}>{displayLabel}</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{count} video{count !== 1 ? 's' : ''}</span>
                </div>
                <div style={{ width: '100%', height: 8, background: 'var(--surface-base)', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                  <div style={{
                    width: `${(count / stats.maxCount) * 100}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, var(--accent), rgba(88,166,255,0.6))',
                    borderRadius: 4,
                    transition: 'width 0.6s ease',
                  }} />
                </div>
              </div>
            );
          })
        ) : (
          <div style={{ textAlign: 'center', padding: 'var(--space-64) var(--space-24)' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-16)' }}>📂</div>
            <div style={{ fontWeight: 600, fontSize: 'var(--font-title-card)', marginBottom: 'var(--space-8)' }}>No footage yet</div>
            <div style={{ color: 'var(--text-secondary)', maxWidth: 360, margin: '0 auto var(--space-24)' }}>
              Upload your first video and let the AI organise it into categories automatically.
            </div>
            <Link to="/app/uploads" className="btn btn-primary">Upload Footage</Link>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Dashboard({ currentUser }) {
  if (currentUser?.role === 'admin') return <AdminOverview />;
  return <EditorDashboard currentUser={currentUser} />;
}
