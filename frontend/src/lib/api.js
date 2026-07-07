/**
 * SafeNet AI — API Layer (Vercel Production + Local Dev)
 *
 * This module abstracts all data fetching with automatic fallback
 * to local development or Vercel production endpoints.
 *
 * All backend endpoints are prefixed with /api/ so that:
 *   - In local dev  → requests hit http://localhost:8000/api/...
 *   - On Vercel     → requests hit https://your-app.vercel.app/api/...
 *     (which routes to the api/index.py serverless function)
 */

import mockDashboardFeed from '../mocks/mockDashboardFeed.json';
import mockHotspots from '../mocks/mockHotspots.json';
import mockCaseEvidence from '../mocks/mockCaseEvidence.json';
import mockChatResponses from '../mocks/mockChatResponses.json';

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Auto-detect API base URL
const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    // On Vercel: use the current origin — /api/* rewrites handle routing
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      return window.location.origin;
    }
  }
  // Local development: FastAPI uvicorn server
  return 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

export async function getDashboardFeed() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/orchestrator/dashboard-feed`);
    if (!res.ok) throw new Error('Network response was not ok');
    const data = await res.json();
    // Return backend data, or fallback to mock if backend feed is empty (initial load)
    return data.length > 0 ? data : mockDashboardFeed;
  } catch (err) {
    console.warn("Orchestrator not running or reachable. Falling back to mocks.");
    await delay(600);
    return mockDashboardFeed;
  }
}

export async function getHotspots() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/geo/hotspots`);
    if (!res.ok) throw new Error(`Geo API returned ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`Hotspots API unavailable: ${err.message}. Falling back to mocks.`);
    await delay(800);
    return mockHotspots;
  }
}

export async function getCaseEvidence(eventId) {
  try {
    // Strategy: the feed event stores the actual entity IDs (phone/account numbers)
    // in its `entities` array. Resolve against the orchestrator feed first,
    // then the legacy aggregate feed, and try every candidate until one works.
    const candidateIds = [eventId];

    for (const feedUrl of [
      `${API_BASE_URL}/api/orchestrator/dashboard-feed`,
      `${API_BASE_URL}/api/dashboard/feed`,
    ]) {
      try {
        const feedRes = await fetch(feedUrl);
        if (feedRes.ok) {
          const feed = await feedRes.json();
          const matchingEvent = feed.find(e => e.id === eventId);
          if (matchingEvent?.entities?.length > 0) {
            candidateIds.push(...matchingEvent.entities);
          }
        }
      } catch (_) { /* ignore and try the next source */ }
    }

    const uniqueCandidates = [...new Set(candidateIds.filter(Boolean))];
    let lastError = null;
    for (const entityId of uniqueCandidates) {
      const res = await fetch(`${API_BASE_URL}/api/graph/case/${encodeURIComponent(entityId)}`);
      if (res.ok) return await res.json();
      lastError = new Error(`Graph API returned ${res.status} for ${entityId}`);
    }
    throw lastError || new Error('No graph entity candidates found');
  } catch (err) {
    console.warn(`Graph case API unavailable for "${eventId}": ${err.message}. Falling back to mock.`);
    await delay(500);
    return mockCaseEvidence[eventId] || Object.values(mockCaseEvidence)[0];
  }
}

/**
 * Sends a question to the Citizen Shield conversational agent.
 *
 * @param {string} query    - User's natural-language question.
 * @param {string} language - ISO 639-1 code (default 'en'). Pass 'hi' for Hindi.
 * @returns {Promise<{ id, sender, text, timestamp, isActionable, intent, risk_level }>}
 */
export async function askCitizenShield(query, language = 'en') {
  try {
    const res = await fetch(`${API_BASE_URL}/api/shield/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, language }),
    });
    if (!res.ok) throw new Error(`Shield API returned ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`Citizen Shield API unavailable: ${err.message}. Falling back to mock.`);
    await delay(1000);
    const botResponses = mockChatResponses.filter(m => m.sender === 'bot');
    const response = botResponses[Math.floor(Math.random() * botResponses.length)];
    return {
      ...response,
      id: `msg-${Date.now()}`,
      timestamp: new Date().toISOString(),
    };
  }
}

export async function generateIncidentReport(caseId) {
  await delay(1500); // Simulating PDF generation / backend crunching
  return { success: true, reportUrl: `/reports/${caseId}.pdf` };
}

/**
 * Sends a currency note image to the backend for counterfeit detection.
 * Returns authenticity verdict, confidence, denomination, and Grad-CAM overlay.
 *
 * @param {File} imageFile - The image File object from a file input.
 * @returns {Promise<{
 *   is_fake: boolean,
 *   confidence: number,
 *   denomination: string,
 *   denomination_raw: string,
 *   auth_class: string,
 *   gradcam_overlay: string,
 *   recommendation: string,
 *   severity: string,
 *   event_id: string,
 *   timestamp: string
 * }>}
 */
export async function checkNote(imageFile) {
  const formData = new FormData();
  formData.append('file', imageFile);

  try {
    const res = await fetch(`${API_BASE_URL}/api/vision/check-note`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Note check failed');
    }
    return await res.json();
  } catch (err) {
    console.warn('Backend not reachable for note check:', err.message);
    // Mock fallback so UI stays functional during development
    await delay(800);
    return {
      is_fake: true,
      confidence: 0.923,
      denomination: '₹500',
      denomination_raw: '500',
      auth_class: 'fake',
      gradcam_overlay: '',
      recommendation: 'ALERT: High-confidence counterfeit detected. (MOCK — backend offline)',
      severity: 'critical',
      event_id: `cv-mock-${Date.now()}`,
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Triggers the orchestrator's demo scenario — drives the "Simulate Scenario" button.
 * Fires off a sequence of correlated events to demonstrate compound risk scoring.
 *
 * @returns {Promise<{ status: string, message: string }>}
 */
export async function simulateScenario() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/orchestrator/simulate`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`Orchestrator returned ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`Orchestrator simulate API unavailable: ${err.message}. Mock fallback.`);
    await delay(500);
    return { status: 'simulation_started', message: 'Mock scenario (backend offline).', mock: true };
  }
}
