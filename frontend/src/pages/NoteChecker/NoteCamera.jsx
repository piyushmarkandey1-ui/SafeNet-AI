import { useState, useRef, useEffect, useCallback } from 'react';
import { Camera, AlertTriangle, RefreshCw } from 'lucide-react';
import './NoteCamera.css';

export default function NoteCamera({ onCapture, disabled }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  
  const [error, setError] = useState(null);
  const [isLiveMode, setIsLiveMode] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  
  // Need to know if we are on a front-facing camera to mirror the video
  const [isMirrored, setIsMirrored] = useState(false);

  const startCamera = async () => {
    setError(null);
    try {
      // Prefer rear camera if available (facingMode: 'environment')
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      
      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        
        // Check if the actual track we got is front-facing (often happens on desktop)
        const track = stream.getVideoTracks()[0];
        const settings = track.getSettings();
        // If facingMode is 'user', mirror the video so it doesn't feel backwards
        setIsMirrored(settings.facingMode === 'user');
      }
    } catch (err) {
      console.error("Camera access error:", err);
      if (err.name === 'NotAllowedError') {
        setError('Camera permission denied. Please allow camera access in your browser settings.');
      } else if (err.name === 'NotFoundError') {
        setError('No camera found on this device.');
      } else if (err.name === 'NotReadableError') {
        setError('Camera is already in use by another application.');
      } else {
        setError('Unable to access camera: ' + err.message);
      }
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  const captureFrame = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current) return null;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    // Set canvas dimensions to match video source
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    
    // If mirrored, flip the canvas context before drawing so the captured image is correct
    if (isMirrored) {
      ctx.translate(canvas.width, 0);
      ctx.scale(-1, 1);
    }
    
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Reset transform
    if (isMirrored) {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
    }

    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        if (!blob) {
          resolve(null);
          return;
        }
        // Create a File object to match the file upload flow
        const file = new File([blob], `capture-${Date.now()}.jpg`, { type: 'image/jpeg' });
        resolve(file);
      }, 'image/jpeg', 0.9);
    });
  }, [isMirrored]);

  const handleManualCapture = async () => {
    if (disabled || isCapturing) return;
    setIsCapturing(true);
    try {
      const file = await captureFrame();
      if (file && onCapture) {
        await onCapture(file, false); // false = not live mode
      }
    } finally {
      setIsCapturing(false);
    }
  };

  // Live mode loop
  useEffect(() => {
    if (!isLiveMode || disabled) return;
    
    let isSubscribed = true;
    let isProcessing = false;

    const liveLoop = async () => {
      if (!isSubscribed) return;
      
      if (!isProcessing) {
        isProcessing = true;
        try {
          const file = await captureFrame();
          if (file && onCapture) {
            // true = is live mode
            await onCapture(file, true);
          }
        } catch (err) {
          console.error("Live loop capture error:", err);
        } finally {
          isProcessing = false;
        }
      }
      
      // Schedule next capture (1500ms is a safe interval considering backend latency of ~585ms)
      setTimeout(liveLoop, 1500);
    };
    
    // Start loop
    setTimeout(liveLoop, 500); // initial delay to let camera focus

    return () => {
      isSubscribed = false;
    };
  }, [isLiveMode, disabled, captureFrame, onCapture]);

  if (error) {
    return (
      <div className="note-camera__container" style={{ minHeight: '300px', border: '1px solid var(--border-color)' }}>
        <div className="note-camera__error">
          <AlertTriangle className="note-camera__error-icon" size={48} />
          <h3>Camera Unavailable</h3>
          <p>{error}</p>
          <button className="btn-retry" onClick={startCamera}>
            <RefreshCw size={16} style={{ display: 'inline', marginRight: 8 }} />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="note-camera-wrapper">
      <div className="note-camera__container">
        <video 
          ref={videoRef}
          className={`note-camera__video ${isMirrored ? 'note-camera__video--mirrored' : ''}`}
          autoPlay 
          playsInline 
          muted
        />
        <canvas ref={canvasRef} style={{ display: 'none' }} />
        
        {/* Overlay Guide */}
        <div className="note-camera__overlay">
          <div className="note-camera__guide">
            <div className="guide-corner guide-corner--tl" />
            <div className="guide-corner guide-corner--tr" />
            <div className="guide-corner guide-corner--bl" />
            <div className="guide-corner guide-corner--br" />
          </div>
        </div>
      </div>

      <div className="note-camera__controls">
        <button 
          className="note-camera__btn-capture"
          onClick={handleManualCapture}
          disabled={disabled || isLiveMode || isCapturing}
        >
          <Camera size={18} />
          {isCapturing ? 'Capturing...' : 'Capture Frame'}
        </button>

        <div className="note-camera__mode-toggle" onClick={() => !disabled && setIsLiveMode(!isLiveMode)}>
          <div className="mode-toggle-switch" data-active={isLiveMode}>
            <div className="mode-toggle-knob" />
          </div>
          <span className="mode-toggle-label" data-active={isLiveMode}>
            {isLiveMode ? (
              <><span className="live-pulse" /> Live Analysis</>
            ) : (
              'Live Analysis'
            )}
          </span>
        </div>
      </div>
    </div>
  );
}
