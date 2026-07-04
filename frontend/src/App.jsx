/**
 * SafeNet AI — Application Root
 *
 * Sets up React Router with the design system preview
 * route and a placeholder home route.
 */
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import DesignSystemPage from './pages/DesignSystemPage/DesignSystemPage';
import './App.css';

function Home() {
  return (
    <div className="home">
      <div className="home__content">
        <p className="home__label">SafeNet AI</p>
        <h1 className="home__title">Command Center</h1>
        <p className="home__subtitle">
          Unified digital public safety intelligence platform.
          <br />
          Modules will be built here after design approval.
        </p>
        <Link to="/design-system" className="home__link">
          View Design System →
        </Link>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/design-system" element={<DesignSystemPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
