/**
 * SafeNet AI — API Layer
 *
 * This module abstracts all data fetching. Currently, it returns
 * mocked JSON data with a simulated network delay.
 * When the backend is ready, simply replace the `setTimeout` blocks
 * with real `fetch()` calls.
 */

import mockDashboardFeed from '../mocks/mockDashboardFeed.json';
import mockHotspots from '../mocks/mockHotspots.json';
import mockCaseEvidence from '../mocks/mockCaseEvidence.json';
import mockChatResponses from '../mocks/mockChatResponses.json';

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export async function getDashboardFeed() {
  await delay(600); // Simulate network latency
  return mockDashboardFeed;
}

export async function getHotspots() {
  await delay(800);
  return mockHotspots;
}

export async function getCaseEvidence(eventId) {
  await delay(500);
  // Return specific mock if it exists, otherwise return a default mock
  return mockCaseEvidence[eventId] || Object.values(mockCaseEvidence)[0];
}

export async function askCitizenShield(query) {
  await delay(1000); // Chatbots take a moment to "think"
  
  // For simulation, just return a canned response based on sequence or randomness
  // Here we just return the full mock transcript to the UI to handle, 
  // or ideally the UI sends a query and gets 1 response back.
  // For the sake of the mock, we'll return a random response from the bot.
  const botResponses = mockChatResponses.filter(m => m.sender === 'bot');
  const response = botResponses[Math.floor(Math.random() * botResponses.length)];
  
  return {
    ...response,
    id: `msg-${Date.now()}`,
    timestamp: new Date().toISOString()
  };
}

export async function generateIncidentReport(caseId) {
  await delay(1500); // Simulating PDF generation / backend crunching
  return { success: true, reportUrl: `/reports/${caseId}.pdf` };
}
