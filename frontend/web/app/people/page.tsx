'use client';
import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import Card, { CardBody, CardHeader } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Badge from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/Loading';
import { people } from '@/lib/api';
import Link from 'next/link';
import { Trash2, UserPlus, Users as UsersIcon, Search, Grid, List } from 'lucide-react';

export default function PeoplePage() {
    const [users, setUsers] = useState<any[]>([]);
    const [filteredUsers, setFilteredUsers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [deleteModal, setDeleteModal] = useState<{ isOpen: boolean; user: any | null }>({
        isOpen: false,
        user: null,
    });

    useEffect(() => {
        fetchPeople();
    }, []);

    useEffect(() => {
        if (searchTerm) {
            const filtered = users.filter(
                (user) =>
                    user.user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    user.person_id.toLowerCase().includes(searchTerm.toLowerCase())
            );
            setFilteredUsers(filtered);
        } else {
            setFilteredUsers(users);
        }
    }, [searchTerm, users]);

    const fetchPeople = async () => {
        try {
            const res = await people.list();
            setUsers(res.data);
            setFilteredUsers(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (userId: string) => {
        try {
            await people.delete(userId);
            setDeleteModal({ isOpen: false, user: null });
            fetchPeople();
        } catch (err) {
            console.error('Failed to delete user:', err);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
            <Navbar />

            <div className="container mx-auto p-6 space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between flex-wrap gap-4">
                    <div>
                        <h1 className="text-4xl font-bold text-white mb-2">People Management</h1>
                        <p className="text-gray-400">Manage enrolled users in the system</p>
                    </div>
                    <Link href="/enroll">
                        <Button variant="primary">
                            <UserPlus size={20} />
                            Add New Person
                        </Button>
                    </Link>
                </div>

                {/* Search and View Toggle */}
                <Card>
                    <CardBody>
                        <div className="flex flex-col md:flex-row gap-4 items-end">
                            <div className="flex-1">
                                <div className="relative">
                                    <input
                                        type="text"
                                        placeholder="Search by name or user ID..."
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                        className="w-full px-4 py-2.5 pl-10 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                    <Search className="absolute left-3 top-3 text-gray-500" size={18} />
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setViewMode('grid')}
                                    className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400'
                                        }`}
                                >
                                    <Grid size={20} />
                                </button>
                                <button
                                    onClick={() => setViewMode('list')}
                                    className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400'
                                        }`}
                                >
                                    <List size={20} />
                                </button>
                            </div>
                        </div>
                    </CardBody>
                </Card>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card hover>
                        <CardBody className="flex items-center gap-4">
                            <div className="p-3 bg-blue-500/20 rounded-lg">
                                <UsersIcon size={24} className="text-blue-400" />
                            </div>
                            <div>
                                <p className="text-gray-400 text-sm">Total People</p>
                                <p className="text-2xl font-bold text-white">{filteredUsers.length}</p>
                            </div>
                        </CardBody>
                    </Card>
                </div>

                {/* Users Display */}
                {loading ? (
                    <Card>
                        <CardBody className="flex justify-center py-12">
                            <LoadingSpinner size="lg" />
                        </CardBody>
                    </Card>
                ) : filteredUsers.length === 0 ? (
                    <Card>
                        <CardBody className="text-center py-12">
                            <UsersIcon size={48} className="mx-auto mb-4 opacity-50 text-gray-400" />
                            <p className="text-lg font-medium text-gray-300">No people found</p>
                            <p className="text-sm text-gray-500 mb-6">
                                {searchTerm ? 'Try a different search term' : 'Add your first person to get started'}
                            </p>
                            <Link href="/enroll">
                                <Button variant="primary">
                                    <UserPlus size={20} />
                                    Enroll New Person
                                </Button>
                            </Link>
                        </CardBody>
                    </Card>
                ) : viewMode === 'grid' ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredUsers.map((user) => (
                            <Card key={user.person_id} hover>
                                <CardBody>
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                                <span className="text-white font-bold text-lg">
                                                    {user.user_name.charAt(0).toUpperCase()}
                                                </span>
                                            </div>
                                            <div>
                                                <h3 className="text-white font-bold text-lg">{user.user_name}</h3>
                                                <p className="text-gray-400 text-sm">{user.person_id}</p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => setDeleteModal({ isOpen: true, user })}
                                            className="text-red-500 hover:text-red-400 p-2 hover:bg-gray-800 rounded-lg transition-colors"
                                        >
                                            <Trash2 size={20} />
                                        </button>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-gray-400">Face ID:</span>
                                            <Badge variant="info">{user.face_id?.substring(0, 8)}...</Badge>
                                        </div>
                                    </div>
                                </CardBody>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <Card>
                        <CardBody>
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-gray-700">
                                            <th className="text-left p-4 text-gray-400 font-medium">Name</th>
                                            <th className="text-left p-4 text-gray-400 font-medium">User ID</th>
                                            <th className="text-left p-4 text-gray-400 font-medium">Face ID</th>
                                            <th className="text-left p-4 text-gray-400 font-medium">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filteredUsers.map((user) => (
                                            <tr key={user.person_id} className="border-b border-gray-800 hover:bg-gray-800/50">
                                                <td className="p-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                                            <span className="text-white font-bold">
                                                                {user.user_name.charAt(0).toUpperCase()}
                                                            </span>
                                                        </div>
                                                        <span className="text-white font-medium">{user.user_name}</span>
                                                    </div>
                                                </td>
                                                <td className="p-4 text-gray-300">{user.person_id}</td>
                                                <td className="p-4">
                                                    <Badge variant="info">{user.face_id?.substring(0, 12)}...</Badge>
                                                </td>
                                                <td className="p-4">
                                                    <button
                                                        onClick={() => setDeleteModal({ isOpen: true, user })}
                                                        className="text-red-500 hover:text-red-400"
                                                    >
                                                        <Trash2 size={20} />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </CardBody>
                    </Card>
                )}
            </div>

            {/* Delete Confirmation Modal */}
            <Modal
                isOpen={deleteModal.isOpen}
                onClose={() => setDeleteModal({ isOpen: false, user: null })}
                title="Confirm Delete"
            >
                <div className="space-y-4">
                    <p className="text-gray-300">
                        Are you sure you want to delete <span className="font-bold text-white">{deleteModal.user?.user_name}</span>?
                        This action cannot be undone.
                    </p>
                    <div className="flex gap-3 justify-end">
                        <Button variant="outline" onClick={() => setDeleteModal({ isOpen: false, user: null })}>
                            Cancel
                        </Button>
                        <Button variant="danger" onClick={() => handleDelete(deleteModal.user?.person_id)}>
                            <Trash2 size={18} />
                            Delete
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
}
