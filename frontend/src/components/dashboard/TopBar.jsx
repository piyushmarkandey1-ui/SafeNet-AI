import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Play, Activity, ScanLine } from 'lucide-react';
import { GlassPanel } from '../ui';
import './TopBar.css';

const MODULES = [
  { id: 'scam', name: 'Scam Call Detector' },
  { id: 'vision', name: 'Counterfeit Vision' },
  { id: 'graph', name: 'Fraud Graph' },
  { id: 'geo', name: 'Geospatial Heatmap' },
  { id: 'chat', name: 'Citizen Shield' },
];

export function TopBar({ onSimulate }) {
  const navigate = useNavigate();
  const [isSimulating, setIsSimulating] = useState(false);

  const handleSimulate = () => {
    setIsSimulating(true);
    onSimulate();
    setTimeout(() => setIsSimulating(false), 5000);
  };

  return (
    <header className="topbar">
      <div className="topbar__brand">
        <ShieldAlert className="topbar__logo" size={24} />
        <h1 className="topbar__title">SafeNet AI Command Center</h1>
      </div>

      <div className="topbar__modules">
        {MODULES.map((mod) => (
          <div key={mod.id} className="topbar__module-status">
            <span className="status-dot healthy" />
            <span className="status-name">{mod.name}</span>
          </div>
        ))}
      </div>

      <div className="topbar__actions">
        <button
          className="btn-note-check"
          onClick={() => navigate('/note-checker')}
          title="Open Note Checker"
        >
          <ScanLine size={16} />
          <span>Check Note</span>
        </button>
        <button
          className="btn-simulate"
          onClick={handleSimulate}
          disabled={isSimulating}
        >
          {isSimulating ? <Activity className="animate-spin" size={16} /> : <Play size={16} />}
          <span>{isSimulating ? 'Simulating...' : 'Simulate Scenario'}</span>
        </button>
      </div>
    </header>
  );
}
