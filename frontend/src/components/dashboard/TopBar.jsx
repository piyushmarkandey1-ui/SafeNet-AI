import { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldAlert, Network, Map, Shield, Flag, MoreVertical, Home, Search, Hash } from 'lucide-react';
import { AmdStatusPanel } from './AmdStatusPanel';
import './TopBar.css';

const MODULES = [
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
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

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

        {/* 3-dots Dropdown Navigation */}
        <div className="topbar__menu-container" ref={menuRef}>
          <button 
            className="btn-kebab-menu cursor-target" 
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="Menu"
          >
            <MoreVertical size={20} />
          </button>
          
          {isMenuOpen && (
            <div className="topbar__dropdown">
              <Link to="/" className="dropdown-item" onClick={() => setIsMenuOpen(false)}>
                <Home size={16} />
                <span>Home</span>
              </Link>
              <Link to="/note-checker" className="dropdown-item" onClick={() => setIsMenuOpen(false)}>
                <Search size={16} />
                <span>Note Checker</span>
              </Link>
              <Link to="/number-checker" className="dropdown-item" onClick={() => setIsMenuOpen(false)}>
                <Hash size={16} />
                <span>Number Checker</span>
              </Link>
              <button 
                className="dropdown-item" 
                onClick={() => {
                  setIsMenuOpen(false);
                  window.dispatchEvent(new CustomEvent('open-citizen-shield'));
                }}
              >
                <Shield size={16} />
                <span>Citizen Help Bot</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

