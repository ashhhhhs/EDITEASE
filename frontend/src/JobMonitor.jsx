import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE } from './config';
import { Activity, XCircle, CheckCircle2, Loader2, ChevronLeft, ChevronRight, FileVideo } from 'lucide-react';
import PageHeader from './components/PageHeader';
import ContentSection from './components/ContentSection';
import LoadingState from './components/LoadingState';
import EmptyState from './components/EmptyState';

export default function JobMonitor() {
  const [jobs, setJobs] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 15;
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const fetchJobs = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/admin/jobs?page=${page}&limit=${limit}`;
      if (filterType) url += `&type=${filterType}`;
      if (filterStatus) url += `&status=${filterStatus}`;
      const res = await axios.get(url);
      setJobs(res.data.jobs || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(() => {
        if (jobs.some(j => j.status === 'PENDING' || j.status === 'STARTED')) {
            fetchJobs();
        }
    }, 5000);
    return () => clearInterval(interval);
  }, [page, filterType, filterStatus, jobs]);

  const totalPages = Math.ceil(total / limit);

  const StatusIcon = ({ status }) => {
      switch (status) {
          case 'SUCCESS': return <CheckCircle2 size={16} color="var(--success)" />;
          case 'FAILURE': return <XCircle size={16} color="var(--danger)" />;
          case 'STARTED':
          case 'PENDING': return <Loader2 size={16} color="var(--accent)" className="spin" />;
          default: return <Activity size={16} />;
      }
  };

  return (
    <div>
      <PageHeader 
        title="Job Monitor" 
        description="Real-time Celery task tracking for server-side processing workflows." 
        actions={
            <div style={{ display: 'flex', gap: 'var(--space-12)' }}>
                <select className="styled-input" value={filterType} onChange={e => {setFilterType(e.target.value); setPage(1);}} style={{ width: 'auto' }}>
                    <option value="">All Types</option>
                    <option value="upload">Upload</option>
                    <option value="auto_organize">Auto-Organize</option>
                </select>
                <select className="styled-input" value={filterStatus} onChange={e => {setFilterStatus(e.target.value); setPage(1);}} style={{ width: 'auto' }}>
                    <option value="">All Statuses</option>
                    <option value="PENDING">PENDING</option>
                    <option value="STARTED">STARTED</option>
                    <option value="SUCCESS">SUCCESS</option>
                    <option value="FAILURE">FAILURE</option>
                </select>
            </div>
        }
      />

      <ContentSection style={{ padding: 0, overflow: 'hidden' }}>
        {loading && jobs.length === 0 ? (
          <LoadingState type="table" />
        ) : jobs.length === 0 ? (
          <EmptyState icon={Activity} title="No Jobs Found" message="No tasks match your current filter criteria." />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Task ID</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Path / Output</th>
                  <th>Timing</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map(j => (
                  <tr key={j._id}>
                    <td style={{ fontFamily: 'monospace', fontSize: 'var(--font-meta)' }}>
                      {j.task_id.split('-')[0]}...
                    </td>
                    <td>
                      <span className="badge" style={{ background: 'var(--surface-base)' }}>{j.type}</span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', fontWeight: '600', color: j.status === 'FAILURE' ? 'var(--danger)' : j.status === 'SUCCESS' ? 'var(--success)' : 'var(--text-primary)' }}>
                          <StatusIcon status={j.status} /> {j.status}
                      </div>
                      {j.progress_step && (
                          <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)', marginTop: 'var(--space-4)', textTransform: 'uppercase' }}>
                              Step: {j.progress_step}
                          </div>
                      )}
                    </td>
                    <td style={{ maxWidth: '300px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                          {j.input_path && <span title={j.input_path} style={{ color: 'var(--text-secondary)' }}><FileVideo size={12} style={{verticalAlign: 'middle', marginRight: 'var(--space-4)'}}/> {j.input_path.split(/[\/\\]/).pop()}</span>}
                          {j.output_path && <span style={{ color: 'var(--success)' }}>Output: {j.output_path.split(/[\/\\]/).pop()}</span>}
                          {j.error_message && <span style={{ color: 'var(--danger)', padding: 'var(--space-4) var(--space-8)', background: 'rgba(218, 54, 51, 0.1)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(218,54,51,0.2)' }}>{j.error_message}</span>}
                      </div>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>
                      {new Date(j.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {jobs.length > 0 && (
          <div style={{ padding: 'var(--space-16) var(--space-24)', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>Showing {jobs.length} of {total} results</span>
            <div style={{ display: 'flex', gap: 'var(--space-8)', alignItems: 'center' }}>
              <button className="btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft size={16} /> Prev</button>
              <button className="btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next <ChevronRight size={16} /></button>
            </div>
          </div>
        )}
      </ContentSection>
    </div>
  );
}
