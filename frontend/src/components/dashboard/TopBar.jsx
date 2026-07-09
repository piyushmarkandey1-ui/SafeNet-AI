import { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldAlert, Shield, Flag, Menu, Home, Search, Hash } from 'lucide-react';
import { AmdStatusPanel } from './AmdStatusPanel';
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

