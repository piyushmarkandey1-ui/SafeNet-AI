/**
 * DesignSystemPage — Visual reference for all design tokens & components
 *
 * Displays every color swatch, type scale step, spacing token,
 * and interactive component primitive in a single scrollable page.
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { GlassPanel, RiskBadge, AnimatedCounter, Skeleton, SkeletonGroup } from '../../components/ui';
import { fadeInUp, staggerChildren, staggerItem, fadeIn } from '../../lib/motion';
import './DesignSystemPage.css';

/* ─── Color Swatches ─── */
const COLORS = [
  { group: 'Backgrounds', items: [
    { name: 'Base',     var: '--bg-base',     hex: '#0A0E14' },
    { name: 'Surface',  var: '--bg-surface',  hex: '#111923' },
    { name: 'Elevated', var: '--bg-elevated', hex: '#1A2332' },
    { name: 'Overlay',  var: '--bg-overlay',  hex: '#243044' },
  ]},
  { group: 'Accent', items: [
    { name: 'Risk',    var: '--accent-risk',    hex: '#E05A33' },
    { name: 'Trust',   var: '--accent-trust',   hex: '#2EC4B6' },
    { name: 'Warning', var: '--accent-warning', hex: '#F2A93B' },
  ]},
  { group: 'Text', items: [
    { name: 'Primary',   var: '--text-primary',   hex: '#F0F2F5' },
    { name: 'Secondary', var: '--text-secondary', hex: '#94A3B8' },
    { name: 'Muted',     var: '--text-muted',     hex: '#64748B' },
    { name: 'Disabled',  var: '--text-disabled',  hex: '#475569' },
  ]},
];

/* ─── Type Scale ─── */
const TYPE_SCALE = [
  { name: 'Display',  var: '--text-display', size: '3.5rem', tracking: 'tight',  weight: '700', font: 'display' },
  { name: 'H1',       var: '--text-h1',      size: '2.5rem', tracking: 'tight',  weight: '700', font: 'display' },
  { name: 'H2',       var: '--text-h2',      size: '2rem',   tracking: 'snug',   weight: '600', font: 'display' },
  { name: 'H3',       var: '--text-h3',      size: '1.5rem', tracking: 'snug',   weight: '600', font: 'display' },
  { name: 'H4',       var: '--text-h4',      size: '1.25rem',tracking: 'normal', weight: '500', font: 'display' },
  { name: 'Body',     var: '--text-body',     size: '1rem',   tracking: 'normal', weight: '400', font: 'body'    },
  { name: 'Small',    var: '--text-sm',       size: '0.875rem',tracking: 'normal', weight: '400', font: 'body'   },
  { name: 'Caption',  var: '--text-caption',  size: '0.75rem', tracking: 'wide',   weight: '500', font: 'body'   },
];

/* ─── Radius Tokens ─── */
const RADII = [
  { name: 'sm', value: '6px' },
  { name: 'md', value: '8px' },
  { name: 'lg', value: '10px' },
  { name: 'xl', value: '14px' },
];

