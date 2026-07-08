/**
 * SafeNet AI — AMD Status Panel
 *
 * Shows real-time inference provider status on the dashboard.
 * Polls /api/provider-status every 30 seconds.
 *
 * When FIREWORKS_API_KEY is set the badge shows "AMD" (green).
 * Otherwise it shows which fallback is active.
 *
 * This component satisfies the hackathon "Use of AMD Platforms" criterion
 * by making the AMD inference status visible to judges at a glance.
 */
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import './AmdStatusPanel.css';

const API_BASE = (() => {
  if (typeof window !== 'undefined') {
    const h = window.location.hostname;
    if (h !== 'localhost' && h !== '127.0.0.1') return window.location.origin;
  }
  return 'http://localhost:8000';
})();

async function fetchProviderStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/provider-status`);
    if (!res.ok) throw new Error('non-ok');
    return await res.json();
  } catch {
    return null;
  }
}

const PROVIDER_LABELS = {
  'fireworks-ai': { label: 'AMD · Fireworks AI', color: 'amd',     dot: '#00cc88' },
  'gemini':        { label: 'Gemini 2.0 Flash',  color: 'gemini',  dot: '#4285F4' },
  'openai':        { label: 'OpenAI GPT-4o',      color: 'openai',  dot: '#74aa9c' },
  'none':          { label: 'Template Fallback',  color: 'offline', dot: '#888'    },
};

export function AmdStatusPanel() {
  const [status, setStatus]       = useState(null);
  const [expanded, setExpanded]   = useState(false);
  const [pulse, setPulse]         = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const data = await fetchProviderStatus();
      if (!cancelled) {
        setStatus(data);
        setPulse(true);
        setTimeout(() => setPulse(false), 800);
      }
    }

    load();
    const id = setInterval(load, 30_000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  if (!status) return null;

  const provider  = status.active_provider ?? 'none';
  const meta      = PROVIDER_LABELS[provider] ?? PROVIDER_LABELS['none'];
  const isAmd     = provider === 'fireworks-ai';
  const modelName = (status.active_model ?? '').split('/').pop();

  return (
    <div className={`amd-panel amd-panel--${meta.color} ${pulse ? 'amd-panel--pulse' : ''}`}>
      {/* ── Collapsed bar ─────────────────────────── */}
      <button className="amd-panel__bar" onClick={() => setExpanded(e => !e)}>
        <div className="amd-panel__left">
          <span className="amd-panel__dot" style={{ background: meta.dot }} />
          {isAmd && <Cpu size={13} className="amd-panel__cpu-icon" />}
          <span className="amd-panel__label">{meta.label}</span>
        </div>
        <div className="amd-panel__right">
          {isAmd && (
            <span className="amd-panel__badge">
              <Zap size={10} /> AMD GPU
            </span>
          )}
          <span className="amd-panel__model">{modelName}</span>
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </div>
      </button>

      {/* ── Expanded detail ───────────────────────── */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            className="amd-panel__detail"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="amd-detail__row">
              <span className="amd-detail__key">Provider</span>
              <span className="amd-detail__val">{provider}</span>
            </div>
            <div className="amd-detail__row">
              <span className="amd-detail__key">Model</span>
              <span className="amd-detail__val">{status.active_model ?? '—'}</span>
            </div>
            <div className="amd-detail__row">
              <span className="amd-detail__key">AMD inference</span>
              <span className={`amd-detail__val ${isAmd ? 'amd-detail__val--on' : 'amd-detail__val--off'}`}>
                {isAmd ? '✓ Active' : '✗ Inactive'}
              </span>
            </div>
            {status.providers?.fireworks_ai && (
              <div className="amd-detail__routing">
                <span className="amd-detail__key">Task routing</span>
                <ul className="amd-detail__routes">
                  {Object.entries(status.providers.fireworks_ai.task_routing ?? {}).map(([task, model]) => (
                    <li key={task}>
                      <code>{task}</code>
                      <span>→ {model}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {!isAmd && (
              <p className="amd-detail__hint">
                Set <code>FIREWORKS_API_KEY</code> to enable AMD GPU inference.
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
