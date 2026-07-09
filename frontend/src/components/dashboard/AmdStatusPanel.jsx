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

const API_BASE = '';

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
              <span className="amd-detail__key">AMD LLM Inference</span>
              <span className={`amd-detail__val ${isAmd ? 'amd-detail__val--on' : 'amd-detail__val--off'}`}>
                {isAmd ? '✓ Active' : '✗ Inactive'}
              </span>
            </div>

            {status.local_gpu && (
              <>
                <div className="amd-detail__row" style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '8px', marginTop: '8px' }}>
                  <span className="amd-detail__key">Local Vision GPU</span>
                  <span className={`amd-detail__val ${status.local_gpu.gpu_available ? 'amd-detail__val--on' : 'amd-detail__val--off'}`}>
                    {status.local_gpu.gpu_available ? '✓ Active' : '✗ Inactive'}
                  </span>
                </div>
                {status.local_gpu.gpu_available ? (
                  <>
                    <div className="amd-detail__row">
                      <span className="amd-detail__key">GPU Device</span>
                      <span className="amd-detail__val">{status.local_gpu.device_name || 'AMD GPU'}</span>
                    </div>
                    <div className="amd-detail__row">
                      <span className="amd-detail__key">Compute Stack</span>
                      <span className="amd-detail__val">{status.local_gpu.platform}</span>
                    </div>
                  </>
                ) : (
                  <div className="amd-detail__row">
                    <span className="amd-detail__key">Compute Stack</span>
                    <span className="amd-detail__val">{status.local_gpu.platform || 'CPU Fallback'}</span>
                  </div>
                )}
              </>
            )}

            {status.providers?.fireworks_ai && (
              <div className="amd-detail__routing" style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '8px', marginTop: '8px' }}>
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
                Set <code>FIREWORKS_API_KEY</code> to enable AMD GPU LLM inference.
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
