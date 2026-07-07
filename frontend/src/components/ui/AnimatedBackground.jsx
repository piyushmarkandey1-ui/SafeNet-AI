import React from 'react';
import './AnimatedBackground.css';

/**
 * A fluid, animated background component inspired by React Bits "ColorBends".
 * Uses CSS mesh gradients and subtle noise to create a futuristic vibe
 * that perfectly aligns with the SafeNet AI dark neon theme.
 */
export default function AnimatedBackground() {
  return (
    <div className="color-bends-container">
      <div className="color-bends-noise"></div>
      <div className="color-bends-blob blob-1"></div>
      <div className="color-bends-blob blob-2"></div>
      <div className="color-bends-blob blob-3"></div>
    </div>
  );
}
