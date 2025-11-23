'use client';
import { useRef, useState, useEffect, useCallback } from 'react';
import Webcam from 'react-webcam';
import { identify } from '@/lib/api';
import Card, { CardBody, CardHeader } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { Camera, Activity, UserCheck, Settings, Play, Pause, RefreshCw } from 'lucide-react';

export default function IdentifyPage() {
    const webcamRef = useRef<Webcam>(null);
    const [matches, setMatches] = useState<any[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isAutoMode, setIsAutoMode] = useState(true);
    const [captureInterval, setCaptureInterval] = useState(1000);
    const [stats, setStats] = useState({
        totalIdentifications: 0,
        successfulMatches: 0,
        lastIdentified: null as any
    });

    const capture = useCallback(async () => {
        if (webcamRef.current && !isProcessing) {
            const imageSrc = webcamRef.current.getScreenshot();
            if (imageSrc) {
                setIsProcessing(true);
                try {
                    const res = await fetch(imageSrc);
                    const blob = await res.blob();
                    const formData = new FormData();
                    formData.append('image', blob, 'capture.jpg');

                    const response = await identify.identifyFace(formData);
                    setMatches(response.data.faces);

                    // Update stats
                    setStats(prev => ({
                        totalIdentifications: prev.totalIdentifications + 1,
                        successfulMatches: response.data.faces.length > 0 ? prev.successfulMatches + 1 : prev.successfulMatches,
                        lastIdentified: response.data.faces[0] || null
                    }));
                } catch (err) {
                    console.error(err);
                } finally {
                    setIsProcessing(false);
                }
            }
        }
    }, [isProcessing]);

    useEffect(() => {
        if (!isAutoMode) return;
        const interval = setInterval(capture, captureInterval);
        return () => clearInterval(interval);
    }, [capture, isAutoMode, captureInterval]);

    const successRate = stats.totalIdentifications > 0
        ? Math.round((stats.successfulMatches / stats.totalIdentifications) * 100)
        : 0;

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-4xl font-bold text-white mb-2">Face Recognition</h1>
                        <p className="text-gray-400">Real-time identification system</p>
                    </div>
                    <div className="flex items-center gap-2">
                        {isAutoMode && (
                            <div className="flex items-center gap-2 px-4 py-2 bg-green-500/20 rounded-lg border border-green-500/50">
                                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                <span className="text-green-400 text-sm font-medium">LIVE</span>
                            </div>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Camera Section */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Camera View */}
                        <Card>
                            <CardBody className="p-0">
                                <div className="relative bg-black rounded-lg overflow-hidden aspect-video">
                                    <Webcam
                                        audio={false}
                                        ref={webcamRef}
                                        screenshotFormat="image/jpeg"
                                        className="w-full h-full object-cover"
                                    />

                                    {/* Bounding Boxes */}
                                    {matches.map((match, idx) => {
                                        const { bbox } = match;
                                        if (!bbox) return null;

                                        const style = {
                                            left: `${bbox.Left * 100}%`,
                                            top: `${bbox.Top * 100}%`,
                                            width: `${bbox.Width * 100}%`,
                                            height: `${bbox.Height * 100}%`,
                                        };
                                        return (
                                            <div
                                                key={idx}
                                                className="absolute border-4 border-green-500 shadow-lg shadow-green-500/50 transition-all"
                                                style={style}
                                            >
                                                <div className="absolute -top-8 left-0 bg-green-500 text-black px-3 py-1 rounded-md text-sm font-bold backdrop-blur-sm">
                                                    <div className="flex flex-col">
                                                        <span className="text-lg">{match.user_name}</span>
                                                        <span className="text-xs font-normal opacity-90">Confidence: {Math.round(match.confidence * 100)}%</span>
                                                        {match.gender && <span className="text-xs font-normal opacity-90">Gender: {match.gender}</span>}
                                                        {match.birth_year && <span className="text-xs font-normal opacity-90">Year: {match.birth_year}</span>}
                                                        {match.hometown && <span className="text-xs font-normal opacity-90">Hometown: {match.hometown}</span>}
                                                        {match.residence && <span className="text-xs font-normal opacity-90">Residence: {match.residence}</span>}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}

                                    {/* Processing Overlay */}
                                    {isProcessing && (
                                        <div className="absolute bottom-4 right-4 bg-blue-500/80 backdrop-blur-sm text-white px-4 py-2 rounded-lg flex items-center gap-2">
                                            <RefreshCw className="animate-spin" size={16} />
                                            <span className="text-sm font-medium">Processing...</span>
                                        </div>
                                    )}
                                </div>
                            </CardBody>
                        </Card>

                        {/* Controls */}
                        <Card>
                            <CardHeader>
                                <div className="flex items-center gap-2">
                                    <Settings size={20} className="text-blue-400" />
                                    <h3 className="text-lg font-bold text-white">Controls</h3>
                                </div>
                            </CardHeader>
                            <CardBody>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm text-gray-400 mb-2 block">Mode</label>
                                        <Button
                                            variant={isAutoMode ? 'primary' : 'secondary'}
                                            onClick={() => setIsAutoMode(!isAutoMode)}
                                            className="w-full"
                                        >
                                            {isAutoMode ? <Pause size={18} /> : <Play size={18} />}
                                            {isAutoMode ? 'Auto Mode' : 'Manual Mode'}
                                        </Button>
                                    </div>
                                    <div>
                                        <label className="text-sm text-gray-400 mb-2 block">Manual Capture</label>
                                        <Button
                                            variant="secondary"
                                            onClick={capture}
                                            disabled={isProcessing}
                                            className="w-full"
                                        >
                                            <Camera size={18} />
                                            Capture Now
                                        </Button>
                                    </div>
                                    {isAutoMode && (
                                        <div className="sm:col-span-2">
                                            <label className="text-sm text-gray-400 mb-2 block">
                                                Capture Interval: {captureInterval}ms
                                            </label>
                                            <input
                                                type="range"
                                                min="500"
                                                max="3000"
                                                step="100"
                                                value={captureInterval}
                                                onChange={(e) => setCaptureInterval(Number(e.target.value))}
                                                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                                            />
                                        </div>
                                    )}
                                </div>
                            </CardBody>
                        </Card>
                    </div>

                    {/* Stats Sidebar */}
                    <div className="space-y-6">
                        {/* Live Stats */}


                        {/* Last Identified */}
                        {stats.lastIdentified && (
                            <Card>
                                <CardHeader>
                                    <div className="flex items-center gap-2">
                                        <UserCheck size={20} className="text-green-400" />
                                        <h3 className="text-lg font-bold text-white">Last Identified</h3>
                                    </div>
                                </CardHeader>
                                <CardBody>
                                    <div className="flex items-center gap-4">
                                        <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold text-2xl">
                                            {stats.lastIdentified.user_name[0]}
                                        </div>
                                        <div>
                                            <p className="text-white font-bold text-lg">{stats.lastIdentified.user_name}</p>
                                            <p className="text-gray-400 text-sm">
                                                Confidence: {Math.round(stats.lastIdentified.confidence * 100)}%
                                            </p>
                                        </div>
                                    </div>
                                </CardBody>
                            </Card>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
