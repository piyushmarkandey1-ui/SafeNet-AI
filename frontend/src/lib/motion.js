/**
 * SafeNet AI — Motion Vocabulary
 *
 * Reusable Framer Motion variant sets for the entire application.
 * All motion is precise and functional — short durations, confident
 * ease-out curves. Nothing bouncy, nothing playful.
 */

/* ─── Easing Curves ─── */
const easeOut = [0.16, 1, 0.3, 1];
const easeInOut = [0.65, 0, 0.35, 1];

/* ─── Fade In Up ─── */
export const fadeInUp = {
  hidden: {
    opacity: 0,
    y: 24,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: easeOut,
    },
  },
  exit: {
    opacity: 0,
    y: -12,
    transition: {
      duration: 0.25,
      ease: easeInOut,
    },
  },
};

/* ─── Fade In (no vertical shift) ─── */
export const fadeIn = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.35, ease: easeOut },
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.2, ease: easeInOut },
  },
};

/* ─── Stagger Children ─── */
export const staggerChildren = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
};

/* ─── Stagger item (pair with staggerChildren on parent) ─── */
export const staggerItem = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: easeOut },
  },
};

/* ─── Scale In on Hover ─── */
export const scaleInOnHover = {
  rest: { scale: 1 },
  hover: {
    scale: 1.03,
    transition: { duration: 0.25, ease: easeOut },
  },
  tap: {
    scale: 0.98,
    transition: { duration: 0.1, ease: easeOut },
  },
};

/* ─── Pulse on Alert ─── */
export const pulseOnAlert = {
  idle: {
    scale: 1,
    boxShadow: '0 0 0px rgba(224, 90, 51, 0)',
  },
  alert: {
    scale: [1, 1.04, 1],
    boxShadow: [
      '0 0 0px rgba(224, 90, 51, 0)',
      '0 0 16px rgba(224, 90, 51, 0.5)',
      '0 0 0px rgba(224, 90, 51, 0)',
    ],
    transition: {
      duration: 1.8,
      repeat: Infinity,
      ease: easeInOut,
    },
  },
};

/* ─── Slide In From Left ─── */
export const slideInLeft = {
  hidden: { opacity: 0, x: -32 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.4, ease: easeOut },
  },
};

/* ─── Shimmer (for skeleton loaders) ─── */
export const shimmer = {
  initial: { backgroundPosition: '-200% 0' },
  animate: {
    backgroundPosition: '200% 0',
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'linear',
    },
  },
};

/* ─── Page transition wrapper ─── */
export const pageTransition = {
  initial: { opacity: 0, y: 12 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: easeOut },
  },
  exit: {
    opacity: 0,
    y: -12,
    transition: { duration: 0.2, ease: easeInOut },
  },
};
