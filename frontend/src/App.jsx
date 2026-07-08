/**
 * SafeNet AI — Application Root
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navigation } from './components/ui';
import TargetCursor from './components/ui/TargetCursor';
import DesignSystemPage from './pages/DesignSystemPage/DesignSystemPage';
import Dashboard from './components/dashboard/Dashboard';
import LandingPage from './pages/LandingPage/LandingPage';
import NoteChecker from './pages/NoteChecker/NoteChecker';
import NumberChecker from './pages/NumberChecker/NumberChecker';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      {/* Global custom cursor — desktop only (auto-hidden on mobile) */}
      <TargetCursor
        targetSelector="button:not(:disabled), a[href], .cursor-target, .topbar__module-btn, .btn-simulate, .btn-note-check, .btn-report-incident, .hero-btn, .cta-button, .rim-type-btn, .rim-severity-btn, .rim-btn-primary, .rim-btn-secondary, .drop-zone, .glass-panel, .risk-item, .mode-btn"
        spinDuration={3}
        hideDefaultCursor={true}
        parallaxOn={true}
        cursorColor="#2ec4b6"
        cursorColorOnTarget="#2ec4b6"
        hoverDuration={0.15}
      />
      <Navigation />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/note-checker" element={<NoteChecker />} />
        <Route path="/number-checker" element={<NumberChecker />} />
        <Route path="/design-system" element={<DesignSystemPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
