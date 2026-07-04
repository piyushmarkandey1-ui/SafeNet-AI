/**
 * RiskBadge — Severity-coded status indicator
 *
 * Color-coded pill badge with severity levels:
 *   critical  → accent-risk with pulse animation
 *   high      → accent-risk (static)
 *   medium    → accent-warning
 *   low       → accent-trust
 *   safe      → accent-trust (emphasized)
 *
 * The "critical" level pulses to draw attention without
 * being obnoxious — a slow, subtle scale+glow loop.
 */
import { motion } from 'framer-motion';
import { pulseOnAlert } from '../../lib/motion';
import './RiskBadge.css';

const SEVERITY_MAP = {
  critical: { className: 'risk-badge--critical', pulse: true },
  high:     { className: 'risk-badge--high',     pulse: false },
  medium:   { className: 'risk-badge--medium',   pulse: false },
  low:      { className: 'risk-badge--low',      pulse: false },
  safe:     { className: 'risk-badge--safe',      pulse: false },
};

export function RiskBadge({ severity = 'medium', label, className = '' }) {
  const config = SEVERITY_MAP[severity] || SEVERITY_MAP.medium;
  const displayLabel = label || severity.charAt(0).toUpperCase() + severity.slice(1);

  return (
    <motion.span
      className={`risk-badge ${config.className} ${className}`}
      variants={pulseOnAlert}
      initial="idle"
      animate={config.pulse ? 'alert' : 'idle'}
    >
      <span className="risk-badge__dot" />
      {displayLabel}
    </motion.span>
  );
}
