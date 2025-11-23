'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Card, { CardBody, CardHeader } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/Loading';
import { people, logs } from '@/lib/api';
import { Users, Camera, Activity, TrendingUp, Video, UserPlus, Home } from 'lucide-react';
import Link from 'next/link';

export default function MainDashboard() {
    const [stats, setStats] = useState({
        totalPeople: 0,
        recentIdentifications: 0,
        systemStatus: 'operational',
    });
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        const userStr = localStorage.getItem('user');
        if (!userStr) {
            router.push('/');
            return;
        }

        fetchData();
    }, [router]);

    const fetchData = async () => {
        try {
            // Fetch people count
            const peopleRes = await people.list();
            const totalPeople = peopleRes.data.length;

            // Fetch recent logs
            const logsRes = await logs.list();
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
        } catch (err) {
            console.error('Failed to fetch dashboard data:', err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-950 flex items-center justify-center">
                <LoadingSpinner size="lg" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 p-6">
            <div className="max-w-7xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                            <Home className="text-blue-500" size={36} />
                            Dashboard
                        </h1>
                        <p className="text-gray-400">System Overview</p>
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
            </div>
        </div>
    );
}
