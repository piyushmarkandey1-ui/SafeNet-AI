import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { AnimatePresence } from 'framer-motion';
import { TopBar } from './TopBar';
import { RiskFeed } from './RiskFeed';
import { CrimeMap } from './CrimeMap';
import { EvidencePanel } from './EvidencePanel';
import { CitizenShieldChat } from './CitizenShieldChat';
import ReportIncidentModal from './ReportIncidentModal';
import { ChevronDown } from 'lucide-react';
import { getDashboardFeed, getHotspots, getCaseEvidence, simulateScenario } from '../../lib/api';
import './DashboardLayout.css';

const USER_REPORTS_KEY = 'safenet_user_reports';

/** Validates that a stored report has the required shape before rendering */
function isValidReport(r) {
  return (
    r &&
    typeof r.id === 'string' &&
    typeof r.type === 'string' &&
    typeof r.severity === 'string' &&
    r.location &&
    typeof r.location.lat === 'number' &&
    typeof r.location.lng === 'number'
  );
}

export default function Dashboard() {
  const [feedItems, setFeedItems] = useState([]);
  const [hotspots, setHotspots] = useState([]);
  const [loadingFeed, setLoadingFeed] = useState(true);
  const [loadingHotspots, setLoadingHotspots] = useState(true);
  
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [evidenceData, setEvidenceData] = useState(null);
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [feedOpen, setFeedOpen] = useState(false); // collapsed by default on mobile

  // Ref to track simulate polling interval so it can be cleared on unmount
  const pollIntervalRef = useRef(null);

  // User-submitted reports — persisted in localStorage, validated on load
  const [userReports, setUserReports] = useState(() => {
    try {
      const raw = JSON.parse(localStorage.getItem(USER_REPORTS_KEY) || '[]');
      // Filter out any malformed entries so a corrupted localStorage can't break the dashboard
      return Array.isArray(raw) ? raw.filter(isValidReport) : [];
    } catch {
      return [];
    }
  });

  const handleNewReport = useCallback((report) => {
    setUserReports(prev => {
      const updated = [report, ...prev];
      localStorage.setItem(USER_REPORTS_KEY, JSON.stringify(updated));
      return updated;
    });
    // Also push into the live risk feed so it shows up immediately
    setFeedItems(prev => [report, ...prev]);
  }, []);

  useEffect(() => {
    async function loadInitialData() {
      const [feed, spots] = await Promise.all([
        getDashboardFeed(),
        getHotspots()
      ]);
      setFeedItems(feed);
      setLoadingFeed(false);
      setHotspots(spots);
      setLoadingHotspots(false);
    }
    loadInitialData();

    // Cleanup: clear any simulate polling interval on unmount
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const handleSelectEvent = useCallback(async (event) => {
    if (selectedEvent?.id === event.id) {
      setSelectedEvent(null);
      setEvidenceData(null);
      return;
    }
    
    setSelectedEvent(event);
    setLoadingEvidence(true);
    setEvidenceData(null); // Clear stale data before loading new
    try {
      const data = await getCaseEvidence(event.id);
      setEvidenceData(data);
    } catch {
      // api.js swallows errors and falls back to mock — if we still get here, just show nothing
      setEvidenceData(null);
    } finally {
      setLoadingEvidence(false);
    }
  }, [selectedEvent]);

  const handleSimulate = useCallback(async () => {
    // Trigger the real orchestrator simulation
    const result = await simulateScenario();
    console.log('Simulation started:', result);

    if (result.mock) {
      const newEvent = {
        id: `sim-${Date.now()}`,
        type: "SCAM_CALL",
        severity: "critical",
        timestamp: new Date().toISOString(),
        title: "SIMULATED: Phishing Attack Detected",
        description: "Backend offline; showing local demo event.",
        location: { lat: 28.6139, lng: 77.2090, name: "New Delhi" },
        entities: ["+1-999-555-1234"],
        score: 99.1
      };
      setFeedItems(prev => [newEvent, ...prev]);
      return;
    }

    if (result.events && result.events.length > 0) {
      // Vercel serverless environment (synchronous completion)
      setFeedItems(result.events);
      return;
    }

    // Polling fallback for local long-running background tasks
    let pollCount = 0;
    const maxPolls = 8;
    
    // Clear any existing poll first
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    pollIntervalRef.current = setInterval(async () => {
      pollCount++;
      const updatedFeed = await getDashboardFeed();
      setFeedItems(updatedFeed);
      
      if (pollCount >= maxPolls) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }, 1500);
  }, []);

  const handleDeleteReport = useCallback((id) => {
    // Guard: only delete reports that are user-submitted
    setUserReports(prev => {
      const report = prev.find(r => r.id === id);
      if (!report || !report.isUserReport) return prev; // safety guard
      const updated = prev.filter(r => r.id !== id);
      localStorage.setItem(USER_REPORTS_KEY, JSON.stringify(updated));
      return updated;
    });
    setFeedItems(prev => prev.filter(r => r.id !== id || !r.isUserReport));
    if (selectedEvent?.id === id) {
      setSelectedEvent(null);
      setEvidenceData(null);
    }
  }, [selectedEvent]);

  // Memoize arrays passed as props to prevent unnecessary child re-renders
  const memoFeedItems = useMemo(() => feedItems, [feedItems]);
  const memoHotspots = useMemo(() => hotspots, [hotspots]);
  const memoUserReports = useMemo(() => userReports, [userReports]);

  return (
    <div className="dashboard-layout">
      <TopBar onSimulate={handleSimulate} onReport={() => setShowReportModal(true)} />
      
      <main className="dashboard-content">
        {/* Map — always visible and prominent on mobile */}
        <section className="pane-center" id="crime-map-panel">
          <CrimeMap 
            hotspots={memoHotspots} 
            loading={loadingHotspots} 
            selectedEvent={selectedEvent}
            userReports={memoUserReports}
          />
        </section>

        {/* Risk Feed — collapsible accordion on mobile, always open on desktop */}
        <aside className="pane-left" id="risk-feed-panel">
          {/* Mobile accordion toggle (hidden on desktop via CSS) */}
          <button
            className="feed-accordion-toggle"
            onClick={() => setFeedOpen(o => !o)}
            aria-expanded={feedOpen}
            aria-controls="feed-accordion-body"
          >
            <span className="feed-accordion-label">
              <span className="feed-accordion-dot" />
              Live Risk Feed
              {memoFeedItems.length > 0 && (
                <span className="feed-accordion-count">{memoFeedItems.length}</span>
              )}
            </span>
            <ChevronDown
              size={18}
              className={`feed-accordion-chevron${feedOpen ? ' open' : ''}`}
            />
          </button>

          {/* Body — always shown on desktop, toggles on mobile */}
          <div id="feed-accordion-body" className={`feed-accordion-body${feedOpen ? ' feed-accordion-body--open' : ''}`}>
            <RiskFeed 
              items={memoFeedItems} 
              loading={loadingFeed} 
              selectedId={selectedEvent?.id}
              onSelect={handleSelectEvent}
              hideMobileHeader
            />
          </div>
        </aside>
        
        <AnimatePresence>
          {selectedEvent && (
            <aside className="pane-right" key="evidence-panel" aria-label="Case Evidence Panel">
              <EvidencePanel 
                event={selectedEvent} 
                evidence={evidenceData} 
                loading={loadingEvidence} 
                onDeleteReport={selectedEvent.isUserReport ? () => handleDeleteReport(selectedEvent.id) : undefined}
              />
            </aside>
          )}
        </AnimatePresence>
      </main>

      <CitizenShieldChat />

      {showReportModal && (
        <ReportIncidentModal
          onClose={() => setShowReportModal(false)}
          onSubmit={(r) => { handleNewReport(r); setShowReportModal(false); }}
        />
      )}
    </div>
  );
}
