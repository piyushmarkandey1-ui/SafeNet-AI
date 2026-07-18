import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassPanel, AnimatedCounter, RiskBadge, Skeleton, SkeletonGroup } from '../ui';
import { FileText, Network, CheckCircle2, AlertCircle, Trash2 } from 'lucide-react';
import { slideInLeft, staggerChildren, staggerItem } from '../../lib/motion';
import { generateIncidentReport } from '../../lib/api';
import './EvidencePanel.css';

export function EvidencePanel({ event, evidence, loading, onDeleteReport }) {
  const [reportState, setReportState] = useState('idle'); // idle | loading | success

  if (!event) return null;

  const handleGenerateReport = async () => {
    setReportState('loading');
    await generateIncidentReport(evidence?.caseId);
    setReportState('success');
    setTimeout(() => setReportState('idle'), 3000);
  };

  return (
    <motion.div 
      className="evidence-panel"
      initial={{ width: 0, opacity: 0, borderLeftWidth: 0 }}
      animate={{ width: 400, opacity: 1, borderLeftWidth: 1 }}
      exit={{ width: 0, opacity: 0, borderLeftWidth: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="evidence-panel__inner">
        {loading ? (
          <div className="p-4 flex-col gap-6">
            <Skeleton width="60%" height="24px" />
            <SkeletonGroup lines={4} />
            <GlassPanel hoverable={false} className="mt-4">
              <Skeleton width="100%" height="150px" />
            </GlassPanel>
          </div>
        ) : (
          <motion.div 
            className="evidence-content"
            variants={staggerChildren}
            initial="hidden"
            animate="visible"
          >
            <motion.div className="ev-header" variants={staggerItem}>
              <h2 className="ev-title">Case Evidence</h2>
              <RiskBadge severity={event.severity} />
            </motion.div>

            <motion.div variants={staggerItem}>
              <GlassPanel hoverable={false} className="score-card">
                <span className="score-label">Compound Risk Score</span>
                <div className="score-value">
                  <AnimatedCounter value={evidence.riskScore} decimals={1} />
                  <span className="score-max">/ 100</span>
                </div>
              </GlassPanel>
            </motion.div>

            <motion.div className="ev-section" variants={staggerItem}>
              <h3 className="section-title">Summary</h3>
              <p className="ev-summary">{evidence.summary}</p>
            </motion.div>

            <motion.div className="ev-section" variants={staggerItem}>
              <h3 className="section-title">Key Evidence</h3>
              <div className="ev-items">
                {evidence.evidenceItems.map((item, i) => (
                  <div key={i} className="ev-item">
                    {item.type === 'AUDIO_TRANSCRIPT' ? <FileText size={16} /> : <Network size={16} />}
                    <div className="ev-item-content">
                      <span className="ev-item-type">{item.type.replace('_', ' ')}</span>
                      <p className="ev-item-snippet">"{item.snippet}"</p>
                      <span className="ev-item-conf">Conf: {(item.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div className="ev-section" variants={staggerItem}>
              <h3 className="section-title">Linked Entities</h3>
              <div className="entities-list">
                {evidence.linkedEntities.map((ent, i) => (
                  <div key={i} className={`entity-chip entity--${ent.risk}`}>
                    {ent.id} ({ent.type})
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div className="ev-action" variants={staggerItem}>
              <p className="action-rec"><AlertCircle size={14}/> {evidence.recommendedAction}</p>
              
              <div style={{ display: 'flex', gap: '8px', width: '100%' }}>
                <button 
                  className={`btn-report ${reportState}`}
                  style={{ flex: 1 }}
                  onClick={handleGenerateReport}
                  disabled={reportState !== 'idle'}
                >
                  {reportState === 'idle' && 'Generate Incident Report'}
                  {reportState === 'loading' && <span className="shimmer-text">Generating...</span>}
                  {reportState === 'success' && (
                    <>
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                      >
                        <CheckCircle2 size={18} />
                      </motion.div>
                      Report Saved
                    </>
                  )}
                </button>

                {onDeleteReport && (
                  <button 
                    className="btn-report"
                    style={{ flex: 1, backgroundColor: 'rgba(255, 59, 59, 0.1)', color: '#ff3b3b', border: '1px solid rgba(255, 59, 59, 0.3)' }}
                    onClick={onDeleteReport}
                  >
                    <Trash2 size={16} style={{ marginRight: 6 }} />
                    Remove Report
                  </button>
                )}
              </div>
            </motion.div>

          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
