import { useRef, useEffect } from 'react';
import { GlassPanel, RiskBadge, SkeletonGroup, Skeleton } from '../ui';
import { AlertTriangle, PhoneCall, Link2, MapPin, CheckCircle } from 'lucide-react';
import { cn } from '../../lib/utils';
import './RiskFeed.css';

const TYPE_ICONS = {
  SCAM_CALL: PhoneCall,
  COUNTERFEIT: AlertTriangle,
  FRAUD_NETWORK: Link2,
  SAFE_EVENT: CheckCircle,
};

export function RiskFeed({ items, loading, selectedId, onSelect }) {
  const scrollRef = useRef(null);

  // Auto-scroll logic that allows native user scrolling
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    let rafId;
    let isHovered = false;

    const handleMouseEnter = () => (isHovered = true);
    const handleMouseLeave = () => (isHovered = false);

    el.addEventListener('mouseenter', handleMouseEnter);
    el.addEventListener('mouseleave', handleMouseLeave);

    const loop = () => {
      if (!isHovered) {
        el.scrollTop += 0.5; // Auto-scroll speed
        // If we've scrolled past the first half of the duplicated list, snap back to top seamlessly
        if (el.scrollTop >= el.scrollHeight / 2) {
          el.scrollTop = 0;
        }
      }
      rafId = requestAnimationFrame(loop);
    };

    rafId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(rafId);
      el.removeEventListener('mouseenter', handleMouseEnter);
      el.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [items]); // Re-bind if items change, though it shouldn't matter much

  if (loading) {
    return (
      <div className="risk-feed risk-feed--loading">
        <h2 className="feed-header">Live Risk Feed</h2>
        <div className="feed-list">
          {Array.from({ length: 5 }).map((_, i) => (
            <GlassPanel key={i} hoverable={false} className="feed-item-skeleton">
              <div className="flex-row">
                 <Skeleton variant="circle" width="32px" height="32px" />
                 <div className="flex-col w-full">
                    <Skeleton width="40%" />
                    <Skeleton width="100%" height="8px" />
                 </div>
              </div>
            </GlassPanel>
          ))}
        </div>
      </div>
    );
  }

  // Duplicate items for seamless infinite scroll
  const loopedItems = [...items, ...items];

  return (
    <div className="risk-feed" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <h2 className="feed-header">Live Risk Feed</h2>
      <div 
        ref={scrollRef}
        className="hide-scrollbar" 
        style={{ 
          flex: 1, 
          minHeight: 0, 
          overflowY: 'auto', 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '12px',
          paddingBottom: '20px'
        }}
      >
        {loopedItems.map((item, index) => {
          const Icon = TYPE_ICONS[item.type] || AlertTriangle;
          const isSelected = selectedId === item.id;

          return (
            <GlassPanel
              key={`${item.id}-${index}`}
              hoverable
              glowColor={item.severity === 'critical' || item.severity === 'high' ? 'risk' : 'trust'}
              className={cn('feed-item', isSelected && 'feed-item--selected')}
              onClick={() => onSelect(item)}
              style={{ flexShrink: 0 }}
            >
              <div className="feed-item__header">
                <div className={cn("icon-wrapper", `icon--${item.severity}`)}>
                  <Icon size={18} />
                </div>
                <div className="feed-item__meta">
                  <span className="feed-item__time">
                    {new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </span>
                  <RiskBadge severity={item.severity} />
                </div>
              </div>
              
              <h3 className="feed-item__title">{item.title}</h3>
              <p className="feed-item__desc">{item.description}</p>
              
              <div className="feed-item__footer">
                <div className="feed-item__location">
                  <MapPin size={12} />
                  <span>{item.location.name}</span>
                </div>
                <div className="feed-item__score">
                  Score: {item.score.toFixed(1)}
                </div>
              </div>
            </GlassPanel>
          );
        })}
      </div>
    </div>
  );
}
