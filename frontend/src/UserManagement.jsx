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
    <div style={{ position: 'fixed', inset: 0, zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }}>
      <div className="panel" style={{ width: '400px', backgroundColor: 'var(--surface-panel)', padding: 'var(--space-24)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-default)' }}>
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
              {role === 'editor' && "Can upload videos and trigger auto-organization. Cannot manage users or view system jobs."}
              {role === 'reviewer' && "Can review ambiguous clips in the Review Queue. Read-only access to organized footage."}
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
        <div style={{ padding: 'var(--space-16) var(--space-24)', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.01)', flexWrap: 'wrap', gap: 'var(--space-12)' }}>
          <div style={{ display: 'flex', gap: 'var(--space-12)', flex: 1, minWidth: '300px' }}>
            <div className="input-group" style={{ flex: 1, position: 'relative' }}>
               <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: 12, top: 10 }} />
               <input type="search" placeholder="Search by name or email..." value={search} onChange={e => {setSearch(e.target.value); setPage(1);}} style={{ paddingLeft: 36 }} />
            </div>
            <div className="input-group">
              <select value={roleFilter} onChange={e => { setRoleFilter(e.target.value); setPage(1); }}>
                <option value="all">Any Role</option>
                <option value="admin">Admin</option>
                <option value="reviewer">Reviewer</option>
                <option value="editor">Editor</option>
              </select>
            </div>
            <div className="input-group">
              <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }}>
                <option value="all">Any Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            <div className="input-group">
              <select value={`${sortBy}_${sortOrder}`} onChange={e => { 
                const value = e.target.value;
                const lastIndex = value.lastIndexOf('_');
                const sort = value.substring(0, lastIndex);
                const order = value.substring(lastIndex + 1);
                setSortBy(sort);
                setSortOrder(order);
                setPage(1);
              }}>
                <option value="created_at_desc">Joined (Newest)</option>
                <option value="created_at_asc">Joined (Oldest)</option>
                <option value="last_login_at_desc">Last Seen (Recent)</option>
                <option value="last_login_at_asc">Last Seen (Oldest)</option>
                <option value="name_asc">Name (A-Z)</option>
                <option value="name_desc">Name (Z-A)</option>
                <option value="role_asc">Role (A-Z)</option>
                <option value="role_desc">Role (Z-A)</option>
              </select>
            </div>
          </div>
          <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>Total: {total}</span>
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
                {users.map(u => (
                  <tr key={u._id}>
                    <td>
                      <div style={{ fontWeight: '600' }}>{u.username || u.name}</div>
                      <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginTop: 'var(--space-4)' }}>{u.email || 'No email'}</div>
                    </td>
                    <td><span className={`badge ${u.role === 'admin' ? 'info' : u.role === 'editor' ? 'success' : 'warning'}`}>{u.role}</span></td>
                    <td>
                      {u.is_active
                        ? <span className="badge success" style={{ background: 'transparent' }}><UserCheck size={14}/> Active</span>
                        : <span className="badge danger" style={{ background: 'transparent' }}><UserX size={14}/> Inactive</span>
                      }
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{new Date(u.created_at).toLocaleDateString()}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{relativeTime(u.last_login_at)}</td>
                    <td>
                      {u.id !== currentUser.id && u._id !== currentUser.id ? (
                        <div style={{ display: 'flex', gap: 'var(--space-8)', alignItems: 'center' }}>
                          <select value={u.role} onChange={e => initiateRoleChange(u._id, e.target.value)} style={{ padding: 'var(--space-4) var(--space-8)', width: 'auto' }}>
                            <option value="admin">Admin</option>
                            <option value="reviewer">Reviewer</option>
                            <option value="editor">Editor</option>
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
                ))}
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
