import React, { useEffect, useState } from 'react';
import { Users, UserCheck, Activity, Database, UserPlus, Settings } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';

interface AdminDashboardProps {
    onNavigate: (page: string) => void;
}

interface Stats {
    totalUsers: number;
    activeUsers: number;
    totalFaces: number;
    recentActivity: number;
}

export function AdminDashboard({ onNavigate }: AdminDashboardProps) {
    const [stats, setStats] = useState<Stats>({
        totalUsers: 0,
        activeUsers: 0,
        totalFaces: 0,
        recentActivity: 0
    });

    useEffect(() => {
        // TODO: Fetch actual stats from API
        // For now, using mock data
        setStats({
            totalUsers: 12,
            activeUsers: 8,
            totalFaces: 45,
            recentActivity: 23
        });
    }, []);

    return (
        <div className="max-w-7xl mx-auto p-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">Admin Dashboard</h1>
                <p className="text-gray-400">Manage users and system settings</p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <Card className="p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-400 mb-1">Total Users</p>
                            <p className="text-3xl font-bold text-white">{stats.totalUsers}</p>
                        </div>
                        <div className="bg-blue-500/20 p-3 rounded-full">
                            <Users className="w-6 h-6 text-blue-500" />
                        </div>
                    </div>
                </Card>

                <Card className="p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-400 mb-1">Active Users</p>
                            <p className="text-3xl font-bold text-white">{stats.activeUsers}</p>
                        </div>
                        <div className="bg-green-500/20 p-3 rounded-full">
                            <UserCheck className="w-6 h-6 text-green-500" />
                        </div>
                    </div>
                </Card>

                <Card className="p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-400 mb-1">Enrolled Faces</p>
                            <p className="text-3xl font-bold text-white">{stats.totalFaces}</p>
                        </div>
                        <div className="bg-purple-500/20 p-3 rounded-full">
                            <Database className="w-6 h-6 text-purple-500" />
                        </div>
                    </div>
                </Card>

                <Card className="p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-400 mb-1">Recent Activity</p>
                            <p className="text-3xl font-bold text-white">{stats.recentActivity}</p>
                        </div>
                        <div className="bg-orange-500/20 p-3 rounded-full">
                            <Activity className="w-6 h-6 text-orange-500" />
                        </div>
                    </div>
                </Card>
            </div>

            {/* Quick Actions */}
            <Card className="p-6 mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Button
                        variant="primary"
                        className="flex items-center justify-center"
                        onClick={() => onNavigate('user-management')}
                    >
                        <Users className="w-5 h-5 mr-2" />
                        Manage Users
                    </Button>

                    <Button
                        variant="secondary"
                        className="flex items-center justify-center"
                        onClick={() => onNavigate('people')}
                    >
                        <UserPlus className="w-5 h-5 mr-2" />
                        View All People
                    </Button>

                    <Button
                        variant="secondary"
                        className="flex items-center justify-center"
                        onClick={() => alert('System settings coming soon')}
                    >
                        <Settings className="w-5 h-5 mr-2" />
                        System Settings
                    </Button>
                </div>
            </Card>

            {/* Recent Activity */}
            <Card className="p-6">
                <h2 className="text-xl font-semibold text-white mb-4">Recent Activity</h2>
                <div className="space-y-3">
                    {[1, 2, 3, 4, 5].map((i) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                                    U{i}
                                </div>
                                <div>
                                    <p className="text-white font-medium">User {i} registered</p>
                                    <p className="text-sm text-gray-400">{i} hours ago</p>
                                </div>
                            </div>
                            <Activity className="w-5 h-5 text-gray-500" />
                        </div>
                    ))}
                </div>
            </Card>
        </div>
    );
}
