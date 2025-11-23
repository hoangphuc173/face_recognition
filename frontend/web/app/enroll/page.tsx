'use client';
import { useState, useRef, useEffect, useCallback } from 'react';
import Webcam from 'react-webcam';
import Card, { CardBody, CardHeader } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { enroll } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { Upload, Camera, CheckCircle, AlertCircle, UserPlus, X, Sparkles } from 'lucide-react';

export default function EnrollPage() {
    const [username, setUsername] = useState('');
    const [fullName, setFullName] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [preview, setPreview] = useState<string | null>(null);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [useWebcam, setUseWebcam] = useState(false);
    const [faceQuality, setFaceQuality] = useState<'good' | 'warning' | 'none'>('none');
    const [autoCapture, setAutoCapture] = useState(true);
    const [countdown, setCountdown] = useState<number | null>(null);

    const router = useRouter();
    const webcamRef = useRef<Webcam>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const detectionInterval = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        const userStr = localStorage.getItem('user');
        if (userStr) {
            try {
                const user = JSON.parse(userStr);
                setUsername(user.username);
                setFullName(user.full_name || user.username);
            } catch (e) {
                console.error('Failed to parse user from localStorage');
            }
        }
    }, []);

    // Simple face detection
    const detectFace = useCallback(async () => {
        if (!webcamRef.current || !useWebcam) return;

        const imageSrc = webcamRef.current.getScreenshot();
        if (!imageSrc) return;

        try {
            const img = new Image();
            img.src = imageSrc;
            await new Promise((resolve) => { img.onload = resolve; });

            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            if (!ctx) return;

            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);

            const centerX = img.width / 2;
            const centerY = img.height / 2;
            const regionSize = Math.min(img.width, img.height) * 0.3;

            const imageData = ctx.getImageData(
                centerX - regionSize / 2,
                centerY - regionSize / 2,
                regionSize,
                regionSize
            );

            let totalBrightness = 0;
            let variance = 0;
            const pixels = imageData.data;

            for (let i = 0; i < pixels.length; i += 4) {
                const brightness = (pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3;
                totalBrightness += brightness;
            }

            const avgBrightness = totalBrightness / (pixels.length / 4);

            for (let i = 0; i < pixels.length; i += 4) {
                const brightness = (pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3;
                variance += Math.pow(brightness - avgBrightness, 2);
            }

            const stdDev = Math.sqrt(variance / (pixels.length / 4));

            const hasGoodContrast = stdDev > 20;
            const hasGoodBrightness = avgBrightness > 60 && avgBrightness < 200;

            if (hasGoodContrast && hasGoodBrightness) {
                setFaceQuality('good');
                if (autoCapture && !countdown) {
                    setCountdown(3);
                }
            } else if (hasGoodContrast || avgBrightness > 40) {
                setFaceQuality('warning');
                setCountdown(null);
            } else {
                setFaceQuality('none');
                setCountdown(null);
            }
        } catch (err) {
            console.error('Face detection error:', err);
        }
    }, [useWebcam, autoCapture, countdown]);

    // Countdown logic
    useEffect(() => {
        if (countdown === null) return;

        if (countdown === 0) {
            if (webcamRef.current) {
                const imageSrc = webcamRef.current.getScreenshot();
                if (imageSrc) {
                    // Properly convert base64 data URL to binary File
                    const base64Data = imageSrc.split(',')[1];
                    const binaryString = atob(base64Data);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    const blob = new Blob([bytes], { type: 'image/jpeg' });
                    const capturedFile = new File([blob], 'webcam-capture.jpg', { type: 'image/jpeg' });
                    setFile(capturedFile);
                    setPreview(imageSrc);
                    setUseWebcam(false);
                }
            }
            setCountdown(null);
            return;
        }

        const timer = setTimeout(() => {
            setCountdown(countdown - 1);
        }, 1000);

        return () => clearTimeout(timer);
    }, [countdown]);

    // Start detection
    useEffect(() => {
        if (useWebcam) {
            detectionInterval.current = setInterval(detectFace, 500);
        } else {
            if (detectionInterval.current) {
                clearInterval(detectionInterval.current);
            }
            setFaceQuality('none');
            setCountdown(null);
        }

        return () => {
            if (detectionInterval.current) {
                clearInterval(detectionInterval.current);
            }
        };
    }, [useWebcam, detectFace]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            setFile(selectedFile);
            setPreview(URL.createObjectURL(selectedFile));
            setUseWebcam(false);
        }
    };

    const capturePhoto = () => {
        if (webcamRef.current) {
            const imageSrc = webcamRef.current.getScreenshot();
            if (imageSrc) {
                // Properly convert base64 data URL to binary File  
                const base64Data = imageSrc.split(',')[1];
                const binaryString = atob(base64Data);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                const blob = new Blob([bytes], { type: 'image/jpeg' });
                const capturedFile = new File([blob], 'webcam-capture.jpg', { type: 'image/jpeg' });
                setFile(capturedFile);
                setPreview(imageSrc);
                setUseWebcam(false);
            }
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setMessage(null);

        if (!file || !username) {
            setMessage({ type: 'error', text: 'Please provide an image and ensure you are logged in' });
            return;
        }

        console.log('Enrolling:', { username, fileSize: file!.size });

        const formData = new FormData();
        formData.append('name', fullName || username);
        formData.append('user_id', username);
        formData.append('file', file!);

        try {
            const response = await enroll.enrollUser(formData);
            console.log('Success:', response);
            setMessage({ type: 'success', text: '✅ Person enrolled successfully!' });

            setTimeout(() => {
                router.push('/people');
            }, 2000);
        } catch (err: any) {
            console.error('Error:', err);
            const detail = err.response?.data?.detail;
            const errorDetail = typeof detail === 'object'
                ? JSON.stringify(detail)
                : (detail || err.message || 'Unknown error');

            console.log('Error detail:', errorDetail);

            let errorMessage = '❌ Enrollment failed: ';

            if (typeof errorDetail === 'string' && errorDetail.toLowerCase().includes('no face')) {
                errorMessage += 'No face detected in image. Please ensure:\n• Face is clearly visible\n• Good lighting\n• Face is front-facing\n• No obstructions (glasses, mask, etc.)';
            } else if (typeof errorDetail === 'string' && (errorDetail.toLowerCase().includes('401') || errorDetail.toLowerCase().includes('unauthorized'))) {
                errorMessage += 'Please log in again.';
            } else {
                errorMessage += errorDetail;
            }

            setMessage({
                type: 'error',
                text: errorMessage,
            });
        } finally {
            setIsLoading(false);
        }
    };

    const statusMessages = {
        none: { text: '👤 Position your face in the circle', color: 'text-gray-400' },
        warning: { text: '⚠️ Move closer or improve lighting', color: 'text-yellow-400' },
        good: { text: '✅ Perfect! Hold steady...', color: 'text-green-400' }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 p-6">
            <div className="max-w-4xl mx-auto space-y-6">
                <div className="text-center">
                    <div className="inline-flex items-center gap-2 mb-4">
                        <Sparkles className="text-purple-400" size={32} />
                        <h1 className="text-4xl font-bold text-white">Smart Enrollment</h1>
                    </div>
                    <p className="text-gray-400">AI-powered face detection for easy enrollment</p>
                </div>

                <Card>
                    <CardBody className="p-8">
                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
                                <p className="text-gray-400 text-sm mb-1">Enrolling as:</p>
                                <p className="text-xl font-bold text-white">{fullName || username || 'Loading...'}</p>
                                {fullName && fullName !== username && (
                                    <p className="text-sm text-gray-500">({username})</p>
                                )}
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-3">
                                    Face Photo
                                </label>

                                <div className="grid grid-cols-2 gap-4 mb-4">
                                    <Button
                                        type="button"
                                        variant={!useWebcam ? 'primary' : 'outline'}
                                        onClick={() => {
                                            setUseWebcam(false);
                                            fileInputRef.current?.click();
                                        }}
                                    >
                                        <Upload size={20} />
                                        Upload Photo
                                    </Button>
                                    <Button
                                        type="button"
                                        variant={useWebcam ? 'primary' : 'outline'}
                                        onClick={() => {
                                            setUseWebcam(!useWebcam);
                                            setPreview(null);
                                        }}
                                    >
                                        <Camera size={20} />
                                        Use Camera
                                    </Button>
                                </div>

                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="image/*"
                                    onChange={handleFileChange}
                                    className="hidden"
                                />

                                {useWebcam && (
                                    <div className="space-y-4">
                                        <div className="relative rounded-xl overflow-hidden border-2 border-gray-700 bg-black aspect-video">
                                            <Webcam
                                                audio={false}
                                                ref={webcamRef}
                                                screenshotFormat="image/jpeg"
                                                className="w-full h-full object-cover"
                                                videoConstraints={{ facingMode: "user" }}
                                            />

                                            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                                <div className={`w-64 h-64 rounded-full border-4 transition-all duration-300 ${faceQuality === 'good' ? 'border-green-500 shadow-[0_0_30px_rgba(34,197,94,0.5)]' :
                                                    faceQuality === 'warning' ? 'border-yellow-500 shadow-[0_0_20px_rgba(234,179,8,0.3)]' :
                                                        'border-gray-500/50'
                                                    }`}>
                                                    {countdown !== null && countdown > 0 && (
                                                        <div className="absolute inset-0 flex items-center justify-center">
                                                            <div className="text-8xl font-bold text-white animate-pulse">
                                                                {countdown}
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>

                                            <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-black/70 backdrop-blur-sm px-4 py-2 rounded-full">
                                                <p className={`text-sm font-medium ${statusMessages[faceQuality].color}`}>
                                                    {statusMessages[faceQuality].text}
                                                </p>
                                            </div>

                                            <div className="absolute bottom-4 left-4 bg-black/70 backdrop-blur-sm px-3 py-2 rounded-lg">
                                                <label className="flex items-center gap-2 text-sm text-white cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        checked={autoCapture}
                                                        onChange={(e) => setAutoCapture(e.target.checked)}
                                                        className="rounded"
                                                    />
                                                    Auto-capture
                                                </label>
                                            </div>
                                        </div>

                                        {!autoCapture && (
                                            <Button
                                                type="button"
                                                onClick={capturePhoto}
                                                variant="secondary"
                                                className="w-full"
                                                disabled={faceQuality !== 'good'}
                                            >
                                                <Camera size={20} />
                                                {faceQuality === 'good' ? 'Capture Photo' : 'Wait for good detection...'}
                                            </Button>
                                        )}
                                    </div>
                                )}

                                {preview && !useWebcam && (
                                    <div className="mt-4 space-y-3">
                                        <div className="relative rounded-xl overflow-hidden border-2 border-green-500">
                                            <img src={preview} alt="Preview" className="w-full" />
                                            <button
                                                type="button"
                                                onClick={() => {
                                                    setFile(null);
                                                    setPreview(null);
                                                    if (fileInputRef.current) fileInputRef.current.value = '';
                                                }}
                                                className="absolute top-2 right-2 p-2 bg-red-500 hover:bg-red-600 rounded-full text-white transition-colors"
                                            >
                                                <X size={20} />
                                            </button>
                                        </div>
                                        <div className="flex items-center gap-2 text-green-400 text-sm">
                                            <CheckCircle size={16} />
                                            Image ready for enrollment
                                        </div>
                                    </div>
                                )}
                            </div>

                            {message && (
                                <div className={`flex items-start gap-3 p-4 rounded-lg ${message.type === 'success'
                                    ? 'bg-green-500/10 border border-green-500/50 text-green-400'
                                    : 'bg-red-500/10 border border-red-500/50 text-red-400'
                                    }`}>
                                    <div className="flex-shrink-0 mt-0.5">
                                        {message.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
                                    </div>
                                    <span className="text-sm">{message.text}</span>
                                </div>
                            )}

                            <Button
                                type="submit"
                                variant="primary"
                                className="w-full"
                                isLoading={isLoading}
                                disabled={!file || !username}
                            >
                                {!isLoading && <UserPlus size={20} />}
                                Enroll Person
                            </Button>
                        </form>
                    </CardBody>
                </Card>

                <Card>
                    <CardHeader>
                        <h3 className="text-lg font-bold text-white">💡 Tips for Best Results</h3>
                    </CardHeader>
                    <CardBody>
                        <ul className="space-y-2 text-gray-300 text-sm">
                            <li className="flex items-start gap-2">
                                <CheckCircle size={16} className="text-green-400 mt-0.5 flex-shrink-0" />
                                Position face in circle - system auto-detects
                            </li>
                            <li className="flex items-start gap-2">
                                <CheckCircle size={16} className="text-green-400 mt-0.5 flex-shrink-0" />
                                Ensure good lighting on face
                            </li>
                            <li className="flex items-start gap-2">
                                <CheckCircle size={16} className="text-green-400 mt-0.5 flex-shrink-0" />
                                Look directly at camera
                            </li>
                            <li className="flex items-start gap-2">
                                <CheckCircle size={16} className="text-green-400 mt-0.5 flex-shrink-0" />
                                Remove glasses/masks if possible
                            </li>
                        </ul>
                    </CardBody>
                </Card>
            </div>
        </div>
    );
}
