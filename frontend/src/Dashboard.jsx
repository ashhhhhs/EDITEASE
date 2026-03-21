import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BarChart3, CheckCircle, AlertCircle, Film, Users, Video, Scissors, CheckSquare, Activity, XOctagon } from 'lucide-react';
import { API_BASE } from './config';
import { Link } from 'react-router-dom';
import PageHeader from './components/PageHeader';
import ContentSection from './components/ContentSection';
import LoadingState from './components/LoadingState';

const MIN_PER_CLASS = 50;

function AdminOverview() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        axios.get(`${API_BASE}/admin/overview`)
            .then(res => {
                setStats(res.data);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setLoading(false);
            });
    }, []);

    if (loading) return <LoadingState message="Loading system telemetry..." />;

    return (
        <div>
            <PageHeader 
              title="System Dashboard" 
              description="Real-time operational overview of the EditEase platform." 
            />

            <ContentSection>
                <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', marginBottom: 0 }}>
                    <div className="stat-card">
                        <Users size={24} color="var(--accent)" style={{marginBottom: 'var(--space-8)'}} />
                        <div className="value">{stats?.total_users || 0}</div>
                        <div className="label">Total Users</div>
                        <div style={{fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginTop: 'var(--space-8)'}}>
                            {stats?.active_users || 0} active
                        </div>
                    </div>
                    <div className="stat-card">
                        <Video size={24} color="#a371f7" style={{marginBottom: 'var(--space-8)'}} />
                        <div className="value">{stats?.total_videos || 0}</div>
                        <div className="label">Videos Processed</div>
                    </div>
                    <div className="stat-card">
                        <Scissors size={24} color="var(--accent)" style={{marginBottom: 'var(--space-8)'}} />
                        <div className="value">{stats?.total_clips || 0}</div>
                        <div className="label">Clips Extracted</div>
                    </div>
                    <div className="stat-card">
                        <CheckSquare size={24} color="var(--success)" style={{marginBottom: 'var(--space-8)'}} />
                        <div className="value">{stats?.pending_review || 0}</div>
                        <div className="label">Pending Review</div>
                        {stats?.uncertain_clips > 0 && <div style={{fontSize: 'var(--font-meta)', color: 'var(--warning)', marginTop: 'var(--space-8)'}}>{stats?.uncertain_clips} flagged uncertain</div>}
                    </div>
                    <div className="stat-card" style={{ borderColor: stats?.tasks_failed > 0 ? 'var(--danger)' : 'var(--border-subtle)' }}>
                        <Activity size={24} color={stats?.tasks_running > 0 ? "var(--accent)" : "var(--text-secondary)"} style={{marginBottom: 'var(--space-8)'}} />
                        <div className="value">{stats?.tasks_running || 0}</div>
                        <div className="label">Tasks Running</div>
                        {stats?.tasks_failed > 0 && <div style={{fontSize: 'var(--font-meta)', color: 'var(--danger)', marginTop: 'var(--space-8)'}}><XOctagon size={12} style={{verticalAlign: 'middle'}}/> {stats?.tasks_failed} failed</div>}
                    </div>
                </div>
            </ContentSection>

            <ContentSection title="Quick Actions">
                <div style={{display: 'flex', gap: 'var(--space-16)', flexWrap: 'wrap'}}>
                    <Link to="/app/admin/users" className="styled-button secondary">Manage Users</Link>
                    <Link to="/app/admin/jobs" className="styled-button secondary">System Job Monitor</Link>
                    <Link to="/app/review" className="btn btn-primary">Access Review Queue</Link>
                </div>
            </ContentSection>
        </div>
    );
}

function EditorDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API_BASE}/search?limit=10000`)
      .then(res => {
        const results = res.data.results || [];
        const total = results.length;
        const reviewed = results.filter(r => r.reviewed).length;
        const unreviewed = total - reviewed;
        
        const typeCounts = {};
        const reviewedTypeCounts = {};
        results.forEach(r => {
          const t = r.scene_label || 'other';
          typeCounts[t] = (typeCounts[t] || 0) + 1;
          if (r.reviewed) {
            reviewedTypeCounts[t] = (reviewedTypeCounts[t] || 0) + 1;
          }
        });

        const maxCount = Math.max(...Object.values(typeCounts), 1);
        const allClassesReady = Object.values(reviewedTypeCounts).length > 0 && 
          Object.values(reviewedTypeCounts).every(v => v >= MIN_PER_CLASS);

        setStats({ total, reviewed, unreviewed, typeCounts, reviewedTypeCounts, maxCount, allClassesReady });
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <LoadingState message="Loading dataset statistics..." />;

  return (
    <div>
      <PageHeader 
        title="Dataset Intelligence" 
        description="Monitor machine learning readiness and class distributions across all extracted clips." 
      />
      
      <ContentSection>
        <div className="stat-grid" style={{ marginBottom: 0 }}>
            <div className="stat-card">
            <Film size={24} color="var(--accent)" style={{marginBottom: 'var(--space-8)'}} />
            <div className="value">{stats?.total || 0}</div>
            <div className="label">Total Clips</div>
            </div>
            <div className="stat-card">
            <CheckCircle size={24} color="var(--success)" style={{marginBottom: 'var(--space-8)'}} />
            <div className="value" style={{color: 'var(--success)'}}>{stats?.reviewed || 0}</div>
            <div className="label">Reviewed</div>
            </div>
            <div className="stat-card">
            <AlertCircle size={24} color="var(--danger)" style={{marginBottom: 'var(--space-8)'}} />
            <div className="value" style={{color: 'var(--danger)'}}>{stats?.unreviewed || 0}</div>
            <div className="label">Unreviewed</div>
            </div>
        </div>
      </ContentSection>

      <ContentSection title="ML Training Readiness" className="panel" style={{ borderColor: stats?.allClassesReady ? 'var(--success)' : 'var(--border-subtle)' }}>
        {stats?.allClassesReady ? (
          <p style={{color: 'var(--success)', margin: 0}}>🎉 All classes have {MIN_PER_CLASS}+ reviewed samples. You're ready to train a model!</p>
        ) : (
          <p style={{color: 'var(--text-secondary)', margin: 0}}>
            Each class needs at least <strong>{MIN_PER_CLASS}</strong> reviewed clips before training. 
            Use the Review Queue to tag more clips.
          </p>
        )}
      </ContentSection>

      <ContentSection title="Class Distribution">
        <div style={{display: 'flex', gap: 'var(--space-32)', color: 'var(--text-secondary)', fontSize: 'var(--font-meta)', marginBottom: 'var(--space-24)'}}>
          <span style={{display: 'flex', alignItems: 'center', gap: 'var(--space-8)'}}>
            <span style={{width: 12, height: 12, background: 'var(--accent)', borderRadius: 'var(--radius-sm)', display: 'inline-block'}}></span> Total
          </span>
          <span style={{display: 'flex', alignItems: 'center', gap: 'var(--space-8)'}}>
            <span style={{width: 12, height: 12, background: 'var(--success)', borderRadius: 'var(--radius-sm)', display: 'inline-block'}}></span> Reviewed
          </span>
          <span style={{display: 'flex', alignItems: 'center', gap: 'var(--space-8)'}}>
            <span style={{width: 12, height: 12, background: 'rgba(218, 54, 51, 0.4)', borderRadius: 'var(--radius-sm)', display: 'inline-block'}}></span> Min needed ({MIN_PER_CLASS})
          </span>
        </div>

        {stats && Object.keys(stats.typeCounts).length > 0 ? (
          <div>
            {Object.entries(stats.typeCounts)
              .sort((a,b) => b[1] - a[1])
              .map(([label, count]) => {
                const reviewedCount = stats.reviewedTypeCounts[label] || 0;
                const isReady = reviewedCount >= MIN_PER_CLASS;
                return (
                  <div key={label} style={{marginBottom: 'var(--space-20)'}}>
                    <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-8)'}}>
                      <span style={{fontWeight: '500', display: 'flex', alignItems: 'center', gap: 'var(--space-8)', fontSize: 'var(--font-small)'}}>
                        {label}
                        {isReady && <CheckCircle size={14} color="var(--success)" />}
                      </span>
                      <span style={{color: 'var(--text-secondary)', fontSize: 'var(--font-meta)'}}>
                        {reviewedCount} reviewed / {count} total
                      </span>
                    </div>
                    {/* Stacked bar */}
                    <div style={{width: '100%', height: '14px', background: 'var(--surface-base)', borderRadius: '7px', overflow: 'hidden', position: 'relative', border: '1px solid var(--border-subtle)'}}>
                      <div style={{ width: `${(count / stats.maxCount) * 100}%`, height: '100%', background: 'rgba(88, 166, 255, 0.3)', position: 'absolute' }}></div>
                      <div style={{ width: `${(reviewedCount / stats.maxCount) * 100}%`, height: '100%', background: 'var(--success)', position: 'absolute' }}></div>
                      <div style={{ left: `${Math.min(100, (MIN_PER_CLASS / stats.maxCount) * 100)}%`, position: 'absolute', top: 0, bottom: 0, width: '2px', background: 'rgba(218, 54, 51, 0.6)' }}></div>
                    </div>
                  </div>
                );
              })}
          </div>
        ) : (
          <p style={{color: 'var(--text-secondary)'}}>No data available. Upload and process videos first.</p>
        )}
      </ContentSection>
    </div>
  );
}

export default function Dashboard({ currentUser }) {
    if (currentUser?.role === 'admin') {
        return <AdminOverview />;
    }
    return <EditorDashboard />;
}
