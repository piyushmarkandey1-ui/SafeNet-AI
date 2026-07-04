/**
 * Skeleton — Shimmer loading placeholder
 *
 * Renders a pulsing shimmer bar to indicate loading state.
 * Supports width/height/borderRadius customization.
 * Uses a CSS gradient animation (no JS animation overhead).
 */
import './Skeleton.css';

export function Skeleton({
  width = '100%',
  height = '1rem',
  borderRadius,
  className = '',
  variant = 'text',
}) {
  const radiusMap = {
    text: 'var(--radius-sm)',
    card: 'var(--radius-lg)',
    circle: '50%',
    badge: '100px',
  };

  const resolvedRadius = borderRadius || radiusMap[variant] || radiusMap.text;

  return (
    <div
      className={`skeleton ${className}`}
      style={{
        width,
        height,
        borderRadius: resolvedRadius,
      }}
      role="status"
      aria-label="Loading"
    />
  );
}

/**
 * SkeletonGroup — Multiple skeleton lines for paragraph placeholders
 */
export function SkeletonGroup({ lines = 3, gap = '10px', className = '' }) {
  return (
    <div className={`skeleton-group ${className}`} style={{ gap }}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          width={i === lines - 1 ? '65%' : '100%'}
          height="0.875rem"
        />
      ))}
    </div>
  );
}
