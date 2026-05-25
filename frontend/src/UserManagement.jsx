import React, { useState, useEffect } from 'react';
import { API_BASE } from './config';
import { ShieldAlert, ShieldCheck, UserX, UserCheck, ChevronLeft, ChevronRight, Users, RefreshCw, Search, Filter } from 'lucide-react';
import PageHeader from './components/PageHeader';
import ContentSection from './components/ContentSection';
import LoadingState from './components/LoadingState';
import EmptyState from './components/EmptyState';
import ConfirmationModal from './components/ConfirmationModal';
import { relativeTime } from './hooks/useRelativeTime';
import api from './lib/api';
import { useToast } from './hooks/useToast.jsx';

const ACTIVE_ROLES = ['admin', 'editor', 'reviewer'];

function InviteModal({ isOpen, onClose, onInvite }) {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('editor');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.post('/invite', { email, role });
      onInvite();
      setEmail('');
      setRole('editor');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send invite');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-glass" style={{ width: '420px', padding: 'var(--space-24)' }}>
        <h3 style={{ margin: '0 0 var(--space-16) 0', fontSize: '18px', fontWeight: 600 }}>Invite Team Member</h3>
        <form onSubmit={handleSubmit}>
          {error && <div className="toast toast-error" style={{ marginBottom: 'var(--space-16)' }}>{error}</div>}
          <div className="input-group" style={{ marginBottom: 'var(--space-16)' }}>
            <label>Email Address</label>
            <input type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="colleague@example.com" />
          </div>
          <div className="input-group" style={{ marginBottom: 'var(--space-24)' }}>
            <label>Role</label>
            <select value={role} onChange={e => setRole(e.target.value)}>
              <option value="editor">Editor</option>
              <option value="reviewer">Reviewer</option>
              <option value="admin">Admin</option>
            </select>
            <div style={{ marginTop: 'var(--space-8)', fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              {role === 'editor' && "Can upload, review, organize, download, and delete their own videos."}
              {role === 'reviewer' && "Can review clips assigned to them, without upload, download, or admin permissions."}
              {role === 'admin' && "Full platform access. Can manage users, monitor jobs, and access system settings."}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-12)', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} className="btn" style={{ background: 'transparent' }} disabled={loading}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading || !email}>{loading ? 'Sending...' : 'Send Invite'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function UserManagement({ currentUser }) {
  const toast = useToast();
  const [users, setUsers] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 15;
  const [loading, setLoading] = useState(true);
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  
  const [confirmAction, setConfirmAction] = useState({ isOpen: false, type: null, userId: null, payload: null });

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(handler);
  }, [search]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/admin/users?page=${page}&limit=${limit}&search=${encodeURIComponent(debouncedSearch)}&role=${roleFilter}&status=${statusFilter}&sort=${sortBy}&order=${sortOrder}`);
      setUsers(res.data.users || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      toast.error(err.friendlyMessage || 'Failed to load users');
    }
    setLoading(false);
  };

  useEffect(() => { fetchUsers(); }, [page, debouncedSearch, roleFilter, statusFilter, sortBy, sortOrder]);

  const initiateRoleChange = (userId, newRole) => {
    setConfirmAction({
      isOpen: true,
      type: 'role',
      userId,
      payload: { role: newRole }
    });
  };

  const initiateStatusChange = (userId, isActive) => {
    setConfirmAction({
      isOpen: true,
      type: 'status',
      userId,
      payload: { is_active: isActive }
    });
  };

  const executeConfirmAction = async () => {
    const { type, userId, payload } = confirmAction;
    try {
      if (type === 'role') {
        await api.patch(`/admin/users/${userId}/role`, payload);
        toast.success('Role updated successfully');
      } else if (type === 'status') {
        await api.patch(`/admin/users/${userId}/status`, payload);
        toast.success(payload.is_active ? 'User activated' : 'User deactivated');
      }
      fetchUsers();
    } catch (err) {
      toast.error(err.friendlyMessage || 'Action failed');
    } finally {
      setConfirmAction({ isOpen: false, type: null, userId: null, payload: null });
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      <PageHeader
        title="User Management"
        eyebrow="TEAM · MEMBERS"
        description="Control access and permissions for all users across the platform."
        actions={
          <div style={{ display: 'flex', gap: 'var(--space-8)' }}>
            <button className="btn" onClick={fetchUsers}>
              <RefreshCw size={16} /> Refresh
            </button>
            <button className="btn btn-primary" onClick={() => setIsInviteModalOpen(true)}>
              <Users size={16} /> Invite User
            </button>
          </div>
        }
      />

      <InviteModal 
        isOpen={isInviteModalOpen} 
        onClose={() => setIsInviteModalOpen(false)} 
        onInvite={() => {
          setIsInviteModalOpen(false);
          toast.success("Invitation sent successfully");
          // Optionally fetch invitations here if displaying them
        }}
      />

      <ConfirmationModal 
        isOpen={confirmAction.isOpen}
        title={confirmAction.type === 'role' ? 'Change User Role' : 'Change User Status'}
        body={
          confirmAction.type === 'role' 
            ? `You are about to change this user's role to ${confirmAction.payload?.role}. Are you sure?` 
            : `You are about to ${confirmAction.payload?.is_active ? 'activate' : 'deactivate'} this account. Are you sure?`
        }
        confirmLabel={confirmAction.type === 'role' ? 'Change Role' : (confirmAction.payload?.is_active ? 'Activate' : 'Deactivate')}
        variant={confirmAction.payload?.is_active ? 'primary' : 'danger'}
        onConfirm={executeConfirmAction}
        onCancel={() => setConfirmAction({ isOpen: false, type: null, userId: null, payload: null })}
      />

      <ContentSection style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: 'var(--space-16) var(--space-24)', borderBottom: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: 'var(--space-12)', background: 'rgba(255,255,255,0.01)' }}>
          <div style={{ display: 'flex', gap: 'var(--space-12)', alignItems: 'center', flexWrap: 'wrap' }}>
            <div className="filter-search" style={{ flex: '1 1 240px' }}>
              <Search size={14} color="var(--text-muted)" />
              <input type="search" placeholder="Search by name or email..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
            </div>
            <select value={`${sortBy}_${sortOrder}`} onChange={e => {
              const value = e.target.value;
              const lastIndex = value.lastIndexOf('_');
              setSortBy(value.substring(0, lastIndex));
              setSortOrder(value.substring(lastIndex + 1));
              setPage(1);
            }} style={{ padding: 'var(--space-8) var(--space-12)', width: 'auto' }}>
              <option value="created_at_desc">Joined (Newest)</option>
              <option value="created_at_asc">Joined (Oldest)</option>
              <option value="last_login_at_desc">Last Seen (Recent)</option>
              <option value="last_login_at_asc">Last Seen (Oldest)</option>
              <option value="name_asc">Name (A–Z)</option>
              <option value="name_desc">Name (Z–A)</option>
            </select>
            <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)', marginLeft: 'auto' }}>Total: {total}</span>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-24)', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)' }}>
              <span className="mono-caps" style={{ marginRight: 4 }}>Role</span>
              <div className="filter-chips">
                {['all', ...ACTIVE_ROLES].map(r => (
                  <button key={r} className={`chip${roleFilter === r ? ' active' : ''}`} onClick={() => { setRoleFilter(r); setPage(1); }}>
                    {r === 'all' ? 'Any' : r.charAt(0).toUpperCase() + r.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)' }}>
              <span className="mono-caps" style={{ marginRight: 4 }}>Status</span>
              <div className="filter-chips">
                {['all', 'active', 'inactive'].map(s => (
                  <button key={s} className={`chip${statusFilter === s ? ' active' : ''}`} onClick={() => { setStatusFilter(s); setPage(1); }}>
                    {s === 'all' ? 'Any' : s.charAt(0).toUpperCase() + s.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {loading ? (
          <LoadingState type="table" />
        ) : users.length === 0 ? (
          <EmptyState icon={Users} title="No Users Found" message="There are no users to display." />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Joined</th>
                  <th>Last Seen</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => {
                  const initials = (u.username || u.name || '?').slice(0, 2).toUpperCase();
                  const avatarClass = u.role === 'admin' ? 'avatar-gradient-admin' : 'avatar-gradient-editor';
                  const lastSeen = u.last_login_at ? new Date(u.last_login_at) : null;
                  const minsAgo = lastSeen ? (Date.now() - lastSeen.getTime()) / 60000 : Infinity;
                  const presenceClass = minsAgo < 5 ? 'presence-dot--active' : minsAgo < 60 ? 'presence-dot--recent' : 'presence-dot--idle';
                  return (
                  <tr key={u._id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)' }}>
                        <div className={avatarClass} style={{ width: 36, height: 36, borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 600, fontSize: 'var(--font-meta)', flexShrink: 0 }}>{initials}</div>
                        <div>
                          <div style={{ fontWeight: '600' }}>{u.username || u.name}</div>
                          <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginTop: 2 }}>{u.email || 'No email'}</div>
                        </div>
                      </div>
                    </td>
                    <td><span className={`badge ${u.role === 'admin' ? 'info' : u.role === 'editor' ? 'success' : 'warning'}`}>{u.role}</span></td>
                    <td>
                      {u.is_active
                        ? <span className="badge success" style={{ background: 'transparent' }}><UserCheck size={14}/> Active</span>
                        : <span className="badge danger" style={{ background: 'transparent' }}><UserX size={14}/> Inactive</span>
                      }
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{new Date(u.created_at).toLocaleDateString()}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', color: 'var(--text-secondary)' }}>
                        <span className={`presence-dot ${presenceClass}`} />
                        {relativeTime(u.last_login_at)}
                      </div>
                    </td>
                    <td>
                      {u.id !== currentUser.id && u._id !== currentUser.id ? (
                        <div style={{ display: 'flex', gap: 'var(--space-8)', alignItems: 'center' }}>
                          <select value={u.role} onChange={e => initiateRoleChange(u._id, e.target.value)} style={{ padding: 'var(--space-4) var(--space-8)', width: 'auto' }}>
                            {!ACTIVE_ROLES.includes(u.role) && (
                              <option value={u.role}>Legacy: {u.role}</option>
                            )}
                            <option value="admin">Admin</option>
                            <option value="editor">Editor</option>
                            <option value="reviewer">Reviewer</option>
                          </select>
                          <button
                            onClick={() => initiateStatusChange(u._id, !u.is_active)}
                            style={{ padding: 'var(--space-8)', border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer', background: u.is_active ? 'rgba(218, 54, 51, 0.1)' : 'rgba(35, 134, 54, 0.1)', color: u.is_active ? 'var(--danger)' : 'var(--success)' }}
                            title={u.is_active ? 'Deactivate User' : 'Activate User'}
                            aria-label={u.is_active ? 'Deactivate User' : 'Activate User'}
                          >
                            {u.is_active ? <ShieldAlert size={16} /> : <ShieldCheck size={16} />}
                          </button>
                        </div>
                      ) : (
                        <span style={{ fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', padding: 'var(--space-4) var(--space-8)', background: 'var(--surface-base)', borderRadius: 'var(--radius-sm)' }}>It's you</span>
                      )}
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <div style={{ padding: 'var(--space-16) var(--space-24)', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>Showing {users.length} of {total}</span>
          <div style={{ display: 'flex', gap: 'var(--space-8)', alignItems: 'center' }}>
            <button className="btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft size={16} /> Prev</button>
            <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>
              Page {page} of {totalPages || 1}
            </span>
            <button className="btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next <ChevronRight size={16} /></button>
          </div>
        </div>
      </ContentSection>
    </div>
  );
}
