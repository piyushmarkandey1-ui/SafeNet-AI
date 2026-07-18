import { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldAlert, Shield, Flag, Menu, Home, Search, Hash } from 'lucide-react';
import { AmdStatusPanel } from './AmdStatusPanel';
import LineSidebar from '../ui/LineSidebar';
import './TopBar.css';

export function TopBar({ onSimulate, onReport }) {
  const navigate = useNavigate();
  const [isSimulating, setIsSimulating] = useState(false);
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

  return (
    <header className="topbar">
      <div className="topbar__brand">
        <ShieldAlert className="topbar__logo" size={24} />
        <h1 className="topbar__title">SafeNet AI Command Center</h1>
      </div>

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

        {/* Hamburger Dropdown Navigation */}
        <div className="topbar__menu-container" ref={menuRef}>
          <button 
            className="btn-kebab-menu cursor-target" 
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="Menu"
          >
            <Menu size={20} />
          </button>
          
          {isMenuOpen && (
            <div className="topbar__dropdown">
              <LineSidebar
                items={['Home', 'Note Checker', 'Number Checker', 'Citizen Help Bot']}
                accentColor="#ff6b35" // SafeNet-AI brand color (risk accent)
                textColor="#c4c4c4"
                markerColor="#3a4049" // border-accent
                showIndex={false}
                showMarker={true}
                proximityRadius={60}
                maxShift={10}
                markerLength={15}
                markerGap={10}
                tickScale={0}
                itemGap={14}
                fontSize={0.9}
                onItemClick={(index, label) => {
                  setIsMenuOpen(false);
                  if (label === 'Home') navigate('/');
                  else if (label === 'Note Checker') navigate('/note-checker');
                  else if (label === 'Number Checker') navigate('/number-checker');
                  else if (label === 'Citizen Help Bot') window.dispatchEvent(new CustomEvent('open-citizen-shield'));
                }}
              />
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

