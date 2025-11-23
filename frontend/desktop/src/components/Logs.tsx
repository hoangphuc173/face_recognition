import { useEffect, useState } from 'react';
import Card, { CardBody, CardHeader } from './ui/Card';
import Badge from './ui/Badge';
import { SkeletonTable } from './ui/Loading';
import { logs } from '../config/api';
import { Calendar, Filter, Download, User, TrendingUp } from 'lucide-react';

export default function Logs() {
    const [allLogs, setAllLogs] = useState<any[]>([]);
    const [filteredLogs, setFilteredLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchLogs();
    }, []);

    useEffect(() => {
        // Filter logs based on search term
        if (searchTerm) {
            const filtered = allLogs.filter((log) =>
                log.UserId.toLowerCase().includes(searchTerm.toLowerCase())
            );
            setFilteredLogs(filtered);
        } else {
            setFilteredLogs(allLogs);
        }
    }, [searchTerm, allLogs]);

    const fetchLogs = async () => {
        try {
            const res = await logs.list();
            const sortedLogs = res.data.sort((a: any, b: any) => b.Timestamp - a.Timestamp);
            setAllLogs(sortedLogs);
            setFilteredLogs(sortedLogs);
        } catch (err) {
            console.error('Failed to fetch logs:', err);
        } finally {
            setLoading(false);
        }
    };

    const exportToCSV = () => {
        const headers = ['Date', 'Time', 'User ID', 'Confidence', 'Action'];
        const rows = filteredLogs.map((log) => {
            const date = new Date(log.Timestamp * 1000);
            return [
                date.toLocaleDateString(),
                date.toLocaleTimeString(),
                log.UserId,
                `${Math.round(parseFloat(log.Confidence))}%`,
                log.Action,
            ];
        });

        const csvContent = [headers, ...rows].map((row) => row.join(',')).join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `access_logs_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
    };

    const getConfidenceBadge = (confidence: string) => {
        const conf = parseFloat(confidence);
        if (conf >= 95) return <Badge variant="success">{Math.round(conf)}%</Badge>;
        if (conf >= 85) return <Badge variant="warning">{Math.round(conf)}%</Badge>;
        return <Badge variant="danger">{Math.round(conf)}%</Badge>;
    };

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Access Logs</h1>
                    <p className="text-gray-400">View all identification records</p>
                </div>
            </div>

            {/* Filters & Actions */}
            <Card>
                <CardBody>
                    <div className="flex flex-col md:flex-row gap-4 items-end">
                        <div className="flex-1">
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Search by User ID
                            </label>
                            <div className="relative">
                                <input
                                    type="text"
                                    placeholder="Filter by user ID..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="w-full px-4 py-2.5 pl-10 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <Filter className="absolute left-3 top-3 text-gray-500" size={18} />
                            </div>
                        </div>

                        <button
                            onClick={exportToCSV}
                            disabled={filteredLogs.length === 0}
                            className="flex items-center gap-2 px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <Download size={18} />
                            Export CSV
                        </button>
                    </div>
                </CardBody>
            </Card>

            {/* Stats Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card hover>
                    <CardBody className="flex items-center gap-4">
                        <div className="p-3 bg-blue-500/20 rounded-lg">
                            <Calendar size={24} className="text-blue-400" />
                        </div>
                        <div>
                            <p className="text-gray-400 text-sm">Total Logs</p>
                            <p className="text-2xl font-bold text-white">{filteredLogs.length}</p>
                        </div>
                    </CardBody>
                </Card>

                <Card hover>
                    <CardBody className="flex items-center gap-4">
                        <div className="p-3 bg-green-500/20 rounded-lg">
                            <User size={24} className="text-green-400" />
                        </div>
                        <div>
                            <p className="text-gray-400 text-sm">Unique Users</p>
                            <p className="text-2xl font-bold text-white">
                                {new Set(filteredLogs.map((log) => log.UserId)).size}
                            </p>
                        </div>
                    </CardBody>
                </Card>

                <Card hover>
                    <CardBody className="flex items-center gap-4">
                        <div className="p-3 bg-purple-500/20 rounded-lg">
                            <TrendingUp size={24} className="text-purple-400" />
                        </div>
                        <div>
                            <p className="text-gray-400 text-sm">Avg Confidence</p>
                            <p className="text-2xl font-bold text-white">
                                {filteredLogs.length > 0
                                    ? Math.round(
                                        filteredLogs.reduce((sum, log) => sum + parseFloat(log.Confidence), 0) /
                                        filteredLogs.length
                                    )
                                    : 0}
                                %
                            </p>
                        </div>
                    </CardBody>
                </Card>
            </div>

            {/* Logs Table */}
            <Card>
                <CardHeader>
                    <h2 className="text-xl font-bold text-white">
                        {searchTerm ? `Search Results (${filteredLogs.length})` : 'All Logs'}
                    </h2>
                </CardHeader>
                <CardBody>
                    {loading ? (
                        <SkeletonTable rows={10} />
                    ) : filteredLogs.length === 0 ? (
                        <div className="text-center py-12 text-gray-400">
                            <Calendar size={48} className="mx-auto mb-4 opacity-50" />
                            <p className="text-lg font-medium">No logs found</p>
                            <p className="text-sm">
                                {searchTerm ? 'Try a different search term' : 'No identification records yet'}
                            </p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-gray-700">
                                        <th className="text-left p-4 text-gray-400 font-medium">Date & Time</th>
                                        <th className="text-left p-4 text-gray-400 font-medium">User ID</th>
                                        <th className="text-left p-4 text-gray-400 font-medium">Action</th>
                                        <th className="text-left p-4 text-gray-400 font-medium">Confidence</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredLogs.map((log, idx) => (
                                        <tr
                                            key={idx}
                                            className="border-b border-gray-800 hover:bg-gray-800/50 transition-colors"
                                        >
                                            <td className="p-4 text-gray-300">
                                                <div className="flex flex-col">
                                                    <span>{new Date(log.Timestamp * 1000).toLocaleDateString()}</span>
                                                    <span className="text-sm text-gray-500">
                                                        {new Date(log.Timestamp * 1000).toLocaleTimeString()}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="p-4">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                                        <User size={16} className="text-white" />
                                                    </div>
                                                    <span className="text-white font-medium">{log.UserId}</span>
                                                </div>
                                            </td>
                                            <td className="p-4">
                                                <Badge variant="info">{log.Action}</Badge>
                                            </td>
                                            <td className="p-4">{getConfidenceBadge(log.Confidence)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardBody>
            </Card>
        </div>
    );
}
