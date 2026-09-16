import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { cn, formatDate } from '../lib/utils';
import { User, UserRole } from '../types';
import { Users, Plus, Edit2, Trash2, X } from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';

export function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    role: 'ops_manager' as UserRole,
    password: '',
    is_active: true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [roles] = useState<UserRole[]>([
    'client_leadership',
    'ops_leadership',
    'ops_manager',
    'team_lead',
    'ar_executive',
    'qa_auditor',
  ]);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const users = await api.getUsers();
      setUsers(users);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (user?: User) => {
    if (user) {
      setEditingUser(user);
      setFormData({
        name: user.name,
        email: user.email,
        role: user.role,
        password: '',
        is_active: user.is_active,
      });
    } else {
      setEditingUser(null);
      setFormData({
        name: '',
        email: '',
        role: 'ops_manager',
        password: '',
        is_active: true,
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingUser(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (editingUser) {
        // For editing, we'd need a PATCH endpoint
        // For now, just close modal
        setShowModal(false);
      } else {
        await api.register(formData);
        fetchUsers();
        setShowModal(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save user');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (_userId: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    // Would need a DELETE endpoint
    alert('Delete functionality would be implemented with a DELETE endpoint');
  };

  const formatRole = (role: UserRole) => {
    return role.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  const getRoleBadge = (role: UserRole) => {
    const badges: Record<UserRole, string> = {
      client_leadership: 'bg-purple-100 text-purple-800',
      ops_leadership: 'bg-blue-100 text-blue-800',
      ops_manager: 'bg-green-100 text-green-800',
      team_lead: 'bg-amber-100 text-amber-800',
      ar_executive: 'bg-orange-100 text-orange-800',
      qa_auditor: 'bg-red-100 text-red-800',
    };
    return badges[role] || 'bg-slate-100 text-slate-800';
  };

  return (
          <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">User Management</h1>
            <p className="text-slate-600">Manage system users and roles</p>
          </div>
          <button onClick={() => handleOpenModal()} className="btn-primary">
            <Plus className="w-4 h-4 mr-2" />
            Add User
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent mx-auto" />
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-slate-50 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                        <th className="px-4 py-3">User</th>
                        <th className="px-4 py-3">Email</th>
                        <th className="px-4 py-3">Role</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3">Created</th>
                        <th className="px-4 py-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-sm">
                      {users.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="px-4 py-12 text-center text-slate-500">
                            No users found
                          </td>
                        </tr>
                      ) : (
                        users.map((user) => (
                          <tr key={user.user_id} className="hover:bg-slate-50/80 transition-colors">
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                                  <Users className="w-4 h-4 text-primary-600" />
                                </div>
                                <span className="font-medium text-slate-900">{user.name}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-slate-600">{user.email}</td>
                            <td className="px-4 py-3">
                              <span className={cn('badge', getRoleBadge(user.role))}>
                                {formatRole(user.role)}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <span className={cn('badge', user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800')}>
                                {user.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-slate-600">{formatDate(user.created_at)}</td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <button
                                  onClick={() => handleOpenModal(user)}
                                  className="p-2 rounded-lg hover:bg-slate-100 text-slate-500"
                                  title="Edit"
                                >
                                  <Edit2 className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleDelete(user.user_id)}
                                  className="p-2 rounded-lg hover:bg-slate-100 text-slate-500"
                                  title="Delete"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white rounded-xl shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
              <div className="p-4 border-b border-slate-200 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">
                  {editingUser ? 'Edit User' : 'Add New User'}
                </h2>
                <button onClick={handleCloseModal} className="p-2 rounded-lg hover:bg-slate-100">
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <form onSubmit={handleSubmit} className="p-4 space-y-4">
                <div>
                  <label className="label">Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="label">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    className="input"
                    required
                    disabled={!!editingUser}
                  />
                </div>
                <div>
                  <label className="label">Role</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value as UserRole }))}
                    className="input"
                    required
                  >
                    {roles.map(role => (
                      <option key={role} value={role}>{formatRole(role)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">
                    {editingUser ? 'New Password (leave blank to keep current)' : 'Password'}
                  </label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                    className="input"
                    required={!editingUser}
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="w-4 h-4 text-primary-600 border-slate-300 rounded focus:ring-primary-500"
                  />
                  <label htmlFor="is_active" className="ml-2 text-sm text-slate-700">Active</label>
                </div>
                
                <div className="flex justify-end gap-2 pt-4 border-t border-slate-200">
                  <button type="button" onClick={handleCloseModal} className="btn-secondary">
                    Cancel
                  </button>
                  <button type="submit" disabled={submitting} className="btn-primary">
                    {submitting ? 'Saving...' : editingUser ? 'Update' : 'Create'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>);
}