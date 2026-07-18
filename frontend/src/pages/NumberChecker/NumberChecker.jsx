/**
 * SafeNet AI — Number Checker Page
 *
 * ⚠️ No live call interception. The user submits the number + optional
 * message/transcript text themselves.
 */
import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Phone, Search, ArrowLeft, AlertTriangle, CheckCircle,
  ShieldAlert, FileText, Info, ChevronDown, ChevronUp,
  Database, ScanText, List, Home, LayoutDashboard,
} from 'lucide-react';
import { RiskBadge, GlassPanel, Breadcrumb } from '../../components/ui';
import { checkNumber } from '../../lib/api';
import './NumberChecker.css';

// Confidence bar colours per risk level
const RISK_COLORS = {
  critical: 'var(--accent-risk)',
  high:     'var(--accent-risk)',
  medium:   'var(--accent-warning)',
  low:      'var(--accent-trust)',
};

const SOURCE_ICONS = {
  'Fraud Graph': Database,
  'Message content': ScanText,
  'Synthetic blocklist': List,
};

function SourceIcon({ label }) {
  const entry = Object.entries(SOURCE_ICONS).find(([k]) => label.toLowerCase().includes(k.toLowerCase()));
  const Icon = entry ? entry[1] : Info;
  return <Icon size={14} className="source-icon" />;
}

