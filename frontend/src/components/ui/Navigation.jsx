/**
 * SafeNet AI — Global Navigation Component
 * 
 * Provides consistent navigation across all pages with:
 * - Brand/logo with home link
 * - Main navigation items
 * - Active route highlighting
 * - Mobile responsive menu
 */
import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  ShieldAlert, 
  LayoutDashboard, 
  Banknote, 
  Phone, 
  Menu, 
  X,
  Home,
  Shield
} from 'lucide-react';
import './Navigation.css';

const NAV_ITEMS = [
  {
    path: '/',
    label: 'Home',
    icon: Home,
    description: 'Landing page'
  },
  {
    path: '/dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    description: 'Command center'
  },
  {
    path: '/note-checker',
    label: 'Note Checker',
    icon: Banknote,
    description: 'Counterfeit detection'
  },
  {
    path: '/number-checker',
    label: 'Number Checker',
    icon: Phone,
    description: 'Phone fraud analysis'
  }
];

export function Navigation() {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  const handleNavClick = (path) => {
    navigate(path);
    setMobileMenuOpen(false);
  };

  // Don't show navigation on landing page
  if (location.pathname === '/') {
    return null;
  }

  return (
    <nav className="global-nav">
      {/* Brand */}
      <button 
        className="global-nav__brand"
        onClick={() => handleNavClick('/')}
      >
        <ShieldAlert size={24} className="global-nav__logo" />
        <div className="global-nav__brand-text">
          <span className="global-nav__title">SafeNet AI</span>
          <span className="global-nav__subtitle">Fraud Intelligence Platform</span>
        </div>
      </button>

      {/* Desktop Navigation */}
      <ul className="global-nav__items">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          
          return (
            <li key={item.path}>
              <button
                className={`global-nav__link ${active ? 'global-nav__link--active' : ''}`}
                onClick={() => handleNavClick(item.path)}
                title={item.description}
              >
                <Icon size={18} className="global-nav__icon" />
                <span className="global-nav__label">{item.label}</span>
                {active && <span className="global-nav__active-indicator" />}
              </button>
            </li>
          );
        })}
      </ul>

      {/* Mobile Menu Toggle */}
      <button
        className="global-nav__mobile-toggle"
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        aria-label="Toggle navigation menu"
      >
        {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <>
          <div 
            className="global-nav__overlay"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="global-nav__mobile-menu">
            <div className="global-nav__mobile-header">
              <ShieldAlert size={20} />
              <span>SafeNet AI Navigation</span>
            </div>
            <ul className="global-nav__mobile-items">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.path);
                
                return (
                  <li key={item.path}>
                    <button
                      className={`global-nav__mobile-link ${active ? 'global-nav__mobile-link--active' : ''}`}
                      onClick={() => handleNavClick(item.path)}
                    >
                      <Icon size={20} />
                      <div className="global-nav__mobile-link-content">
                        <span className="global-nav__mobile-link-label">{item.label}</span>
                        <span className="global-nav__mobile-link-desc">{item.description}</span>
                      </div>
                      {active && <Shield size={16} className="global-nav__mobile-active-icon" />}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        </>
      )}
    </nav>
  );
}
