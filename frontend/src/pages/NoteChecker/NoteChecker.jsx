/**
 * NoteChecker — Currency Counterfeit Detection UI
 *
 * Lets a user upload a photo of an Indian Rupee note and receive:
 *   - Real / Fake verdict with confidence score
 *   - Denomination prediction
 *   - Grad-CAM heatmap showing which regions drove the decision
 *
 * Calls checkNote() from lib/api.js → POST /vision/check-note (real backend)
 * Falls back to a mock response automatically when backend is offline.
 */
import { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Upload,
  Eye,
  ShieldCheck,
  ShieldAlert,
  Loader2,
  ScanLine,
  X,
  Info,
  Camera,
  Home,
  LayoutDashboard,
  Banknote,
} from 'lucide-react';
import { GlassPanel, RiskBadge, Breadcrumb } from '../../components/ui';
import NoteCamera from './NoteCamera';
import { checkNote } from '../../lib/api';
import { fadeInUp } from '../../lib/motion';
import './NoteChecker.css';

// ── Animations ────────────────────────────────────────────────────────────────
const resultVariants = {
  hidden: { opacity: 0, y: 24, scale: 0.97 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
  exit:   { opacity: 0, y: -12, transition: { duration: 0.2 } },
};


// ── Sub-components ────────────────────────────────────────────────────────────

function ConfidenceBar({ confidence, isFake }) {
  const pct = Math.round(confidence * 100);
  return (
    <div className="verdict-confidence">
      <span className="verdict-confidence__label">Confidence</span>
      <div className="verdict-confidence__bar-wrap">
        <motion.div
          className={`verdict-confidence__bar ${isFake ? 'verdict-confidence__bar--fake' : 'verdict-confidence__bar--real'}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>
      <span className="verdict-confidence__value">{pct}%</span>
    </div>
  );
}


function VerdictCard({ result }) {
  const isFake = result.is_fake;
  const Icon = isFake ? ShieldAlert : ShieldCheck;

  return (
    <GlassPanel
      className="verdict-card"
      glowColor={isFake ? 'risk' : 'trust'}
      hoverable={false}
    >
      <div className="verdict-header">
        <div>
          <h2 className={`verdict-title ${result.severity === 'unknown' ? 'verdict-title--unknown' : (isFake ? 'verdict-title--fake' : 'verdict-title--real')}`}>
            <Icon size={20} style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />
            {result.severity === 'unknown' ? 'NO NOTE DETECTED' : (isFake ? 'COUNTERFEIT DETECTED' : 'GENUINE NOTE')}
          </h2>
          {result.severity !== 'unknown' && (
            <p className="verdict-denomination">
              Denomination: <strong>{result.denomination}</strong>
            </p>
          )}
        </div>
        {result.severity !== 'unknown' && <RiskBadge severity={result.severity} />}
      </div>

      <p className="verdict-recommendation">{result.recommendation}</p>

      {result.severity !== 'unknown' && (
        <ConfidenceBar confidence={result.confidence} isFake={isFake} />
      )}
    </GlassPanel>
  );
}


function GradCamCard({ base64Png }) {
  if (!base64Png) return null;

  return (
    <GlassPanel className="gradcam-card" hoverable={false} glowColor="trust">
      <p className="gradcam-title">
        <Eye size={14} />
        Grad-CAM Explainability Overlay
      </p>
      <img
        className="gradcam-img"
        src={`data:image/png;base64,${base64Png}`}
        alt="Grad-CAM heatmap showing decision-relevant regions"
      />
      <div className="gradcam-legend">
        <span>
          <span className="gradcam-legend__swatch" style={{ background: '#0000ff' }} />
          Low attention
        </span>
        <span>
          <span className="gradcam-legend__swatch" style={{ background: '#00ff00' }} />
          Medium
        </span>
        <span>
          <span className="gradcam-legend__swatch" style={{ background: '#ff0000' }} />
          High attention
        </span>
      </div>
    </GlassPanel>
  );
}


// ── Main Page ─────────────────────────────────────────────────────────────────

export default function NoteChecker() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [inputMode, setInputMode] = useState('upload'); // 'upload' or 'camera'

  // ── File handling ──────────────────────────────────────────────────────────
  const handleFile = useCallback((file) => {
    if (!file || !file.type.startsWith('image/')) {
      setError('Please select an image file (JPEG, PNG, WEBP).');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large. Maximum size is 10 MB.');
      return;
    }
    setError(null);
    setResult(null);
    
    // Cleanup previous URL if it exists
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  }, [previewUrl]);

  const handleFileInput = (e) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);

  const clearFile = useCallback(() => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, [previewUrl]);

  // Cleanup object URL on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);


  // ── Submission ─────────────────────────────────────────────────────────────
  const handleSubmit = async (fileToSubmit = selectedFile) => {
    if (!fileToSubmit) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await checkNote(fileToSubmit);
      setResult(data);
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCameraCapture = async (file, isLive) => {
    // If it's a live capture, don't show the big spinner blocking the UI
    if (isLive) {
      try {
        const data = await checkNote(file);
        setResult(data);
        setError(null);
      } catch (err) {
        console.warn("Live check failed:", err);
      }
    } else {
      // Standard capture logic (shows loading spinner)
      setSelectedFile(file);
      await handleSubmit(file);
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="note-checker">
      <Breadcrumb 
        items={[
          { label: 'Home', path: '/', icon: Home },
          { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
          { label: 'Note Checker', icon: Banknote }
        ]}
      />
      
      {/* Body */}
      <div className="note-checker__body">

        {/* ── Upload Pane ── */}
        <div>
          <GlassPanel hoverable={false} glowColor="trust">
            <div className="upload-pane__header">
              <div>
                <h1 className="upload-pane__title">Check a Currency Note</h1>
                <p className="upload-pane__subtitle">
                  {inputMode === 'upload' 
                    ? 'Upload a photo of an Indian Rupee note.' 
                    : 'Scan an Indian Rupee note with your camera.'}
                  The AI will classify it as genuine or counterfeit and highlight the decision-relevant regions.
                </p>
              </div>
              
              <div className="input-mode-toggle">
                <button 
                  className={`mode-btn ${inputMode === 'upload' ? 'active' : ''}`}
                  onClick={() => setInputMode('upload')}
                >
                  <Upload size={14} /> Upload
                </button>
                <button 
                  className={`mode-btn ${inputMode === 'camera' ? 'active' : ''}`}
                  onClick={() => setInputMode('camera')}
                >
                  <Camera size={14} /> Camera
                </button>
              </div>
            </div>

            {inputMode === 'upload' ? (
              <>
                {!selectedFile ? (
              <div
                className={`drop-zone ${isDragging ? 'drop-zone--active' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="drop-zone__input"
                  onChange={handleFileInput}
                />
                <Upload className="drop-zone__icon" size={36} />
                <p className="drop-zone__primary">Drop image here or click to browse</p>
                <p className="drop-zone__secondary">JPEG, PNG, WEBP · max 10 MB</p>
              </div>
            ) : (
              <div className="preview-container">
                <img
                  className="preview-img"
                  src={previewUrl}
                  alt="Selected currency note"
                />
                <button className="preview-remove" onClick={clearFile} title="Remove">
                  <X size={14} />
                </button>
                <p className="preview-meta">
                  {selectedFile.name} · {(selectedFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
            )}

            {error && (
              <p style={{
                marginTop: 'var(--space-sm)',
                fontSize: 'var(--text-sm)',
                color: 'var(--accent-risk)',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}>
                <Info size={14} /> {error}
              </p>
            )}

                <button
                  className={`btn-check ${isLoading ? 'btn-check--loading' : ''}`}
                  onClick={() => handleSubmit(selectedFile)}
                  disabled={!selectedFile || isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 size={18} className="spinner" />
                      Analysing…
                    </>
                  ) : (
                    <>
                      <ScanLine size={18} />
                      Check Note
                    </>
                  )}
                </button>
              </>
            ) : (
              <NoteCamera onCapture={handleCameraCapture} disabled={isLoading} />
            )}
          </GlassPanel>
        </div>

        {/* ── Result Pane ── */}
        <div className="result-pane">
          <AnimatePresence mode="wait">
            {!result && !isLoading && (
              <motion.div
                key="empty"
                className="result-pane__empty"
                variants={resultVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
              >
                <ScanLine className="result-pane__empty-icon" size={48} />
                <p className="result-pane__empty-text">
                  Upload a note image and click "Check Note" to see the verdict.
                </p>
              </motion.div>
            )}

            {isLoading && (
              <motion.div
                key="loading"
                className="result-pane__empty"
                variants={resultVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
              >
                <Loader2 size={48} className="spinner" style={{ color: 'var(--accent-trust)' }} />
                <p className="result-pane__empty-text">Running inference + Grad-CAM…</p>
              </motion.div>
            )}

            {result && (
              <motion.div
                key="result"
                variants={resultVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}
              >
                <VerdictCard result={result} />
                <GradCamCard base64Png={result.gradcam_overlay} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

      </div>
    </div>
  );
}
