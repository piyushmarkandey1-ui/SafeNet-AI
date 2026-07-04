import { motion, AnimatePresence } from 'framer-motion';
import { GlassPanel, RiskBadge, SkeletonGroup, Skeleton } from '../ui';
import { fadeInUp, staggerChildren, staggerItem } from '../../lib/motion';
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

  return (
    <div className="risk-feed">
      <h2 className="feed-header">Live Risk Feed</h2>
      <motion.div 
        className="feed-list"
        variants={staggerChildren}
        initial="hidden"
        animate="visible"
      >
        <AnimatePresence mode="popLayout">
          {items.map((item) => {
            const Icon = TYPE_ICONS[item.type] || AlertTriangle;
            const isSelected = selectedId === item.id;

            return (
              <motion.div
                key={item.id}
                layout
                variants={staggerItem}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.3 }}
              >
                <GlassPanel
                  hoverable
                  glowColor={item.severity === 'critical' || item.severity === 'high' ? 'risk' : 'trust'}
                  className={cn('feed-item', isSelected && 'feed-item--selected')}
                  onClick={() => onSelect(item)}
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
              </motion.div>
            );
          })}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
