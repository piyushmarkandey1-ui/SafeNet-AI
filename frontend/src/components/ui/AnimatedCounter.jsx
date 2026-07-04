/**
 * AnimatedCounter — Smooth number count-up
 *
 * Uses Framer Motion's useSpring and useMotionValue to
 * smoothly interpolate between number values. The counter
 * animates when `value` prop changes.
 */
import { useEffect, useRef } from 'react';
import { useMotionValue, useSpring, motion, useTransform } from 'framer-motion';
import './AnimatedCounter.css';

export function AnimatedCounter({
  value = 0,
  duration = 0.8,
  decimals = 0,
  prefix = '',
  suffix = '',
  className = '',
}) {
  const motionValue = useMotionValue(0);
  const spring = useSpring(motionValue, {
    stiffness: 80,
    damping: 20,
    duration,
  });
  const display = useTransform(spring, (latest) => {
    return `${prefix}${Number(latest).toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })}${suffix}`;
  });

  const prevValue = useRef(value);

  useEffect(() => {
    prevValue.current = value;
    motionValue.set(value);
  }, [value, motionValue]);

  return (
    <motion.span className={`animated-counter ${className}`}>
      {display}
    </motion.span>
  );
}
