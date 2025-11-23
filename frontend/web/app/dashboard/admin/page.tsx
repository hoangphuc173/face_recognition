'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Card, { CardBody, CardHeader } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/Loading';
import { people, logs } from '@/lib/api';
import { Users, Camera, Activity, TrendingUp, Video, UserPlus, Search, Edit, Trash2, Shield } from 'lucide-react';
import Link from 'next/link';

export default function AdminDashboard() {
    const [stats, setStats] = useState({
        totalPeople: 0,
        recentIdentifications: 0,
        systemStatus: 'operational',
    });
    const [recentLogs, setRecentLogs] = useState<any[]>([]);
    const [users, setUsers] = useState<any[]>([]); // For User Management
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const router = useRouter();

    useEffect(() => {
        // Verify Admin Role
        const userStr = localStorage.getItem('user');
        if (!userStr) {
            router.push('/');
            return;
        }
        const user = JSON.parse(userStr);
        if (user.role !== 'Admin') {
            router.push('/dashboard/user');
            return;
        }

        fetchData();
    }, [router]);

    const fetchData = async () => {
        try {
            // Fetch people count
            const peopleRes = await people.list();
            const totalPeople = peopleRes.data.length;
            setUsers(peopleRes.data.map((p: any) => ({
                id: p.UserId,
                username: p.Name, // Assuming Name is username for now
                full_name: p.Name,
                role: 'User', // Default to User for now
                email: 'N/A'
            })));

            // Fetch recent logs
            const logsRes = await logs.list();
            const recentLogs = logsRes.data.slice(0, 5);
            const recentIdentifications = logsRes.data.filter((log: any) => {
                const logTime = log.Timestamp * 1000;
                const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
                return logTime > oneDayAgo;
            }).length;

            setStats({
                totalPeople,
                recentIdentifications,
                systemStatus: 'operational',
            });
            setRecentLogs(recentLogs);
        } catch (err) {
            console.error('Failed to fetch dashboard data:', err);
        } finally {
            setLoading(false);
        }
    };

    const filteredUsers = users.filter(u =>
        u.username.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-950 flex items-center justify-center">
                <LoadingSpinner size="lg" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 p-6">
            <div className="max-w-7xl mx-auto space-y-8">{/*Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                            <Shield className="text-blue-500" size={36} />
                            Admin Dashboard
                        </h1>
                        <p className="text-gray-400">System Overview & User Management</p>
                    </div>
                    <Badge variant="success">
                        <Activity size={14} className="mr-1" />
                        System {stats.systemStatus}
                    </Badge>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card hover>
                        <CardBody className="flex items-center gap-4">
                            <div className="p-3 bg-blue-500/20 rounded-lg">
                                <Users size={32} className="text-blue-400" />
                            </div>
                            <div>
                                <p className="text-gray-400 text-sm">Total Users</p>
                                <p className="text-3xl font-bold text-white">{stats.totalPeople}</p>
                            </div>
                        </CardBody>
                    </Card>

                    <Card hover>
                        <CardBody className="flex items-center gap-4">
                            <div className="p-3 bg-green-500/20 rounded-lg">
                                <Camera size={32} className="text-green-400" />
                            </div>
                            <div>
                                <p className="text-gray-400 text-sm">Identifications (24h)</p>
                                <p className="text-3xl font-bold text-white">{stats.recentIdentifications}</p>
                            </div>
                        </CardBody>
                    </Card>

                    <Card hover>
                        <CardBody className="flex items-center gap-4">
                            <div className="p-3 bg-purple-500/20 rounded-lg">
                                <TrendingUp size={32} className="text-purple-400" />
                            </div>
                            <div>
                                <p className="text-gray-400 text-sm">Success Rate</p>
                                <p className="text-3xl font-bold text-white">98.5%</p>
                            </div>
                        </CardBody>
                    </Card>
                </div>

                {/* Quick Actions */}
                <Card>
                    <CardHeader>
                        <h2 className="text-xl font-bold text-white">Quick Actions</h2>
                    </CardHeader>
                    <CardBody>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <Link href="/identify">
                                <Button variant="primary" className="w-full justify-start">
                                    <Video size={20} />
                                    Start Real-time Identification
                                </Button>
                            </Link>
                            <Link href="/enroll">
                                <Button variant="secondary" className="w-full justify-start">
                                    <UserPlus size={20} />
                                    Enroll New Person
                                </Button>
                            </Link>
                        </div>
                    </CardBody>
                </Card>

                {/* User Management Table */}
                <Card>
                    <CardHeader>
                        <div className="flex justify-between items-center">
                            <h2 className="text-xl font-bold text-white">User Management</h2>
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
                                <input
                                    type="text"
                                    placeholder="Search users..."
                                    className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </div>
                        </div>
                    </CardHeader>
                    <CardBody className="p-0 overflow-hidden">
                        <table className="w-full text-left text-gray-300">
                            <thead className="bg-gray-800 text-gray-400 uppercase text-xs">
                                <tr>
                                    <th className="px-6 py-4">User</th>
                                    <th className="px-6 py-4">Role</th>
                                    <th className="px-6 py-4">Status</th>
                                    <th className="px-6 py-4 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-800">
                                {filteredUsers.map((user, idx) => (
                                    <tr key={idx} className="hover:bg-gray-800/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                                                    {user.username[0].toUpperCase()}
                                                </div>
                                                <div>
                                                    <div className="font-medium text-white">{user.full_name}</div>
                                                    <div className="text-sm text-gray-500">{user.email}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${user.role === 'Admin' ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400'
                                                }`}>
                                                {user.role}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400">
                                                Active
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex justify-end gap-2">
                                                <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors">
                                                    <Edit size={18} />
                                                </button>
                                                <button className="p-2 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-lg transition-colors">
                                                    <Trash2 size={18} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </CardBody>
                </Card>
            </div>
        </div>
    );
}
