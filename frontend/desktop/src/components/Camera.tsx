import { useRef, useEffect, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import { identify } from '../config/api';
import Card, { CardBody } from './ui/Card';
import Button from './ui/Button';
import { Camera as CameraIcon, Video, AlertCircle, CheckCircle, XCircle, Maximize2, Minimize2 } from 'lucide-react';

export default function Camera() {
  const webcamRef = useRef<Webcam>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [matches, setMatches] = useState<any[]>([]);
  const [lastMatch, setLastMatch] = useState<any>(null);
  const [error, setError] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);

  const capture = useCallback(async () => {
    if (!webcamRef.current || !isScanning) return;

    const imageSrc = webcamRef.current.getScreenshot();
    if (!imageSrc) return;

    try {
      // Convert base64 to blob
      const res = await fetch(imageSrc);
      const blob = await res.blob();
      const formData = new FormData();
      formData.append('file', blob, 'capture.jpg');

      const response = await identify.identifyFace(formData);
      const data = response.data;

      if (data.matches && data.matches.length > 0) {
        setMatches(data.matches);
        // Update last match if confidence is high enough
        const bestMatch = data.matches.reduce((prev: any, current: any) =>
          (prev.confidence > current.confidence) ? prev : current
        );
        if (bestMatch.confidence > 80) {
          setLastMatch({
            ...bestMatch,
            timestamp: new Date(),
            image: imageSrc
          });
        }
      } else {
        setMatches([]);
      }
      setError('');
    } catch (err) {
      console.error('Identification failed:', err);
      // Don't set error state to avoid flickering UI, just log it
    }
  }, [isScanning]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isScanning) {
      interval = setInterval(capture, 1000); // Scan every second
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isScanning, capture]);

  const toggleScanning = () => {
    setIsScanning(!isScanning);
    setMatches([]);
    if (!isScanning) {
      setLastMatch(null);
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
        setIsFullscreen(false);
      }
    }
  };

  return (
    <div className="p-6 h-[calc(100vh-80px)] flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Real-time Identification</h1>
          <p className="text-gray-400">Live camera feed with face recognition</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={toggleFullscreen}
            title="Toggle Fullscreen"
          >
            {isFullscreen ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
          </Button>
          <Button
            variant={isScanning ? 'danger' : 'primary'}
            onClick={toggleScanning}
          >
            {isScanning ? (
              <>
                <XCircle size={20} /> Stop Scanning
              </>
            ) : (
              <>
                <Video size={20} /> Start Scanning
              </>
            )}
          </Button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
        {/* Camera Feed */}
        <div className="lg:col-span-2 relative bg-black rounded-2xl overflow-hidden shadow-2xl border border-gray-800 flex items-center justify-center">
          {!isScanning ? (
            <div className="text-center p-10">
              <div className="w-20 h-20 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-6">
                <CameraIcon size={40} className="text-gray-500" />
              </div>
              <h3 className="text-xl font-medium text-white mb-2">Camera is Offline</h3>
              <p className="text-gray-400 mb-6">Click "Start Scanning" to activate the camera</p>
              <Button variant="primary" onClick={toggleScanning}>
                Start Scanning
              </Button>
            </div>
          ) : (
            <div className="relative w-full h-full">
              <Webcam
                ref={webcamRef}
                audio={false}
                screenshotFormat="image/jpeg"
                className="w-full h-full object-contain"
                videoConstraints={{
                  width: 1280,
                  height: 720,
                  facingMode: "user"
                }}
              />
              {/* Bounding Boxes */}
              {matches.map((match, idx) => (
                <div
                  key={idx}
                  className="absolute border-2 border-green-500 rounded-lg transition-all duration-200"
                  style={{
                    left: `${match.bbox.Left * 100}%`,
                    top: `${match.bbox.Top * 100}%`,
                    width: `${match.bbox.Width * 100}%`,
                    height: `${match.bbox.Height * 100}%`,
                  }}
                >
                  <div className="absolute -top-8 left-0 bg-green-500 text-black text-xs font-bold px-2 py-1 rounded">
                    {match.name} ({Math.round(match.confidence)}%)
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6 overflow-y-auto">
          {/* Status Card */}
          <Card>
            <CardBody>
              <h3 className="text-lg font-bold text-white mb-4">Status</h3>
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-3 h-3 rounded-full ${isScanning ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                <span className="text-gray-300">{isScanning ? 'System Active' : 'System Idle'}</span>
              </div>
              {error && (
                <div className="bg-red-500/10 border border-red-500/20 p-3 rounded-lg flex items-start gap-2 text-sm text-red-400">
                  <AlertCircle size={16} className="shrink-0 mt-0.5" />
                  {error}
                </div>
              )}
            </CardBody>
          </Card>

          {/* Last Match Card */}
          <Card>
            <CardBody>
              <h3 className="text-lg font-bold text-white mb-4">Last Identification</h3>
              {lastMatch ? (
                <div className="space-y-4">
                  <div className="aspect-video bg-gray-800 rounded-lg overflow-hidden relative">
                    <img src={lastMatch.image} alt="Last match" className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex items-end p-3">
                      <div>
                        <p className="text-white font-bold text-lg">{lastMatch.name}</p>
                        <p className="text-green-400 text-sm">{Math.round(lastMatch.confidence)}% Confidence</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <CheckCircle size={16} className="text-green-500" />
                    Verified at {lastMatch.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <User size={32} className="mx-auto mb-2 opacity-50" />
                  <p>No matches yet</p>
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}

// Helper icon component
function User({ size, className }: { size: number, className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
      <circle cx="12" cy="7" r="4"></circle>
    </svg>
  );
}