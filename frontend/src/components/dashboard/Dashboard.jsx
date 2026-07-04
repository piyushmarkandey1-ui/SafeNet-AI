import { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { TopBar } from './TopBar';
import { RiskFeed } from './RiskFeed';
import { CrimeMap } from './CrimeMap';
import { EvidencePanel } from './EvidencePanel';
import { CitizenShieldChat } from './CitizenShieldChat';
import { getDashboardFeed, getHotspots, getCaseEvidence } from '../../lib/api';
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
    // A quick sequence injecting fake events to simulate orchestrator streaming
    const newEvent = {
      id: `sim-${Date.now()}`,
      type: "SCAM_CALL",
      severity: "critical",
      timestamp: new Date().toISOString(),
      title: "SIMULATED: Phishing Attack Detected",
      description: "Real-time intercept triggered by orchestrator analysis.",
      location: { lat: 40.7580, lng: -73.9855, name: "Midtown, NY" },
      entities: ["+1-999-555-1234"],
      score: 99.1
    };

    setLoadingFeed(true);
    await new Promise(r => setTimeout(r, 800));
    setFeedItems(prev => [newEvent, ...prev]);
    setLoadingFeed(false);
  };

  return (
    <div className="dashboard-layout">
      <TopBar onSimulate={handleSimulate} />
      
      <main className="dashboard-content">
        <aside className="pane-left">
          <RiskFeed 
            items={feedItems} 
            loading={loadingFeed} 
            selectedId={selectedEvent?.id}
            onSelect={handleSelectEvent}
          />
        </aside>
        
        <section className="pane-center">
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
