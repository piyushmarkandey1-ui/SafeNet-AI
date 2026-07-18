import { GlassPanel, RiskBadge, SkeletonGroup, Skeleton } from '../ui';
import { AlertTriangle, PhoneCall, Link2, MapPin, CheckCircle } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useIsMobile } from '../../hooks/useIsMobile';
import LogoLoop from '../ui/LogoLoop';
import './RiskFeed.css';

const TYPE_ICONS = {
  SCAM_CALL: PhoneCall,
  COUNTERFEIT: AlertTriangle,
  FRAUD_NETWORK: Link2,
  SAFE_EVENT: CheckCircle,
};

export function RiskFeed({ items, loading, selectedId, onSelect, hideMobileHeader }) {
  const isMobile = useIsMobile();

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

  // Define the custom renderer for each feed item
  const renderFeedItem = (item) => {
    const Icon = TYPE_ICONS[item.type] || AlertTriangle;
    const isSelected = selectedId === item.id;
    
    // Safe accessors to prevent crashes
    const scoreVal = typeof item.score === 'number' ? item.score.toFixed(1) : 'N/A';
    const locName = item.location?.name || 'Unknown Location';

    return (
      <GlassPanel
        hoverable
        glowColor={item.severity === 'critical' || item.severity === 'high' ? 'risk' : 'trust'}
        className={cn('feed-item', isSelected && 'feed-item--selected')}
        onClick={() => onSelect(item)}
        style={{ flexShrink: 0, width: '100%', marginBottom: 0 }}
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
            <span>{locName}</span>
          </div>
          <div className="feed-item__score">
            Score: {scoreVal}
          </div>
        </div>
      </GlassPanel>
    );
  };

  return (
    <div className="risk-feed" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', height: '100%' }}>
      {!(hideMobileHeader && isMobile) && (
        <h2 className="feed-header">Live Risk Feed</h2>
      )}
      <div style={{ flex: 1, minHeight: 0, position: 'relative', overflow: 'hidden' }}>
        {items.length > 0 ? (
          isMobile ? (
             <div className="hide-scrollbar" style={{ overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: '12px', paddingBottom: '20px' }}>
                {items.map((item) => (
                   <div key={item.id}>
                      {renderFeedItem(item)}
                   </div>
                ))}
             </div>
          ) : (
            <LogoLoop
              logos={items}
              speed={60}
              direction="up"
              gap={12}
              hoverSpeed={10}
              allowMouseScroll={true}
              renderItem={renderFeedItem}
              style={{ height: '100%' }}
              className="feed-logoloop"
            />
          )
        ) : (
          <div className="feed-empty-state">
             <AlertTriangle size={32} opacity={0.3} />
             <p>No risk events detected yet.</p>
             <span>Feed will update automatically.</span>
          </div>
        )}
      </div>
    </div>
  );
}
