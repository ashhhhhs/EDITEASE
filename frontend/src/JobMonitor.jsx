import React, { useState, useEffect, useRef } from 'react';
import { Activity, XCircle, CheckCircle2, Loader2, ChevronLeft, ChevronRight, FileVideo, Copy, RefreshCw, XSquare, PlayCircle, UserRound } from 'lucide-react';
import PageHeader from './components/PageHeader';
import ContentSection from './components/ContentSection';
import LoadingState from './components/LoadingState';
import EmptyState from './components/EmptyState';
import ConfirmationModal from './components/ConfirmationModal';
import api from './lib/api';
import { useToast } from './hooks/useToast.jsx';

export default function JobMonitor() {
  const toast = useToast();
  const [jobs, setJobs] = useState([]);
  const [summary, setSummary] = useState({ running: 0, succeeded: 0, failed: 0 });
  const jobsRef = useRef([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 15;
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const [confirmModal, setConfirmModal] = useState({ isOpen: false, type: null, taskId: null });
  const [errorModal, setErrorModal] = useState({ isOpen: false, message: '' });

  const fetchJobs = async () => {
    try {
      let url = `/admin/jobs?page=${page}&limit=${limit}`;
      if (filterType) url += `&type=${filterType}`;
      if (filterStatus) url += `&status=${filterStatus}`;
      const res = await api.get(url);
      setJobs(res.data.jobs || []);
      jobsRef.current = res.data.jobs || [];
      setTotal(res.data.total || 0);
      if (res.data.summary) setSummary(res.data.summary);
    } catch (err) {
      toast.error(err.friendlyMessage || 'Failed to load jobs');
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchJobs().finally(() => setLoading(false));
  }, [page, filterType, filterStatus]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (jobsRef.current.some(j => j.status === 'PENDING' || j.status === 'STARTED')) {
        fetchJobs();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [page, filterType, filterStatus]);

  const copyTaskId = (id) => {
    navigator.clipboard.writeText(id);
    toast.success('Task ID copied');
  };

  const executeAction = async () => {
    const { type, taskId } = confirmModal;
    setConfirmModal({ isOpen: false, type: null, taskId: null });
    try {
      if (type === 'cancel') {
        await api.delete(`/admin/jobs/${taskId}`);
        toast.success('Job cancelled');
      } else if (type === 'retry') {
        await api.post(`/admin/jobs/${taskId}/retry`);
        toast.success('Job retried');
      }
      fetchJobs();
    } catch (err) {
      toast.error(err.friendlyMessage || `Failed to ${type} job`);
    }
  };

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

  const statusBadgeStyle = (status) => ({
    display: 'flex', alignItems: 'center', gap: 'var(--space-8)', fontWeight: 600,
    color: status === 'FAILURE' ? 'var(--danger)' : status === 'SUCCESS' ? 'var(--success)' : 'var(--text-primary)'
  });

  return (
    <div>
      <PageHeader
        title="Job Monitor"
        description="Real-time Celery task tracking for server-side processing workflows."
        actions={
          <div style={{ display: 'flex', gap: 'var(--space-12)', alignItems: 'center' }}>
            <span style={{ display: 'flex', gap: 'var(--space-8)' }}>
              <span className="stat-pill stat-pill--running">
                <span className="pulse-dot" style={{ background: 'var(--accent)' }} />
                {summary.running} Running
              </span>
              <span className="stat-pill stat-pill--failed">
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--danger)', display: 'inline-block', flexShrink: 0 }} />
                {summary.failed} Failed
              </span>
            </span>
            <button className="btn icon-only" onClick={fetchJobs} title="Refresh jobs" style={{ padding: 8 }}>
              <RefreshCw size={14} />
            </button>
            <select value={filterType} onChange={e => { setFilterType(e.target.value); setPage(1); }} style={{ padding: 'var(--space-8) var(--space-12)', width: 'auto' }}>
              <option value="">All Types</option>
              <option value="upload">Upload</option>
              <option value="auto_organize">Auto-Organize</option>
            </select>
            <select value={filterStatus} onChange={e => { setFilterStatus(e.target.value); setPage(1); }} style={{ padding: 'var(--space-8) var(--space-12)', width: 'auto' }}>
              <option value="">All Statuses</option>
              <option value="PENDING">PENDING</option>
              <option value="STARTED">STARTED</option>
              <option value="SUCCESS">SUCCESS</option>
              <option value="FAILURE">FAILURE</option>
            </select>
          </div>
        }
      />

      <ConfirmationModal 
        isOpen={confirmModal.isOpen}
        title={confirmModal.type === 'cancel' ? 'Cancel Job' : 'Retry Job'}
        body={`Are you sure you want to ${confirmModal.type} this job?`}
        confirmLabel={confirmModal.type === 'cancel' ? 'Cancel Job' : 'Retry Job'}
        variant={confirmModal.type === 'cancel' ? 'danger' : 'primary'}
        onConfirm={executeAction}
        onCancel={() => setConfirmModal({ isOpen: false, type: null, taskId: null })}
      />
      <ConfirmationModal 
        isOpen={errorModal.isOpen}
        title="Error Details"
        body={<pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 'var(--font-meta)', color: 'var(--danger)', background: 'var(--surface-base)', padding: 'var(--space-12)', borderRadius: 'var(--radius-sm)' }}>{errorModal.message}</pre>}
        confirmLabel="Close"
        variant="danger"
        onConfirm={() => setErrorModal({ isOpen: false, message: '' })}
        onCancel={() => setErrorModal({ isOpen: false, message: '' })}
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
                  <th>Triggered By</th>
                  <th>Path / Output</th>
                  <th>Timing</th>
                  <th>Duration</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map(j => (
                  <tr key={j._id} className={j.status === 'FAILURE' ? 'status-row--failed' : j.status === 'SUCCESS' ? 'status-row--success' : (j.status === 'STARTED' || j.status === 'PENDING') ? 'status-row--running' : ''}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-meta)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)' }}>
                        <span title={j.task_id}>{j.task_id.split('-')[0]}...</span>
                        <button className="btn icon-only" onClick={() => copyTaskId(j.task_id)} style={{ padding: 4, background: 'none', border: 'none', color: 'var(--text-muted)' }}><Copy size={12} /></button>
                      </div>
                    </td>
                    <td><span className="badge">{j.type}</span></td>
                    <td>
                      <div style={{...statusBadgeStyle(j.status), padding: '4px 10px', borderRadius: '12px', background: j.status === 'FAILURE' ? 'rgba(218,54,51,0.1)' : j.status === 'SUCCESS' ? 'rgba(35,134,54,0.1)' : j.status === 'STARTED' ? 'rgba(88,166,255,0.1)' : 'transparent', width: 'fit-content'}}>
                        <StatusIcon status={j.status} />
                        {j.status === 'STARTED' || j.status === 'PENDING'
                          ? <><span>{j.status}</span><span className="pulse-dot" style={{marginLeft: 4}}/></>
                          : j.status
                        }
                      </div>
                      {j.progress_step && (
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: 'var(--space-8)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', letterSpacing: '0.05em' }}>
                          {j.progress_step}
                        </div>
                      )}
                    </td>
                    <td>
                      {j.initiated_by_user ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', minWidth: 160 }}>
                          <UserRound size={14} color="var(--text-muted)" />
                          <div>
                            <div style={{ fontSize: 'var(--font-small)', fontWeight: 600 }}>{j.initiated_by_user.name || 'Unnamed user'}</div>
                            <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)' }}>{j.initiated_by_user.email || j.initiated_by_user.role}</div>
                          </div>
                        </div>
                      ) : (
                        <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-muted)' }}>System</span>
                      )}
                    </td>
                    <td style={{ maxWidth: '300px' }}>
                      {j.input_path && <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-meta)' }}><FileVideo size={12} style={{verticalAlign: 'middle', marginRight: '4px'}}/>{j.input_path.split(/[\/\\]/).pop()}</div>}
                      {j.output_path && <div style={{ color: 'var(--success)', fontSize: 'var(--font-meta)', marginTop: 4 }}>↳ {j.output_path.split(/[\/\\]/).pop()}</div>}
                      {j.error_message && (
                        <div style={{ marginTop: 8 }}>
                          <button onClick={() => setErrorModal({ isOpen: true, message: j.error_message })} style={{ background: 'rgba(218, 54, 51, 0.1)', color: 'var(--danger)', border: 'none', padding: 'var(--space-4) var(--space-8)', borderRadius: 'var(--radius-sm)', fontSize: 'var(--font-meta)', cursor: 'pointer' }}>View Error Details</button>
                        </div>
                      )}
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 'var(--font-meta)' }}>
                      {new Date(j.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 'var(--font-meta)' }}>
                      {j.duration_seconds !== undefined && j.duration_seconds !== null ? `${j.duration_seconds}s` : '-'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 'var(--space-8)' }}>
                        {(j.status === 'PENDING' || j.status === 'STARTED') && (
                          <button className="btn icon-only" onClick={() => setConfirmModal({ isOpen: true, type: 'cancel', taskId: j.task_id })} title="Cancel Job" style={{ padding: 6, color: 'var(--danger)', background: 'rgba(218,54,51,0.1)' }}>
                            <XSquare size={14} />
                          </button>
                        )}
                        {(j.status === 'FAILURE' || j.status === 'REVOKED') && (
                          <button className="btn icon-only" onClick={() => setConfirmModal({ isOpen: true, type: 'retry', taskId: j.task_id })} title="Retry Job" style={{ padding: 6, color: 'var(--accent)', background: 'rgba(88,166,255,0.1)' }}>
                            <PlayCircle size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {jobs.length > 0 && (
          <div style={{ padding: 'var(--space-16) var(--space-24)', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>Showing {jobs.length} of {total}</span>
            <div style={{ display: 'flex', gap: 'var(--space-8)', alignItems: 'center' }}>
              <button className="btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft size={16} /> Prev</button>
              <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>Page {page} of {totalPages || 1}</span>
              <button className="btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next <ChevronRight size={16} /></button>
            </div>
          </div>
        )}
      </ContentSection>
    </div>
  );
}
