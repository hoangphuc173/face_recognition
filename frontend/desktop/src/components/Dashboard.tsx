import { useEffect, useState } from 'react';
import Card, { CardBody, CardHeader } from './ui/Card';
import Button from './ui/Button';
import Badge from './ui/Badge';
import { LoadingSpinner } from './ui/Loading';
import { people, logs } from '../config/api';
import { Users, Camera, Activity, TrendingUp, Video, UserPlus } from 'lucide-react';

interface DashboardProps {
    onNavigate: (page: string) => void;
}

export default function Dashboard({ onNavigate }: DashboardProps) {
    const [stats, setStats] = useState({
        totalPeople: 0,
        recentIdentifications: 0,
        systemStatus: 'operational',
    });
    const [recentLogs, setRecentLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            // Fetch people count
            const peopleRes = await people.list();
            const totalPeople = peopleRes.data.length;

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

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <LoadingSpinner size="lg" />
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-white mb-2">Dashboard</h1>
                    <p className="text-gray-400">Welcome back! Here's what's happening.</p>
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
                            <p className="text-gray-400 text-sm">Total People</p>
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
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <Button variant="primary" className="w-full justify-start" onClick={() => onNavigate('identify')}>
                            <Video size={20} />
                            Start Real-time Identification
                        </Button>
                        <Button variant="secondary" className="w-full justify-start" onClick={() => onNavigate('enroll')}>
                            <UserPlus size={20} />
                            Enroll New Face
                        </Button>
                        <Button variant="secondary" className="w-full justify-start" onClick={() => onNavigate('people')}>
                            <Users size={20} />
                            Manage People
                        </Button>
                    </div>
                </CardBody>
            </Card>

            {/* Recent Activity */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold text-white">Recent Activity</h2>
                        <Button variant="ghost" size="sm" onClick={() => onNavigate('logs')}>View All</Button>
                    </div>
                </CardHeader>
                <CardBody>
                    {recentLogs.length === 0 ? (
                        <div className="text-center py-8 text-gray-400">
                            <Activity size={48} className="mx-auto mb-4 opacity-50" />
                            <p>No recent activity</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {recentLogs.map((log, idx) => (
                                <div
                                    key={idx}
                                    className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg hover:bg-gray-800 transition-colors"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                            <Users size={20} className="text-white" />
                                        </div>
                                        <div>
                                            <p className="text-white font-medium">{log.UserId}</p>
                                            <p className="text-gray-400 text-sm">
                                                {new Date(log.Timestamp * 1000).toLocaleString()}
                                            </p>
                                        </div>
                                    </div>
                                    <Badge variant={parseFloat(log.Confidence) > 95 ? 'success' : 'warning'}>
                                        {Math.round(parseFloat(log.Confidence))}% confidence
                                    </Badge>
                                </div>
                            ))}
                        </div>
                    )}
                </CardBody>
            </Card>
        </div>
    );
}
