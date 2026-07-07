import { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { TopBar } from './TopBar';
import { RiskFeed } from './RiskFeed';
import { CrimeMap } from './CrimeMap';
import { EvidencePanel } from './EvidencePanel';
import { CitizenShieldChat } from './CitizenShieldChat';
import { getDashboardFeed, getHotspots, getCaseEvidence, simulateScenario } from '../../lib/api';
import './DashboardLayout.css';

export default function Dashboard() {
  const [feedItems, setFeedItems] = useState([]);
  const [hotspots, setHotspots] = useState([]);
  const [loadingFeed, setLoadingFeed] = useState(true);
  const [loadingHotspots, setLoadingHotspots] = useState(true);
  
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [evidenceData, setEvidenceData] = useState(null);
  const [loadingEvidence, setLoadingEvidence] = useState(false);

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
  }, []);

  const handleSelectEvent = async (event) => {
    if (selectedEvent?.id === event.id) {
      setSelectedEvent(null);
      setEvidenceData(null);
      return;
    }
    
    setSelectedEvent(event);
    setLoadingEvidence(true);
    const data = await getCaseEvidence(event.id);
    setEvidenceData(data);
    setLoadingEvidence(false);
  };

  const handleSimulate = async () => {
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
        location: { lat: 40.7580, lng: -73.9855, name: "Midtown, NY" },
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
    
    const pollInterval = setInterval(async () => {
      pollCount++;
      const updatedFeed = await getDashboardFeed();
      setFeedItems(updatedFeed);
      
      if (pollCount >= maxPolls) {
        clearInterval(pollInterval);
      }
    }, 1500);
  };

  return (
    <div className="dashboard-layout">
      <TopBar onSimulate={handleSimulate} />
      
      <main className="dashboard-content">
        <aside className="pane-left" id="risk-feed-panel">
          <RiskFeed 
            items={feedItems} 
            loading={loadingFeed} 
            selectedId={selectedEvent?.id}
            onSelect={handleSelectEvent}
          />
        </aside>
        
        <section className="pane-center" id="crime-map-panel">
          <CrimeMap 
            hotspots={hotspots} 
            loading={loadingHotspots} 
            selectedEvent={selectedEvent}
          />
        </section>

        <AnimatePresence>
          {selectedEvent && (
            <aside className="pane-right" key="evidence-panel">
              <EvidencePanel 
                event={selectedEvent} 
                evidence={evidenceData} 
                loading={loadingEvidence} 
              />
            </aside>
          )}
        </AnimatePresence>
      </main>

      <CitizenShieldChat />
    </div>
  );
}