export default function NumberChecker() {
  const [phone, setPhone] = useState('');
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showSources, setShowSources] = useState(false);
  const resultRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!phone.trim()) {
      setError('Please enter a phone number to analyze.');
      return;
    }
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const data = await checkNumber(phone.trim(), text.trim());
      setResult(data);
      // Scroll to result smoothly
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    } catch (err) {
      setError('Could not reach the analysis API. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setPhone('');
    setText('');
    setResult(null);
    setError('');
    setShowSources(false);
  };

  return (
    <div className="nc-page">
      <Breadcrumb 
        items={[
          { label: 'Home', path: '/', icon: Home },
          { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
          { label: 'Number Checker', icon: Phone }
        ]}
      />

      <main className="nc-main">
        {/* ── Input Card ───────────────────────────────────────────────── */}
        <GlassPanel hoverable={false} className="nc-input-card">
          <div className="nc-input-header">
            <ShieldAlert size={22} className="nc-header-icon" />
            <div>
              <h1 className="nc-title">Check This Number</h1>
              <p className="nc-subtitle">
                Enter a phone number you received a suspicious call or message from.
                Paste the message text for deeper analysis.
              </p>
            </div>
          </div>

          <form className="nc-form" onSubmit={handleSubmit}>
            <div className="nc-field">
              <label className="nc-label" htmlFor="nc-phone">
                Phone Number <span className="nc-required">*</span>
              </label>
              <div className="nc-phone-wrap">
                <Phone size={16} className="nc-phone-icon" />
                <input
                  id="nc-phone"
                  type="tel"
                  className="nc-input"
                  placeholder="+91XXXXXXXXXX  or  0XXXXXXXXXX"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  disabled={loading}
                  required
                  autoComplete="off"
                />
              </div>
            </div>

            <div className="nc-field">
              <label className="nc-label" htmlFor="nc-text">
                Suspicious Message / Call Transcript
                <span className="nc-optional">(optional — paste what they said or sent)</span>
              </label>
              <textarea
                id="nc-text"
                className="nc-textarea"
                placeholder={"Example:\n\"Your account has been flagged for suspicious activity. Call us immediately to avoid legal action. Do not tell anyone about this call.\"\n\nPasting the exact text enables deeper scam-language analysis."}
                rows={5}
                value={text}
                onChange={(e) => setText(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="nc-actions">
              <button
                type="submit"
                className="nc-submit-btn"
                disabled={loading || !phone.trim()}
              >
                {loading ? (
                  <>
                    <span className="nc-spinner" />
                    <span>Analysing…</span>
                  </>
                ) : (
                  <>
                    <Search size={16} />
                    <span>Analyse Number</span>
                  </>
                )}
              </button>
              {(result || phone) && (
                <button type="button" className="nc-clear-btn" onClick={handleClear}>
                  Clear
                </button>
              )}
            </div>
          </form>

          {error && (
            <div className="nc-error">
              <AlertTriangle size={16} />
              <span>{error}</span>
            </div>
          )}
        </GlassPanel>

        {/* ── Results Card ─────────────────────────────────────────────── */}
        <AnimatePresence>
          {result && (
            <motion.div
              ref={resultRef}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 16 }}
              transition={{ duration: 0.35, ease: 'easeOut' }}
            >
              <GlassPanel hoverable={false} className={`nc-result-card nc-result--${result.risk_level}`}>

                {/* ── Verdict header ────────── */}
                <div className="nc-verdict-row">
                  <div className="nc-verdict-left">
                    <span className="nc-result-number">{result.phone_number}</span>
                    <RiskBadge
                      severity={result.risk_level === 'low' && result.confidence === 0 ? 'safe' : result.risk_level}
                      label={result.risk_level.charAt(0).toUpperCase() + result.risk_level.slice(1) + ' Risk'}
                      className="nc-risk-badge"
                    />
                    {result.graph_primary_threat && (
                      <span className="nc-threat-tag">{result.graph_primary_threat}</span>
                    )}
                  </div>

                  {/* Confidence bar */}
                  {result.confidence > 0 && (
                    <div className="nc-confidence">
                      <span className="nc-confidence-label">Confidence</span>
                      <div className="nc-confidence-bar-bg">
                        <motion.div
                          className="nc-confidence-bar-fill"
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.round(result.confidence * 100)}%` }}
                          transition={{ duration: 0.6, ease: 'easeOut', delay: 0.2 }}
                          style={{ background: RISK_COLORS[result.risk_level] }}
                        />
                      </div>
                      <span className="nc-confidence-pct">
                        {Math.round(result.confidence * 100)}%
                      </span>
                    </div>
                  )}
                </div>

                {/* ── Signals found ──────────── */}
                <div className="nc-section">
                  <h3 className="nc-section-title">
                    {result.reasons.length === 1 && result.confidence === 0
                      ? <><CheckCircle size={15} className="nc-icon-ok" /> No Matches Found</>
                      : <><AlertTriangle size={15} className="nc-icon-warn" /> Signals Detected</>
                    }
                  </h3>
                  <ul className="nc-reasons">
                    {result.reasons.map((r, i) => (
                      <motion.li
                        key={i}
                        className="nc-reason-item"
                        initial={{ opacity: 0, x: -12 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 + i * 0.07 }}
                      >
                        <span className={`nc-reason-dot nc-dot--${result.risk_level}`} />
                        <span>{r}</span>
                      </motion.li>
                    ))}
                  </ul>
                </div>

                {/* ── Text score (if provided) ── */}
                {result.text_score !== null && (
                  <div className="nc-section nc-text-score-row">
                    <ScanText size={14} className="nc-icon-sm" />
                    <span className="nc-text-score-label">Message scam-language score:</span>
                    <span
                      className="nc-text-score-val"
                      style={{ color: result.text_score >= 60 ? 'var(--accent-risk)' : 'var(--accent-warning)' }}
                    >
                      {result.text_score}/100
                    </span>
                  </div>
                )}

                {/* ── Graph link ─────────────── */}
                {result.graph_case_id && (
                  <div className="nc-section nc-graph-badge">
                    <Database size={14} className="nc-icon-sm" />
                    <span>Fraud graph case: <strong>{result.graph_case_id}</strong></span>
                    {result.graph_risk_score != null && (
                      <span className="nc-graph-score">
                        · Graph risk {result.graph_risk_score}/100
                      </span>
                    )}
                  </div>
                )}

                {/* ── Recommendation ─────────── */}
                <div className="nc-recommendation">
                  <FileText size={14} className="nc-icon-sm" />
                  <p>{result.recommendation}</p>
                </div>

                {/* ── Sources checked ────────── */}
                <button
                  className="nc-sources-toggle"
                  onClick={() => setShowSources(s => !s)}
                >
                  {showSources ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  <span>Sources checked ({result.sources_checked.length})</span>
                </button>

                <AnimatePresence>
                  {showSources && (
                    <motion.ul
                      className="nc-sources-list"
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      {result.sources_checked.map((s, i) => (
                        <li key={i} className="nc-source-item">
                          <SourceIcon label={s} />
                          <span>{s}</span>
                        </li>
                      ))}
                    </motion.ul>
                  )}
                </AnimatePresence>

                {/* ── Synthetic data disclaimer ─ */}
                <p className="nc-data-note">
                  ⚠️ SYNTHETIC DATA — results are based on a demo dataset, not real telecom records.
                  A "no record" result does not guarantee the number is safe.
                </p>
              </GlassPanel>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Example numbers panel ─────────────────────────────────── */}
        {!result && !loading && (
          <GlassPanel hoverable={false} className="nc-examples-card">
            <h3 className="nc-examples-title">Try these example numbers</h3>
            <div className="nc-examples-grid">
              {[
                {
                  label: 'Known fraud graph number',
                  number: '+916511361582',
                  hint: 'Exists in synthetic dataset — expect graph hit',
                  color: 'risk',
                },
                {
                  label: 'Unknown number + scam message',
                  number: '+917000000001',
                  hint: 'Paste: "Your account is frozen. Pay ₹5000 fine immediately. Do not tell anyone."',
                  color: 'warning',
                },
                {
                  label: 'Unknown number, no message',
                  number: '+917999999999',
                  hint: 'Should return honest "no record found"',
                  color: 'trust',
                },
              ].map((ex) => (
                <button
                  key={ex.number}
                  className={`nc-example-btn nc-example--${ex.color}`}
                  onClick={() => setPhone(ex.number)}
                >
                  <span className="nc-example-label">{ex.label}</span>
                  <span className="nc-example-number">{ex.number}</span>
                  <span className="nc-example-hint">{ex.hint}</span>
                </button>
              ))}
            </div>
          </GlassPanel>
        )}
      </main>
    </div>
  );
}