export default function DesignSystemPage() {
  /* For AnimatedCounter demo */
  const [counterVal, setCounterVal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const t1 = setTimeout(() => setCounterVal(14728), 800);
    const t2 = setTimeout(() => setIsLoading(false), 2500);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);

  return (
    <div className="ds-page">
      {/* ─── Header ─── */}
      <motion.header className="ds-header" variants={fadeInUp} initial="hidden" animate="visible">
        <p className="ds-header__label">SafeNet AI</p>
        <h1 className="ds-header__title">Design System</h1>
        <p className="ds-header__subtitle">
          Tokens, typography, and component primitives for a high-trust
          command-center interface.
        </p>
      </motion.header>

      {/* ═══════════ COLORS ═══════════ */}
      <motion.section className="ds-section" variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }}>
        <h2 className="ds-section__title">Color System</h2>
        {COLORS.map((group) => (
          <div key={group.group} className="ds-color-group">
            <h3 className="ds-color-group__label">{group.group}</h3>
            <motion.div className="ds-swatches" variants={staggerChildren} initial="hidden" whileInView="visible" viewport={{ once: true }}>
              {group.items.map((c) => (
                <motion.div key={c.var} className="ds-swatch" variants={staggerItem}>
                  <div
                    className="ds-swatch__color"
                    style={{ background: `var(${c.var})` }}
                  />
                  <span className="ds-swatch__name">{c.name}</span>
                  <span className="ds-swatch__hex">{c.hex}</span>
                  <code className="ds-swatch__var">{c.var}</code>
                </motion.div>
              ))}
            </motion.div>
          </div>
        ))}
      </motion.section>

      {/* ═══════════ TYPOGRAPHY ═══════════ */}
      <motion.section className="ds-section" variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }}>
        <h2 className="ds-section__title">Type Scale</h2>
        <div className="ds-type-scale">
          {TYPE_SCALE.map((t) => (
            <motion.div key={t.name} className="ds-type-row" variants={staggerItem}>
              <div className="ds-type-row__meta">
                <span className="ds-type-row__name">{t.name}</span>
                <code className="ds-type-row__spec">{t.size} · {t.weight} · {t.tracking}</code>
              </div>
              <p
                className="ds-type-row__sample"
                style={{
                  fontSize: `var(${t.var})`,
                  fontFamily: t.font === 'display' ? 'var(--font-display)' : 'var(--font-body)',
                  fontWeight: t.weight,
                  letterSpacing: `var(--tracking-${t.tracking})`,
                  lineHeight: t.size >= '1.5rem' ? 'var(--leading-tight)' : 'var(--leading-normal)',
                }}
              >
                SafeNet Intelligence
              </p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* ═══════════ SPACING & RADIUS ═══════════ */}
      <motion.section className="ds-section" variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }}>
        <h2 className="ds-section__title">Border Radius</h2>
        <div className="ds-radii">
          {RADII.map((r) => (
            <div key={r.name} className="ds-radius-item">
              <div className="ds-radius-item__box" style={{ borderRadius: r.value }} />
              <span className="ds-radius-item__label">radius-{r.name}</span>
              <code className="ds-radius-item__value">{r.value}</code>
            </div>
          ))}
        </div>
      </motion.section>

      {/* ═══════════ GLASS PANEL ═══════════ */}
      <motion.section className="ds-section" variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }}>
        <h2 className="ds-section__title">GlassPanel</h2>
        <p className="ds-section__desc">Hover or tap to see scale and glow effects.</p>
        <div className="ds-component-grid">
          <GlassPanel glowColor="risk">
            <h4 className="ds-demo-label">Risk Glow</h4>
            <p className="ds-demo-text">Frosted glass container with red-orange radial glow on hover. Backdrop blur, thin border, soft elevation.</p>
          </GlassPanel>
          <GlassPanel glowColor="trust">
            <h4 className="ds-demo-label">Trust Glow</h4>
            <p className="ds-demo-text">Same glass structure with teal glow variant. Used for verified/safe content areas.</p>
          </GlassPanel>
          <GlassPanel hoverable={false} className="ds-panel-static">
            <h4 className="ds-demo-label">Static (no hover)</h4>
            <p className="ds-demo-text">Non-interactive variant for layout containers where hover feedback isn't needed.</p>
          </GlassPanel>
        </div>
      </motion.section>

      {/* ═══════════ RISK BADGES ═══════════ */}
      <motion.section className="ds-section" variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }}>
        <h2 className="ds-section__title">RiskBadge</h2>
        <p className="ds-section__desc">The "Critical" badge pulses continuously to draw attention.</p>
        <motion.div className="ds-badge-row" variants={staggerChildren} initial="hidden" whileInView="visible" viewport={{ once: true }}>
          {['critical', 'high', 'medium', 'low', 'safe'].map((sev) => (
            <motion.div key={sev} variants={staggerItem}>
              <RiskBadge severity={sev} />
            </motion.div>
          ))}
        </motion.div>
      </motion.section>

      {/* ═══════════ ANIMATED COUNTER ═══════════ */}
      <motion.section className="ds-section" variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }}>
        <h2 className="ds-section__title">AnimatedCounter</h2>
        <p className="ds-section__desc">Click the button to randomize. Counters spring-animate to new values.</p>
        <div className="ds-counter-demo">
          <GlassPanel glowColor="trust" className="ds-counter-card">
            <span className="ds-counter-card__label">Threats Analyzed</span>
            <AnimatedCounter value={counterVal} className="ds-counter-card__value" />
          </GlassPanel>
          <GlassPanel glowColor="risk" className="ds-counter-card">
            <span className="ds-counter-card__label">Active Alerts</span>
            <AnimatedCounter value={Math.round(counterVal * 0.032)} className="ds-counter-card__value" />
          </GlassPanel>
          <GlassPanel glowColor="trust" className="ds-counter-card">
            <span className="ds-counter-card__label">Resolution Rate</span>
            <AnimatedCounter value={counterVal > 0 ? 94.7 : 0} decimals={1} suffix="%" className="ds-counter-card__value" />
          </GlassPanel>
        </div>
        <button
          className="ds-counter-btn"
          onClick={() => setCounterVal(Math.floor(Math.random() * 50000) + 1000)}
        >
          Randomize Values
        </button>
      </motion.section>

      {/* ═══════════ SKELETON ═══════════ */}
      <motion.section className="ds-section" variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }}>
        <h2 className="ds-section__title">Skeleton Loaders</h2>
        <p className="ds-section__desc">CSS-only shimmer. No spinners.</p>
        <div className="ds-skeleton-demo">
          <GlassPanel hoverable={false}>
            <div className="ds-skeleton-card">
              <Skeleton variant="circle" width="48px" height="48px" />
              <div className="ds-skeleton-card__body">
                <Skeleton width="40%" height="1rem" />
                <SkeletonGroup lines={3} />
              </div>
            </div>
          </GlassPanel>
          <GlassPanel hoverable={false}>
            <div className="ds-skeleton-badges">
              <Skeleton variant="badge" width="80px" height="24px" />
              <Skeleton variant="badge" width="100px" height="24px" />
              <Skeleton variant="badge" width="60px" height="24px" />
            </div>
            <Skeleton variant="card" width="100%" height="120px" className="ds-skeleton-block" />
          </GlassPanel>
        </div>
      </motion.section>

      {/* ═══════════ MOTION ═══════════ */}
      <motion.section className="ds-section" variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }}>
        <h2 className="ds-section__title">Motion Vocabulary</h2>
        <p className="ds-section__desc">All animations use 200–400ms ease-out curves. Precise, not playful.</p>
        <div className="ds-motion-grid">
          <MotionDemo name="fadeInUp" desc="Primary entrance for content blocks">
            <DemoBlock variants={fadeInUp} />
          </MotionDemo>
          <MotionDemo name="fadeIn" desc="Subtle opacity-only entrance">
            <DemoBlock variants={fadeIn} />
          </MotionDemo>
          <MotionDemo name="staggerChildren" desc="Sequenced list item reveals">
            <motion.div className="ds-motion-stagger" variants={staggerChildren}>
              {[0, 1, 2, 3].map(i => (
                <motion.div key={i} className="ds-motion-stagger__item" variants={staggerItem} />
              ))}
            </motion.div>
          </MotionDemo>
          <MotionDemo name="scaleInOnHover" desc="Interactive feedback on cards">
            <p className="ds-motion-hint">↑ See GlassPanel demos above</p>
          </MotionDemo>
          <MotionDemo name="pulseOnAlert" desc="Continuous draw for critical items">
            <p className="ds-motion-hint">↑ See Critical RiskBadge above</p>
          </MotionDemo>
        </div>
      </motion.section>

      {/* ─── Footer ─── */}
      <footer className="ds-footer">
        <p>SafeNet AI Design System v0.1</p>
      </footer>
    </div>
  );
}

/* ─── Helper: Motion Demo Wrapper ─── */
function MotionDemo({ name, desc, children }) {
  const [play, setPlay] = useState(false);

  return (
    <div className="ds-motion-demo">
      <div className="ds-motion-demo__header">
        <code className="ds-motion-demo__name">{name}</code>
        <span className="ds-motion-demo__desc">{desc}</span>
      </div>
      <div className="ds-motion-demo__stage">
        <motion.div
          key={play ? 'a' : 'b'}
          initial="hidden"
          animate="visible"
        >
          {children}
        </motion.div>
      </div>
      <button className="ds-motion-demo__replay" onClick={() => setPlay(p => !p)}>
        Replay
      </button>
    </div>
  );
}

/* ─── Helper: Animated Block ─── */
function DemoBlock({ variants }) {
  return (
    <motion.div className="ds-demo-block" variants={variants} />
  );
}
