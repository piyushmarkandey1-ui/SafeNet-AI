/**
 * SafeNet AI — Application Root
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DesignSystemPage from './pages/DesignSystemPage/DesignSystemPage';
import Dashboard from './components/dashboard/Dashboard';
import LandingPage from './pages/LandingPage/LandingPage';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/design-system" element={<DesignSystemPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
