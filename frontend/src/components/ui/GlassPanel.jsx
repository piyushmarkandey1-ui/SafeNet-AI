/**
 * GlassPanel — Translucent elevated container
 *
 * A frosted-glass card with a subtle border, backdrop blur,
 * and a soft glow on hover. Used as the primary container
 * for dashboards, modals, and content sections.
 */
import { motion } from 'framer-motion';
import { scaleInOnHover } from '../../lib/motion';
import './GlassPanel.css';

export function GlassPanel({
  children,
  className = '',
  hoverable = true,
  glowColor = 'risk',
  as = 'div',
  ...props
}) {
  const Component = hoverable ? motion.div : as;
  const glowClass = `glass-panel--glow-${glowColor}`;

  const motionProps = hoverable
    ? {
        variants: scaleInOnHover,
        initial: 'rest',
        whileHover: 'hover',
        whileTap: 'tap',
      }
    : {};

  return (
    <Component
      className={`glass-panel ${glowClass} ${className}`}
      {...motionProps}
      {...props}
    >
      {children}
    </Component>
  );
}
