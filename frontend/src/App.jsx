/**
 * SafeNet AI — Application Root
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navigation } from './components/ui';
import DesignSystemPage from './pages/DesignSystemPage/DesignSystemPage';
import Dashboard from './components/dashboard/Dashboard';
import LandingPage from './pages/LandingPage/LandingPage';
import NoteChecker from './pages/NoteChecker/NoteChecker';
import NumberChecker from './pages/NumberChecker/NumberChecker';
import './App.css';

function App() {
  return (
    <BrowserRouter>
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
