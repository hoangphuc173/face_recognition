import React, { useRef, useEffect, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera, X, Check, AlertCircle } from 'lucide-react';
import Button from './ui/Button';
import { FaceDetection } from '@mediapipe/face_detection';
import { Camera as CameraUtils } from '@mediapipe/camera_utils';

interface FaceCaptureProps {
    onCapture: (imageData: string, qualityScore: number) => void;
    onCancel: () => void;
    minQualityScore?: number;
    autoCapture?: boolean;
}

interface QualityMetrics {
    hasFace: boolean;
    brightness: number;
    isBlurry: boolean;
    faceSize: number;
    score: number;
}

export function FaceCapture({
    onCapture,
    onCancel,
    minQualityScore = 70,
    autoCapture = true
}: FaceCaptureProps) {
    const webcamRef = useRef<Webcam>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [quality, setQuality] = useState<QualityMetrics>({
        hasFace: false,
        brightness: 0,
        isBlurry: false,
        faceSize: 0,
        score: 0
    });
    const [countdown, setCountdown] = useState<number | null>(null);
    const [message, setMessage] = useState('Position your face in the frame');
    const [isProcessing, setIsProcessing] = useState(false);
    const faceDetectionRef = useRef<FaceDetection | null>(null);

    // Initialize MediaPipe Face Detection
    useEffect(() => {
        const faceDetection = new FaceDetection({
            locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/${file}`;
            }
        });

        faceDetection.setOptions({
            model: 'short',
            minDetectionConfidence: 0.5
        });

        faceDetection.onResults((results) => {
            if (canvasRef.current && webcamRef.current?.video) {
                const canvas = canvasRef.current;
                const video = webcamRef.current.video;
                const ctx = canvas.getContext('2d');

                if (ctx) {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;

                    // Draw video frame
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                    // Analyze quality
                    const metrics = analyzeQuality(results, canvas, ctx);
                    setQuality(metrics);

                    // Draw overlay
                    drawOverlay(ctx, canvas, metrics, results);

                    // Update message
                    updateMessage(metrics);

                    // Auto-capture logic
                    if (autoCapture && metrics.score >= minQualityScore && !isProcessing) {
                        startCountdown();
                    }
                }
            }
        });

        faceDetectionRef.current = faceDetection;

        return () => {
            faceDetection.close();
        };
    }, [autoCapture, minQualityScore, isProcessing]);

    // Process video stream
    useEffect(() => {
        if (webcamRef.current?.video && faceDetectionRef.current) {
            const camera = new CameraUtils(webcamRef.current.video, {
                onFrame: async () => {
                    if (faceDetectionRef.current && webcamRef.current?.video) {
                        await faceDetectionRef.current.send({ image: webcamRef.current.video });
                    }
                },
                width: 640,
                height: 480
            });
            camera.start();

            return () => {
                camera.stop();
            };
        }
    }, []);

    const analyzeQuality = (results: any, canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D): QualityMetrics => {
        let hasFace = false;
        let faceSize = 0;
        let brightness = 0;
        let isBlurry = false;

        // Check if face detected
        if (results.detections && results.detections.length > 0) {
            hasFace = true;
            const detection = results.detections[0];

            // Calculate face size (relative to frame)
            const bbox = detection.boundingBox;
            faceSize = (bbox.width * bbox.height) / (canvas.width * canvas.height) * 100;
        }

        // Calculate brightness
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        let total = 0;
        for (let i = 0; i < data.length; i += 4) {
            total += (data[i] + data[i + 1] + data[i + 2]) / 3;
        }
        brightness = total / (data.length / 4);

        // Simple blur detection (variance of Laplacian)
        isBlurry = detectBlur(imageData);

        // Calculate overall score
        let score = 0;
        if (hasFace) score += 40;
        if (faceSize > 5 && faceSize < 40) score += 30; // Optimal face size
        if (brightness > 80 && brightness < 180) score += 20; // Good lighting
        if (!isBlurry) score += 10;

        return { hasFace, brightness, isBlurry, faceSize, score };
    };

    const detectBlur = (imageData: ImageData): boolean => {
        // Simplified blur detection
        // In production, use more sophisticated algorithm
        return false; // Placeholder
    };

    const drawOverlay = (
        ctx: CanvasRenderingContext2D,
        canvas: HTMLCanvasElement,
        metrics: QualityMetrics,
        results: any
    ) => {
        // Draw oval guide
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radiusX = canvas.width * 0.3;
        const radiusY = canvas.height * 0.4;

        ctx.strokeStyle = metrics.score >= minQualityScore ? '#10b981' : metrics.hasFace ? '#f59e0b' : '#ef4444';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI);
        ctx.stroke();

        // Draw face bounding box if detected
        if (results.detections && results.detections.length > 0) {
            const detection = results.detections[0];
            const bbox = detection.boundingBox;

            ctx.strokeStyle = '#10b981';
            ctx.lineWidth = 2;
            ctx.strokeRect(bbox.xCenter * canvas.width - bbox.width * canvas.width / 2,
                bbox.yCenter * canvas.height - bbox.height * canvas.height / 2,
                bbox.width * canvas.width,
                bbox.height * canvas.height);
        }
    };

    const updateMessage = (metrics: QualityMetrics) => {
        if (!metrics.hasFace) {
            setMessage('No face detected');
        } else if (metrics.faceSize < 5) {
            setMessage('Move closer to the camera');
        } else if (metrics.faceSize > 40) {
            setMessage('Move away from the camera');
        } else if (metrics.brightness < 80) {
            setMessage('Too dark - increase lighting');
        } else if (metrics.brightness > 180) {
            setMessage('Too bright - reduce lighting');
        } else if (metrics.isBlurry) {
            setMessage('Image is blurry - hold still');
        } else if (metrics.score >= minQualityScore) {
            setMessage('Perfect! Hold steady...');
        } else {
            setMessage('Position your face in the oval');
        }
    };

    const startCountdown = useCallback(() => {
        if (countdown !== null) return; // Already counting

        setCountdown(3);
        const timer = setInterval(() => {
            setCountdown((prev) => {
                if (prev === null || prev <= 1) {
                    clearInterval(timer);
                    if (prev === 1) {
                        handleCapture();
                    }
                    return null;
                }
                return prev - 1;
            });
        }, 1000);
    }, [countdown]);

    const handleCapture = () => {
        if (webcamRef.current) {
            setIsProcessing(true);
            const imageSrc = webcamRef.current.getScreenshot();
            if (imageSrc) {
                onCapture(imageSrc, quality.score);
            }
            setIsProcessing(false);
        }
    };

    const getQualityColor = (score: number): string => {
        if (score >= 80) return 'text-green-500';
        if (score >= 60) return 'text-yellow-500';
        return 'text-red-500';
    };

    const getQualityIcon = () => {
        if (quality.score >= minQualityScore) {
            return <Check className="w-5 h-5 text-green-500" />;
        } else if (quality.hasFace) {
            return <AlertCircle className="w-5 h-5 text-yellow-500" />;
        }
        return <AlertCircle className="w-5 h-5 text-red-500" />;
    };

    return (
        <div className="relative w-full max-w-2xl mx-auto">
            {/* Webcam and Canvas */}
            <div className="relative bg-black rounded-lg overflow-hidden">
                <Webcam
                    ref={webcamRef}
                    audio={false}
                    screenshotFormat="image/jpeg"
                    className="w-full"
                    videoConstraints={{
                        width: 640,
                        height: 480,
                        facingMode: 'user'
                    }}
                />
                <canvas
                    ref={canvasRef}
                    className="absolute top-0 left-0 w-full h-full"
                />

                {/* Countdown Overlay */}
                {countdown !== null && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                        <div className="text-white text-9xl font-bold animate-pulse">
                            {countdown}
                        </div>
                    </div>
                )}
            </div>

            {/* Quality Info */}
            <div className="mt-4 p-4 bg-gray-800 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        {getQualityIcon()}
                        <span className={`font-mono text-lg font-semibold ${getQualityColor(quality.score)}`}>
                            Quality: {quality.score}%
                        </span>
                    </div>
                    <span className="text-sm text-gray-400">
                        Min required: {minQualityScore}%
                    </span>
                </div>

                {/* Message */}
                <div className="text-center py-3 bg-gray-700 rounded text-white">
                    {message}
                </div>

                {/* Quality Bars */}
                <div className="mt-3 space-y-2 text-sm">
                    <div>
                        <div className="flex justify-between text-gray-400 mb-1">
                            <span>Face Detection</span>
                            <span>{quality.hasFace ? 'Detected' : 'Not detected'}</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                            <div
                                className={`h-2 rounded-full ${quality.hasFace ? 'bg-green-500' : 'bg-red-500'}`}
                                style={{ width: quality.hasFace ? '100%' : '0%' }}
                            />
                        </div>
                    </div>

                    <div>
                        <div className="flex justify-between text-gray-400 mb-1">
                            <span>Lighting</span>
                            <span>{quality.brightness.toFixed(0)}</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                            <div
                                className={`h-2 rounded-full ${quality.brightness > 80 && quality.brightness < 180 ? 'bg-green-500' : 'bg-yellow-500'
                                    }`}
                                style={{ width: `${Math.min(quality.brightness / 255 * 100, 100)}%` }}
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="mt-4 flex gap-3">
                <Button
                    variant="secondary"
                    className="flex-1"
                    onClick={onCancel}
                    disabled={isProcessing}
                >
                    <X className="w-5 h-5 mr-2" />
                    Cancel
                </Button>
                <Button
                    variant="primary"
                    className="flex-1"
                    onClick={handleCapture}
                    disabled={quality.score < minQualityScore || isProcessing}
                >
                    <Camera className="w-5 h-5 mr-2" />
                    {autoCapture ? 'Capture Now' : 'Capture'}
                </Button>
            </div>
        </div>
    );
}
