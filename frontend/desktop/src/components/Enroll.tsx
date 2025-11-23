import React, { useState, useRef } from 'react';
import { Camera, Upload, UserPlus, X, Check, AlertCircle, Image as ImageIcon } from 'lucide-react';
import Button from './ui/Button';
import Input from './ui/Input';
import Card from './ui/Card';
import { enroll } from '../config/api';
import { FaceCapture } from './FaceCapture';

export function Enroll() {
    const [mode, setMode] = useState<'upload' | 'webcam'>('upload');
    const [name, setName] = useState('');
    const [userId, setUserId] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [capturedImage, setCapturedImage] = useState<string | null>(null);
    const [capturedQuality, setCapturedQuality] = useState<number>(0);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [showFaceCapture, setShowFaceCapture] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (!file.type.startsWith('image/')) {
                setError('Please select a valid image file');
                return;
            }
            setSelectedFile(file);
            setPreviewUrl(URL.createObjectURL(file));
            setError('');
            setSuccess('');
        }
    };

    const handleFaceCapture = (imageData: string, qualityScore: number) => {
        setCapturedImage(imageData);
        setCapturedQuality(qualityScore);
        setPreviewUrl(imageData);
        setShowFaceCapture(false);
        setError('');
        setSuccess('');
    };

    const handleCancelCapture = () => {
        setShowFaceCapture(false);
    };

    const handleClear = () => {
        setSelectedFile(null);
        setCapturedImage(null);
        setCapturedQuality(0);
        setPreviewUrl(null);
        setError('');
        setSuccess('');
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (!name.trim()) {
            setError('Please enter a name');
            return;
        }

        if (mode === 'upload' && !selectedFile) {
            setError('Please select an image');
            return;
        }

        if (mode === 'webcam' && !capturedImage) {
            setError('Please capture an image');
            return;
        }

        setIsLoading(true);

        try {
            const formData = new FormData();
            formData.append('name', name.trim());
            if (userId.trim()) {
                formData.append('user_id', userId.trim());
            }

            if (mode === 'upload' && selectedFile) {
                formData.append('file', selectedFile);
            } else if (mode === 'webcam' && capturedImage) {
                // Convert base64 to blob
                const res = await fetch(capturedImage);
                const blob = await res.blob();
                formData.append('file', blob, 'captured.jpg');
            }

            const response = await enroll.enrollUser(formData);
            setSuccess(`Successfully enrolled ${response.data.name}! User ID: ${response.data.user_id}${mode === 'webcam' ? ` (Quality: ${capturedQuality}%)` : ''}`);

            // Reset form after 2 seconds
            setTimeout(() => {
                setName('');
                setUserId('');
                handleClear();
                setSuccess('');
            }, 3000);
        } catch (error: any) {
            const message = error.response?.data?.detail || 'Enrollment failed. Please try again.';
            setError(message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto p-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">Enroll New Face</h1>
                <p className="text-gray-400">Add a new person to the face recognition system</p>
            </div>

            {/* Mode Selection */}
            <div className="flex gap-4 mb-6">
                <Button
                    variant={mode === 'upload' ? 'primary' : 'secondary'}
                    onClick={() => {
                        setMode('upload');
                        handleClear();
                        setShowFaceCapture(false);
                    }}
                    className="flex-1"
                    disabled={isLoading}
                >
                    <Upload className="w-5 h-5 mr-2" />
                    Upload Image
                </Button>
                <Button
                    variant={mode === 'webcam' ? 'primary' : 'secondary'}
                    onClick={() => {
                        setMode('webcam');
                        handleClear();
                    }}
                    className="flex-1"
                    disabled={isLoading}
                >
                    <Camera className="w-5 h-5 mr-2" />
                    Capture from Webcam
                </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Image Capture/Upload Section */}
                <Card className="p-6">
                    <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                        {mode === 'upload' ? <Upload className="w-5 h-5" /> : <Camera className="w-5 h-5" />}
                        {mode === 'upload' ? 'Upload Image' : 'Capture Image'}
                    </h2>

                    {mode === 'upload' ? (
                        <div>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/*"
                                onChange={handleFileSelect}
                                className="hidden"
                                id="file-upload"
                                disabled={isLoading}
                            />
                            <label
                                htmlFor="file-upload"
                                className={`border-2 border-dashed border-gray-600 rounded-lg p-8 flex flex-col items-center justify-center cursor-pointer hover:border-blue-500 transition-colors ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                {previewUrl ? (
                                    <div className="relative">
                                        <img
                                            src={previewUrl}
                                            alt="Preview"
                                            className="max-w-full max-h-64 rounded-lg"
                                        />
                                        <button
                                            onClick={(e) => {
                                                e.preventDefault();
                                                handleClear();
                                            }}
                                            className="absolute top-2 right-2 bg-red-500 text-white p-2 rounded-full hover:bg-red-600 transition-colors"
                                            disabled={isLoading}
                                        >
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>
                                ) : (
                                    <>
                                        <ImageIcon className="w-16 h-16 text-gray-500 mb-4" />
                                        <p className="text-gray-400 text-center">
                                            Click to select an image
                                            <br />
                                            <span className="text-sm text-gray-500">or drag and drop</span>
                                        </p>
                                    </>
                                )}
                            </label>
                        </div>
                    ) : (
                        <div>
                            {showFaceCapture ? (
                                <FaceCapture
                                    onCapture={handleFaceCapture}
                                    onCancel={handleCancelCapture}
                                    minQualityScore={70}
                                    autoCapture={true}
                                />
                            ) : !capturedImage ? (
                                <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center">
                                    <Camera className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                                    <p className="text-gray-400 mb-4">Capture a high-quality face photo</p>
                                    <Button
                                        onClick={() => setShowFaceCapture(true)}
                                        disabled={isLoading}
                                    >
                                        <Camera className="w-5 h-5 mr-2" />
                                        Start Face Capture
                                    </Button>
                                </div>
                            ) : (
                                <div className="relative">
                                    <img
                                        src={capturedImage}
                                        alt="Captured"
                                        className="w-full rounded-lg"
                                    />
                                    <div className="absolute top-2 left-2 bg-green-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
                                        Quality: {capturedQuality}%
                                    </div>
                                    <button
                                        onClick={handleClear}
                                        className="absolute top-2 right-2 bg-red-500 text-white p-2 rounded-full hover:bg-red-600 transition-colors"
                                        disabled={isLoading}
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </Card>

                {/* Form Section */}
                <Card className="p-6">
                    <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                        <UserPlus className="w-5 h-5" />
                        Person Details
                    </h2>

                    {error && (
                        <div className="bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 p-4 rounded mb-4">
                            <div className="flex items-center gap-2">
                                <AlertCircle className="w-5 h-5 text-red-500" />
                                <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
                            </div>
                        </div>
                    )}

                    {success && (
                        <div className="bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500 p-4 rounded mb-4">
                            <div className="flex items-center gap-2">
                                <Check className="w-5 h-5 text-green-500" />
                                <p className="text-sm text-green-700 dark:text-green-400">{success}</p>
                            </div>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Name <span className="text-red-500">*</span>
                            </label>
                            <Input
                                type="text"
                                placeholder="Enter person's name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                disabled={isLoading}
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                User ID <span className="text-gray-500">(optional)</span>
                            </label>
                            <Input
                                type="text"
                                placeholder="Auto-generated if left empty"
                                value={userId}
                                onChange={(e) => setUserId(e.target.value)}
                                disabled={isLoading}
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                Leave empty to auto-generate a unique ID
                            </p>
                        </div>

                        <Button
                            type="submit"
                            className="w-full"
                            size="lg"
                            disabled={isLoading || !previewUrl}
                        >
                            {isLoading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                                    Enrolling...
                                </>
                            ) : (
                                <>
                                    <UserPlus className="w-5 h-5 mr-2" />
                                    Enroll Face
                                </>
                            )}
                        </Button>
                    </form>
                </Card>
            </div>
        </div>
    );
}
