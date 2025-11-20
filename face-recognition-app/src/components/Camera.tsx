import React, { useRef, useEffect, useState } from 'react';
import Webcam from 'react-webcam';
import * as faceapi from 'face-api.js';

interface LabeledDescriptor {
    name: string;
    descriptors: number[][];
}

const Camera = () => {
  const webcamRef = useRef<Webcam>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [modelsLoaded, setModelsLoaded] = useState(false);
  const [faceMatcher, setFaceMatcher] = useState<faceapi.FaceMatcher | null>(null);

  useEffect(() => {
    const loadModels = async () => {
      const MODEL_URL = '/models';
      try {
        await Promise.all([
          faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
          faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
          faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
          faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL),
        ]);
        setModelsLoaded(true);
        console.log('Face-api models loaded successfully');
      } catch (error) {
        console.error('Error loading face-api models:', error);
      }
    };
    loadModels();
  }, []);

  useEffect(() => {
    const createFaceMatcher = async () => {
      try {
        // TODO: Implement API call to get labeled descriptors from backend
        // const response = await fetch('http://127.0.0.1:8888/api/descriptors');
        // const labeledDescriptors: LabeledDescriptor[] = await response.json();
        const labeledDescriptors: LabeledDescriptor[] = [];
        if (labeledDescriptors.length === 0) {
            console.log('No labeled descriptors found in the backend.');
            return;
        }

        const labeledFaceDescriptors = labeledDescriptors.map(
            (ld) => new faceapi.LabeledFaceDescriptors(
                ld.name,
                ld.descriptors.map(d => new Float32Array(d))
            )
        );

        const matcher = new faceapi.FaceMatcher(labeledFaceDescriptors, 0.6);
        setFaceMatcher(matcher);
        console.log('Face matcher created successfully');
      } catch (error) {
        console.error('Error creating face matcher:', error);
      }
    };

    if (modelsLoaded) {
      createFaceMatcher();
    }
  }, [modelsLoaded]);

  const handleVideoOnPlay = () => {
    const video = webcamRef.current?.video;
    if (!video || video.paused || video.ended || !modelsLoaded) {
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas) return;

    const displaySize = { width: video.videoWidth, height: video.videoHeight };
    faceapi.matchDimensions(canvas, displaySize);

    setInterval(async () => {
      const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions()).withFaceLandmarks().withFaceExpressions().withFaceDescriptors();
      const resizedDetections = faceapi.resizeResults(detections, displaySize);
      
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (faceMatcher) {
            const results = resizedDetections.map(d => faceMatcher.findBestMatch(d.descriptor));
            results.forEach((result, i) => {
                const box = resizedDetections[i].detection.box;
                const drawBox = new faceapi.draw.DrawBox(box, { label: result.toString() });
                drawBox.draw(canvas);
            });
        } else {
            faceapi.draw.drawDetections(canvas, resizedDetections);
        }

        faceapi.draw.drawFaceLandmarks(canvas, resizedDetections);
        faceapi.draw.drawFaceExpressions(canvas, resizedDetections);
      }
    }, 100);
  };

  return (
    <div className="camera-container" style={{ position: 'relative', width: '640px', height: '480px' }}>
      <h2>Camera Feed</h2>
      {!modelsLoaded && <p>Loading models, please wait...</p>}
      <Webcam
        ref={webcamRef}
        audio={false}
        height={480}
        width={640}
        videoConstraints={{ width: 640, height: 480, facingMode: 'user' }}
        onPlay={handleVideoOnPlay}
        style={{ position: 'absolute', top: 0, left: 0 }}
      />
      <canvas
        ref={canvasRef}
        style={{ position: 'absolute', top: 0, left: 0 }}
      />
    </div>
  );
};

export default Camera;