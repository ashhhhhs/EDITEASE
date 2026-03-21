import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE } from './config';
import { ShieldAlert, ShieldCheck, UserX, UserCheck, ChevronLeft, ChevronRight, Users, RefreshCw } from 'lucide-react';
import PageHeader from './components/PageHeader';
import ContentSection from './components/ContentSection';
import LoadingState from './components/LoadingState';
import EmptyState from './components/EmptyState';

export default function UserManagement({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 15;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/admin/users?page=${page}&limit=${limit}`);
      setUsers(res.data.users || []);
      setTotal(res.data.total || 0);
      setError('');
    } catch (err) {
      console.error(err);
      setError('Failed to load users');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchUsers();
  }, [page]);

  const handleRoleChange = async (userId, newRole) => {
    try {
      await axios.patch(`${API_BASE}/admin/users/${userId}/role`, { role: newRole });
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.error || 'Role change failed');
    }
  };

  const handleStatusChange = async (userId, isActive) => {
    try {
      await axios.patch(`${API_BASE}/admin/users/${userId}/status`, { is_active: isActive });
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.error || 'Status change failed');
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      <PageHeader 
        title="User Management" 
        description="Control access and permissions for all users across the platform."
        actions={
            <button className="styled-button secondary" onClick={fetchUsers}>
                <RefreshCw size={16} /> Refresh
            </button>
        }
      />

      {error && <div style={{ color: 'var(--danger)', marginBottom: 'var(--space-16)', padding: 'var(--space-16)', background: 'rgba(218, 54, 51, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(218, 54, 51, 0.2)' }}>{error}</div>}

      <ContentSection style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: 'var(--space-16) var(--space-24)', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.01)' }}>
            <h3 style={{ margin: 0, fontSize: 'var(--font-body)', fontWeight: 600 }}>System Members</h3>
            <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>Total: {total}</span>
        </div>

        {loading ? (
          <LoadingState type="table" />
        ) : users.length === 0 ? (
          <EmptyState icon={Users} title="No Users Found" message="There are no users to display matching the current criteria." />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Joined</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u._id}>
                    <td>
                      <div style={{ fontWeight: '600' }}>{u.username}</div>
                      <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-secondary)', marginTop: 'var(--space-4)' }}>{u.email || 'No email'}</div>
                    </td>
                    <td>
                      <span className={`badge ${u.role === 'admin' ? 'info' : ''}`}>{u.role}</span>
                    </td>
                    <td>
                      {u.is_active ? (
                          <span style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}><UserCheck size={14}/> Active</span>
                      ) : (
                          <span style={{ color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}><UserX size={14}/> Inactive</span>
                      )}
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      {u.id !== currentUser.id ? (
                        <div style={{ display: 'flex', gap: 'var(--space-8)', alignItems: 'center' }}>
                          <select 
                            value={u.role} 
                            onChange={(e) => handleRoleChange(u._id, e.target.value)}
                            className="styled-input"
                            style={{ padding: 'var(--space-4) var(--space-8)', width: 'auto' }}
                          >
                            <option value="admin">Admin</option>
                            <option value="reviewer">Reviewer</option>
                            <option value="editor">Editor</option>
                          </select>
                          
                          <button 
                              onClick={() => handleStatusChange(u._id, !u.is_active)}
                              style={{ padding: 'var(--space-8)', border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer', background: u.is_active ? 'rgba(218, 54, 51, 0.1)' : 'rgba(35, 134, 54, 0.1)', color: u.is_active ? 'var(--danger)' : 'var(--success)' }}
                              title={u.is_active ? "Deactivate User" : "Activate User"}
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
          <span style={{ fontSize: 'var(--font-small)', color: 'var(--text-secondary)' }}>Showing {users.length} of {total} results</span>
          <div style={{ display: 'flex', gap: 'var(--space-8)', alignItems: 'center' }}>
            <button className="btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft size={16} /> Prev</button>
            <button className="btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next <ChevronRight size={16} /></button>
          </div>
        </div>
      </ContentSection>
    </div>
  );
}
