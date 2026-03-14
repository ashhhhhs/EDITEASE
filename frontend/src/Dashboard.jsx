import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BarChart3, CheckCircle, AlertCircle, Film } from 'lucide-react';
import { API_BASE } from './config';

const MIN_PER_CLASS = 50;

export default function Dashboard() {
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

  if (loading) return (
    <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', height: '50vh', color: 'var(--text-muted)'}}>
      Loading dataset statistics...
    </div>
  );

  return (
    <div>
      <h2>Dashboard</h2>
      
      {/* Stat Cards */}
      <div className="stat-grid">
        <div className="stat-card">
          <Film size={24} color="var(--accent)" style={{marginBottom: '0.5rem'}} />
          <div className="value">{stats?.total || 0}</div>
          <div className="label">Total Clips</div>
        </div>
        <div className="stat-card">
          <CheckCircle size={24} color="var(--success)" style={{marginBottom: '0.5rem'}} />
          <div className="value" style={{color: 'var(--success)'}}>{stats?.reviewed || 0}</div>
          <div className="label">Reviewed</div>
        </div>
        <div className="stat-card">
          <AlertCircle size={24} color="var(--danger)" style={{marginBottom: '0.5rem'}} />
          <div className="value" style={{color: 'var(--danger)'}}>{stats?.unreviewed || 0}</div>
          <div className="label">Unreviewed</div>
        </div>
      </div>

      {/* ML Readiness Alert */}
      <div className="panel" style={{marginBottom: '2rem', borderColor: stats?.allClassesReady ? 'var(--success)' : 'var(--border-color)'}}>
        <h3 style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
          <BarChart3 size={20} /> ML Training Readiness
        </h3>
        {stats?.allClassesReady ? (
          <p style={{color: 'var(--success)'}}>🎉 All classes have 50+ reviewed samples. You're ready to train a model!</p>
        ) : (
          <p style={{color: 'var(--text-muted)'}}>
            Each class needs at least <strong>{MIN_PER_CLASS}</strong> reviewed clips before training. 
            Use the Inspector to review and label more clips.
          </p>
        )}
      </div>

      {/* Class Distribution */}
      <div className="panel">
        <h3>Class Distribution</h3>
        <div style={{display: 'flex', gap: '2rem', color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '1.5rem'}}>
          <span style={{display: 'flex', alignItems: 'center', gap: '0.4rem'}}>
            <span style={{width: 12, height: 12, background: 'var(--accent)', borderRadius: 2, display: 'inline-block'}}></span>
            Total
          </span>
          <span style={{display: 'flex', alignItems: 'center', gap: '0.4rem'}}>
            <span style={{width: 12, height: 12, background: 'var(--success)', borderRadius: 2, display: 'inline-block'}}></span>
            Reviewed
          </span>
          <span style={{display: 'flex', alignItems: 'center', gap: '0.4rem'}}>
            <span style={{width: 12, height: 12, background: 'rgba(218, 54, 51, 0.4)', borderRadius: 2, display: 'inline-block'}}></span>
            Min needed ({MIN_PER_CLASS})
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
                  <div key={label} style={{marginBottom: '1.25rem'}}>
                    <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem'}}>
                      <span style={{fontWeight: '500', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                        {label}
                        {isReady && <CheckCircle size={14} color="var(--success)" />}
                      </span>
                      <span style={{color: 'var(--text-muted)', fontSize: '0.85rem'}}>
                        {reviewedCount} reviewed / {count} total
                      </span>
                    </div>
                    {/* Stacked bar */}
                    <div style={{width: '100%', height: '14px', background: 'var(--border-color)', borderRadius: '7px', overflow: 'hidden', position: 'relative'}}>
                      {/* Total bar */}
                      <div style={{
                        width: `${(count / stats.maxCount) * 100}%`, 
                        height: '100%', 
                        background: 'rgba(88, 166, 255, 0.3)',
                        position: 'absolute',
                        transition: 'width 0.6s ease'
                      }}></div>
                      {/* Reviewed bar */}
                      <div style={{
                        width: `${(reviewedCount / stats.maxCount) * 100}%`, 
                        height: '100%', 
                        background: 'var(--success)',
                        position: 'absolute',
                        transition: 'width 0.6s ease'
                      }}></div>
                      {/* Threshold marker */}
                      <div style={{
                        left: `${Math.min(100, (MIN_PER_CLASS / stats.maxCount) * 100)}%`,
                        position: 'absolute',
                        top: 0, bottom: 0,
                        width: '2px',
                        background: 'rgba(218, 54, 51, 0.6)'
                      }}></div>
                    </div>
                  </div>
                );
              })}
          </div>
        ) : (
          <p style={{color: 'var(--text-muted)'}}>No data available. Upload and process videos first.</p>
        )}
      </div>
    </div>
  );
}
