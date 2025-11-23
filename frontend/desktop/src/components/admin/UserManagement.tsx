import { useState, useEffect } from 'react';
import { Search, Edit2, Trash2, UserCheck, UserX, Shield, User as UserIcon, X } from 'lucide-react';
import { admin } from '../../config/api';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';

interface User {
    username: string;
    full_name: string;
    email: string;
    role: string;
    disabled?: boolean;
    gender?: string;
    hometown?: string;
    current_address?: string;
    created_at: number;
    updated_at: number;
}

export function UserManagement() {
    const [users, setUsers] = useState<User[]>([]);
    const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [selectedUser, setSelectedUser] = useState<User | null>(null);
    const [showEditModal, setShowEditModal] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        fetchUsers();
    }, []);

    useEffect(() => {
        if (!searchQuery.trim()) {
            setFilteredUsers(users);
        } else {
            const query = searchQuery.toLowerCase();
            setFilteredUsers(
                users.filter(
                    (user) =>
                        user.username.toLowerCase().includes(query) ||
                        user.full_name.toLowerCase().includes(query) ||
                        user.email.toLowerCase().includes(query)
                )
            );
        }
    }, [searchQuery, users]);

    const fetchUsers = async () => {
        setIsLoading(true);
        try {
            const data = await admin.listUsers();
            setUsers(data);
            setFilteredUsers(data);
        } catch (err: any) {
            setError('Failed to load users');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleEdit = (user: User) => {
        setSelectedUser(user);
        setShowEditModal(true);
    };

    const handleDelete = async (username: string) => {
        if (!confirm(`Are you sure you want to delete user "${username}"?`)) {
            return;
        }

        try {
            await admin.deleteUser(username);
            setSuccess(`User "${username}" deleted successfully`);
            fetchUsers();
            setTimeout(() => setSuccess(''), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to delete user');
            setTimeout(() => setError(''), 3000);
        }
    };

    const handleToggleStatus = async (user: User) => {
        try {
            await admin.updateUser(user.username, { enabled: !user.disabled });
            setSuccess(`User ${user.disabled ? 'activated' : 'deactivated'} successfully`);
            fetchUsers();
            setTimeout(() => setSuccess(''), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to update user status');
            setTimeout(() => setError(''), 3000);
        }
    };

    const handleToggleRole = async (user: User) => {
        const newRole = user.role === 'Admin' ? 'Staff' : 'Admin';

        if (!confirm(`Change ${user.username}'s role to ${newRole}?`)) {
            return;
        }

        try {
            await admin.updateUser(user.username, { role: newRole });
            setSuccess(`Role updated to ${newRole} successfully`);
            fetchUsers();
            setTimeout(() => setSuccess(''), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to update role');
            setTimeout(() => setError(''), 3000);
        }
    };

    const formatDate = (timestamp: number) => {
        return new Date(timestamp * 1000).toLocaleDateString();
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-gray-400">Loading users...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto p-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">User Management</h1>
                <p className="text-gray-400">Manage all users and permissions</p>
            </div>

            {/* Alerts */}
            {error && (
                <div className="mb-4 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 p-4 rounded">
                    <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
                </div>
            )}

            {success && (
                <div className="mb-4 bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500 p-4 rounded">
                    <p className="text-sm text-green-700 dark:text-green-400">{success}</p>
                </div>
            )}

            {/* Search Bar */}
            <Card className="p-4 mb-6">
                <div className="flex items-center gap-4">
                    <div className="flex-1">
                        <Input
                            icon={Search}
                            type="text"
                            placeholder="Search users by username, name, or email..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <div className="text-sm text-gray-400">
                        Showing {filteredUsers.length} of {users.length} users
                    </div>
                </div>
            </Card>

            {/* User Table */}
            <Card className="p-6">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-700">
                                <th className="text-left p-3 text-gray-400 font-medium">Username</th>
                                <th className="text-left p-3 text-gray-400 font-medium">Full Name</th>
                                <th className="text-left p-3 text-gray-400 font-medium">Email</th>
                                <th className="text-left p-3 text-gray-400 font-medium">Role</th>
                                <th className="text-left p-3 text-gray-400 font-medium">Status</th>
                                <th className="text-left p-3 text-gray-400 font-medium">Created</th>
                                <th className="text-right p-3 text-gray-400 font-medium">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredUsers.map((user) => (
                                <tr key={user.username} className="border-b border-gray-800 hover:bg-gray-800/50 transition-colors">
                                    <td className="p-3">
                                        <div className="flex items-center gap-2">
                                            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                                                {user.username[0].toUpperCase()}
                                            </div>
                                            <span className="text-white font-medium">{user.username}</span>
                                        </div>
                                    </td>
                                    <td className="p-3 text-gray-300">{user.full_name}</td>
                                    <td className="p-3 text-gray-400 text-sm">{user.email}</td>
                                    <td className="p-3">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${user.role === 'Admin'
                                            ? 'bg-purple-500/20 text-purple-400'
                                            : 'bg-blue-500/20 text-blue-400'
                                            }`}>
                                            {user.role}
                                        </span>
                                    </td>
                                    <td className="p-3">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${user.disabled
                                            ? 'bg-red-500/20 text-red-400'
                                            : 'bg-green-500/20 text-green-400'
                                            }`}>
                                            {user.disabled ? 'Disabled' : 'Active'}
                                        </span>
                                    </td>
                                    <td className="p-3 text-gray-400 text-sm">{formatDate(user.created_at)}</td>
                                    <td className="p-3">
                                        <div className="flex items-center justify-end gap-2">
                                            <button
                                                onClick={() => handleToggleRole(user)}
                                                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                                                title={`Change to ${user.role === 'Admin' ? 'Staff' : 'Admin'}`}
                                            >
                                                <Shield className="w-4 h-4 text-purple-400" />
                                            </button>
                                            <button
                                                onClick={() => handleToggleStatus(user)}
                                                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                                                title={user.disabled ? 'Activate user' : 'Deactivate user'}
                                            >
                                                {user.disabled ? (
                                                    <UserCheck className="w-4 h-4 text-green-400" />
                                                ) : (
                                                    <UserX className="w-4 h-4 text-orange-400" />
                                                )}
                                            </button>
                                            <button
                                                onClick={() => handleEdit(user)}
                                                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                                                title="Edit user"
                                            >
                                                <Edit2 className="w-4 h-4 text-blue-400" />
                                            </button>
                                            <button
                                                onClick={() => handleDelete(user.username)}
                                                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                                                title="Delete user"
                                            >
                                                <Trash2 className="w-4 h-4 text-red-400" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    {filteredUsers.length === 0 && (
                        <div className="text-center py-12">
                            <UserIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                            <p className="text-gray-400">No users found</p>
                        </div>
                    )}
                </div>
            </Card>

            {/* Edit Modal */}
            {showEditModal && selectedUser && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <Card className="max-w-md w-full mx-4 p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-xl font-semibold text-white">Edit User</h3>
                            <button
                                onClick={() => setShowEditModal(false)}
                                className="p-2 hover:bg-gray-700 rounded-lg"
                            >
                                <X className="w-5 h-5 text-gray-400" />
                            </button>
                        </div>
                        <div className="text-gray-400 mb-4">
                            <p><strong>Username:</strong> {selectedUser.username}</p>
                            <p><strong>Email:</strong> {selectedUser.email}</p>
                            <p><strong>Role:</strong> {selectedUser.role}</p>
                        </div>
                        <p className="text-sm text-gray-500 mb-4">
                            Use the action buttons in the table to change role, status, or delete user.
                        </p>
                        <Button
                            variant="secondary"
                            className="w-full"
                            onClick={() => setShowEditModal(false)}
                        >
                            Close
                        </Button>
                    </Card>
                </div>
            )}
        </div>
    );
}
