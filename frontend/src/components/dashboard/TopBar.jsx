import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Play, Activity, ScanLine, PhoneCall, AlertTriangle, Network, Map, Shield, Phone, Flag } from 'lucide-react';
import { AmdStatusPanel } from './AmdStatusPanel';
import './TopBar.css';

const MODULES = [
  {
    id: 'scam',
    name: 'Scam Detector',
    icon: PhoneCall,
    tooltip: 'View Risk Feed',
    action: 'scroll',
    target: 'risk-feed-panel',
  },
  {
    id: 'vision',
    name: 'Note Checker',
    icon: AlertTriangle,
    tooltip: 'Open Note Checker',
    action: 'navigate',
    target: '/note-checker',
  },
  {
    id: 'graph',
    name: 'Fraud Graph',
    icon: Network,
    tooltip: 'Click any event in Risk Feed',
    action: 'scroll',
    target: 'risk-feed-panel',
  },
  {
    id: 'geo',
    name: 'Heatmap',
    icon: Map,
    tooltip: 'View Crime Map',
    action: 'scroll',
    target: 'crime-map-panel',
  },
  {
    id: 'chat',
    name: 'Citizen Shield',
    icon: Shield,
    tooltip: 'Open AI Chat',
    action: 'event',
    target: 'open-citizen-shield',
  },
];

export function TopBar({ onSimulate, onReport }) {
  const navigate = useNavigate();
  const [isSimulating, setIsSimulating] = useState(false);
  const [activeModule, setActiveModule] = useState(null);

  const handleSimulate = () => {
    setIsSimulating(true);
    onSimulate();
    setTimeout(() => setIsSimulating(false), 5000);
  };

  const handleModuleClick = (mod) => {
    setActiveModule(mod.id);
    setTimeout(() => setActiveModule(null), 1500);

    if (mod.action === 'navigate') {
      navigate(mod.target);
    } else if (mod.action === 'scroll') {
      const el = document.getElementById(mod.target);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else if (mod.action === 'event') {
      window.dispatchEvent(new CustomEvent(mod.target));
    }
  };

  return (
    <header className="topbar">
      <div className="topbar__brand">
        <ShieldAlert className="topbar__logo" size={24} />
        <h1 className="topbar__title">SafeNet AI Command Center</h1>
      </div>

      <nav className="topbar__modules">
        {MODULES.map((mod) => {
          const Icon = mod.icon;
          return (
            <button
              key={mod.id}
              className={`topbar__module-btn ${activeModule === mod.id ? 'active' : ''}`}
              onClick={() => handleModuleClick(mod)}
              title={mod.tooltip}
            >
              <span className="status-dot healthy" />
              <Icon size={13} className="module-icon" />
              <span className="status-name">{mod.name}</span>
            </button>
          );
        })}
      </nav>

      <div className="topbar__actions">
        <AmdStatusPanel />
        <button
          className="btn-report-incident cursor-target"
          onClick={onReport}
          title="Report a crime or incident in your area"
        >
          <Flag size={16} />
          <span>Report Incident</span>
        </button>
        <button
          className="btn-simulate cursor-target"
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

