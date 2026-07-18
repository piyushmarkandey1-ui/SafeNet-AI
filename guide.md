# 🛡️ SafeNet AI — Complete Developer & Feature Guide

> **SafeNet AI** is an intelligent, real-time public safety platform designed to protect Indian citizens from digital and physical crime. It combines multi-modal AI threat detection, a live geospatial risk heatmap, a conversational fraud-protection assistant, counterfeit currency verification, and suspicious number lookup — all in a unified interface.

---

## 📌 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Tech Stack](#3-tech-stack)
4. [Frontend Pages & Features](#4-frontend-pages--features)
5. [Backend Modules & API Endpoints](#5-backend-modules--api-endpoints)
6. [AI & LLM Integration (Fireworks AI on AMD)](#6-ai--llm-integration-fireworks-ai-on-amd)
7. [Data Flow & Logic](#7-data-flow--logic)
8. [Environment Variables](#8-environment-variables)
9. [Local Development Setup](#9-local-development-setup)
10. [Deployment (Vercel)](#10-deployment-vercel)
11. [Integrating Fireworks AI into Your Own Project](#11-integrating-fireworks-ai-into-your-own-project)

---

## 1. Project Overview

SafeNet AI was built for the **ET Hackathon** as a unified digital safety intelligence platform. It addresses the most common crime categories affecting Indian citizens today:

| Threat Type              | Module Handling It                     |
|--------------------------|----------------------------------------|
| UPI / Payment Fraud      | Scam Detector + Citizen Shield Chat    |
| Counterfeit Currency     | Counterfeit Vision (CV model)          |
| Scam Calls & Phishing    | Number Checker + Citizen Shield Chat   |
| Identity / Aadhaar Fraud | Citizen Shield Chat + Fraud Graph      |
| Online Scams             | Scam Detector + Citizen Shield Chat    |
| Geographic Crime Hotspots | Geospatial Module + Crime Heatmap     |

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vite + React)                   │
│                                                                  │
│  Landing Page → Dashboard → Note Checker → Number Checker        │
│                     ↓                                            │
│   CrimeMap  |  RiskFeed  |  CitizenShieldChat  |  EvidencePanel  │
│   TopBar    |  ReportIncidentModal              |  AmdStatusPanel │
└────────────────────────────┬────────────────────────────────────┘
                             │  REST API (/api/*)
┌────────────────────────────▼────────────────────────────────────┐
│                    BACKEND (FastAPI on Vercel Serverless)         │
│                                                                  │
│  /api/shield/ask        → Citizen Shield (LLM conversational)    │
│  /api/detect            → Scam Detector (pattern + ML)           │
│  /api/note-check        → Counterfeit Vision (image AI)          │
│  /api/number-check      → Number Checker (reputation lookup)     │
│  /api/dashboard/feed    → Aggregated live risk feed              │
│  /api/hotspots          → Geospatial risk heatmap data           │
│  /api/evidence          → Fraud Graph evidence                   │
│  /api/provider-status   → AMD / LLM provider health             │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              AI INFERENCE LAYER (Fireworks AI — AMD Instinct)    │
│                                                                  │
│  Primary Model:  GLM-5p1 (ChatGLM 108B, AMD-hosted)             │
│  Fallback 1:     Google Gemini API                               │
│  Fallback 2:     OpenAI API                                      │
│  Fallback 3:     Offline grounded templates (no API required)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Tech Stack

### Frontend
| Layer | Technology | Purpose |
|---|---|---|
| Framework | **React 18 + Vite** | Component-based SPA with hot module reload |
| Routing | **React Router v6** | Multi-page SPA routing |
| Animations | **Framer Motion** | Micro-animations, page transitions |
| Map | **Leaflet.js + React-Leaflet** | Interactive geospatial crime heatmap |
| Styling | **Vanilla CSS** | Custom design system (glassmorphism dark-mode) |
| Icons | **Lucide React** | Consistent icon library |
| HTTP | **Fetch API** | Calling the backend /api/* routes |
| Font | **Google Fonts — Inter** | Modern, legible typography |
| Cursor | **Custom TargetCursor** | Premium interactive crosshair cursor |

### Backend
| Layer | Technology | Purpose |
|---|---|---|
| Framework | **FastAPI 0.115** | Async REST API with automatic Swagger docs |
| Server | **Uvicorn** | ASGI server for local development |
| Serverless Adapter | **Mangum** | Wraps FastAPI for Vercel serverless functions |
| AI Inference | **Fireworks AI (via OpenAI SDK)** | AMD-hosted LLM inference |
| Image Processing | **Pillow + NumPy** | Counterfeit currency image analysis |
| Env Management | **python-dotenv** | Local .env file loading |
| Graph Engine | **NetworkX** (lazy-loaded) | Fraud entity network graph |
| LLM Orchestration | **LangGraph + LangChain Core** | Multi-step AI agent workflows |
| Vision Fallback | **Google Gemini Vision API** | Backup for counterfeit image analysis |

### Infrastructure
| Component | Service |
|---|---|
| Hosting (Frontend + API) | **Vercel** (Serverless) |
| Container (Local) | **Docker + Docker Compose** |
| Source Control | **GitHub** |
| AI GPU Cluster | **AMD Instinct via Fireworks AI** |

---

## 4. Frontend Pages & Features

### 🏠 `/` — Landing Page
- Hero section with animated tagline and call-to-action buttons
- Feature highlights showing all four protection modules
- Navigation to Dashboard, Note Checker, Number Checker

---

### 📊 `/dashboard` — Live Intelligence Dashboard

The main command centre. Consists of 6 sub-components:

#### 🗺️ CrimeMap
- Full-screen interactive Leaflet.js map of India
- Plots crime hotspots as color-coded risk circles (green → critical red)
- Plots user-submitted incident reports as pinned markers
- Clicking a hotspot or report opens the Evidence Panel on the right
- Severity-based pulse animations on critical events

#### 📡 RiskFeed
- Vertical scrolling ticker of live threat events
- Events are aggregated from all backend modules via `/api/dashboard/feed`
- Each card shows: severity badge, event type, city, timestamp, and score
- Clicking any event selects it and shows its evidence in the right panel
- Smooth continuous auto-scroll animation (6x item duplication to prevent jitter)

#### 🔍 EvidencePanel (Right Sidebar)
- Appears on the right when an event is selected
- Shows: Compound Risk Score, AI summary, key evidence items, linked fraud entities
- **Generate Incident Report** button creates an official report
- **Remove Report** button (only shown for your own reports) deletes it from the map and feed immediately

#### 💬 CitizenShieldChat
- Floating chat bubble (bottom-right corner) powered by Citizen Shield AI
- Context-aware conversational assistant for fraud help
- Multi-language support: English, Hindi, Tamil, Telugu, Bengali, Marathi
- Response includes: natural language advice + risk level badge + next steps
- Built on Fireworks AI glm-5p1 (AMD GPU-backed)

#### 📋 ReportIncidentModal (Report an Incident)
- 2-step modal accessible from the TopBar "Report Incident" button
- **Step 1 — Incident Details**: Type selector (8 categories), Severity selector, Title, Description
- **Step 2 — Location + Contact**: City search (any Indian city — type or dropdown), Landmark, Optional name + phone
- Submitted reports immediately appear on the CrimeMap and RiskFeed
- Reports persist in localStorage across browser sessions
- User can delete their own reports via the EvidencePanel

#### ⚙️ AmdStatusPanel
- Real-time panel showing which LLM providers are active
- Pings `/api/provider-status` every 30 seconds
- Shows: Fireworks AI (AMD) status, Gemini fallback, OpenAI fallback
- Green pulse = active, red = unavailable

---

### 🧾 `/note-checker` — Counterfeit Currency Detector

- Drag-and-drop or click-to-upload interface for currency note images
- AI-powered image analysis detects signs of counterfeit notes
- Reports: Authenticity verdict, Confidence score, Suspicious features list
- Supported: Rs.500, Rs.200, Rs.100, Rs.50 notes
- Backend: `POST /api/note-check` → Counterfeit Vision module

---

### 📞 `/number-checker` — Scam Number Lookup

- Input any Indian phone number (+91 format)
- AI checks the number against scam pattern databases and known fraud entities
- Reports: Risk level, Scam type likelihood, Fraud entity links
- Backend: `POST /api/number-check` → Number Checker module

---

## 5. Backend Modules & API Endpoints

### Module A: Scam Detector (`/api/detect`)
**File:** `backend/app/scam_detector/`

- **Input:** Raw text, phone number, UPI ID, or transaction description
- **Logic:** Pattern matching on known scam keywords → LLM classification → confidence scoring
- **Output:** Intent classification, pattern match score (0–100), detected tactics list
- **Key endpoint:** `POST /api/detect`

---

### Module B: Counterfeit Vision (`/api/note-check`)
**File:** `backend/app/counterfeit_vision/`

- **Input:** Image of a currency note (JPG/PNG, up to 10MB)
- **Logic:** Pillow + NumPy for pixel analysis → Gemini Vision API for feature extraction → authenticity scoring
- **Output:** Verdict (GENUINE / COUNTERFEIT / SUSPICIOUS), confidence %, flagged features
- **Key endpoint:** `POST /api/note-check`

---

### Module C: Fraud Graph (`/api/evidence`, `/api/case-evidence/{id}`)
**File:** `backend/app/fraud_graph/`

- **Logic:** NetworkX-based entity graph linking phone numbers, UPI IDs, and accounts involved in known fraud cases
- **Output:** Linked fraud entities, risk classification, evidence summary
- **Key endpoint:** `GET /api/case-evidence/{event_id}`

---

### Module D: Geospatial (`/api/hotspots`)
**File:** `backend/app/geospatial/`

- **Logic:** Aggregates crime event coordinates → generates risk hotspot clusters for the map
- **Output:** List of { lat, lng, severity, type, count } hotspot objects
- **Key endpoint:** `GET /api/hotspots`

---

### Module E: Citizen Shield Chat (`/api/shield/ask`)
**File:** `backend/app/citizen_shield/`

- **Input:** `{ query: string, language: "en"|"hi"|"ta"|"te"|"bn"|"mr" }`
- **Logic:**
  1. Keyword-based intent detection (30+ rule patterns)
  2. Grounding facts pulled from Module A (pattern score) and Module C (fraud graph)
  3. System prompt + grounding facts + user message sent to Fireworks AI glm-5p1
  4. Response cleaned to strip any internal reasoning artifacts
  5. Risk level + next steps extracted from response via regex post-processor
- **Output:** `{ text, risk_level, intent, next_steps, isActionable }`
- **Key endpoint:** `POST /api/shield/ask`

---

### Module F: Number Checker (`/api/number-check`)
**File:** `backend/app/number_checker/`

- **Input:** `{ number: string }`
- **Logic:** Pattern analysis on number format + LLM-based fraud likelihood scoring
- **Output:** Risk verdict, scam type, linked fraud entities
- **Key endpoint:** `POST /api/number-check`

---

### Utility Endpoints
| Endpoint | Method | Description |
|---|---|---|
| `/api/dashboard/feed` | GET | Aggregated live risk feed (all modules, newest-first, max 50) |
| `/api/provider-status` | GET | LLM provider health and AMD inference status |
| `/api/debug-llm` | GET | Debug endpoint to verify active Fireworks AI key and model |
| `/api/simulate` | POST | Triggers a simulated threat scenario for demo/testing |
| `/health` | GET | Backend health check for load balancers and Docker |

---

## 6. AI & LLM Integration (Fireworks AI on AMD)

### Why Fireworks AI?
Fireworks AI hosts open-source LLMs on **AMD Instinct MI300X GPU clusters**, satisfying the hackathon's AMD platform requirement. Every inference call made from SafeNet AI runs on AMD hardware.

### Primary Model
| Model | ID | Reason |
|---|---|---|
| ChatGLM-5p1 | `accounts/fireworks/models/glm-5p1` | 108B parameters. Direct, clean responses. No reasoning monologue leak. |

### Fallback Chain
```
1. Fireworks AI (glm-5p1, AMD Instinct)  ← primary
2. Google Gemini API                      ← if FIREWORKS_API_KEY missing
3. OpenAI API                             ← if GEMINI_API_KEY missing
4. Offline grounded template              ← if all keys missing
```

### Reasoning Leak Prevention
The `clean_thinking_process()` function in `fireworks_client.py` post-processes every LLM response:
1. Strips `<think>...</think>` XML blocks
2. Strips `Thinking Process:` sections delimited by `---`
3. **Block-splitting fallback**: If a response contains draft markers (Draft 1:, Formulate the Response:, Grounding facts), the response is split by double newlines and the last clean paragraph is extracted as the final answer

### Citizen Shield System Prompt Design
The agent is instructed to:
- **Never repeat** the same safety script twice — vary phrasing and examples
- Ask **exactly ONE** clarifying question if the user's message is too vague
- Build on **conversation history** — never re-introduce itself
- Respond **only in the user's selected language**
- Wrap all internal reasoning in `<think>` tags (filtered before display)

---

## 7. Data Flow & Logic

### Flow: User Says "I received a suspicious call"

```
User types "I received a suspicious call from 9876543210"
         ↓
CitizenShieldChat.jsx → POST /api/shield/ask
         ↓
agent.py → Intent detection ("suspicious_call")
         ↓
agent.py → Calls Module A (scam_detector) for pattern score
         ↓
agent.py → Calls Module C (fraud_graph) for entity lookup
         ↓
agent.py → Builds system prompt + grounding facts
         ↓
fireworks_client.py → Calls glm-5p1 on Fireworks AI (AMD)
         ↓
fireworks_client.py → clean_thinking_process(response)
         ↓
agent.py → Extracts risk_level + next_steps from response text
         ↓
API returns { text, risk_level, intent, next_steps }
         ↓
CitizenShieldChat.jsx renders clean conversational response + badge
```

### Flow: User Uploads Currency Note Image

```
User drops image on Note Checker page
         ↓
NoteChecker.jsx → POST /api/note-check (multipart/form-data)
         ↓
counterfeit_vision/api.py → Pillow + NumPy analysis
         ↓
→ Gemini Vision API for feature detection (security strip, watermark, etc.)
         ↓
Returns { verdict, confidence, features_flagged }
         ↓
NoteChecker.jsx renders verdict card with animated confidence ring
```

### Flow: User Submits Incident Report

```
User fills ReportIncidentModal (type, severity, title, description, city)
         ↓
ReportIncidentModal.jsx validates both steps
         ↓
Finds city lat/lng from INDIAN_CITIES lookup table
Adds random jitter to prevent map pin stacking
         ↓
Creates report object { id, type, severity, location, isUserReport: true }
         ↓
Dashboard.jsx → handleNewReport()
  → Prepends to feedItems state (appears in RiskFeed immediately)
  → Prepends to userReports state
  → Persists to localStorage
         ↓
CrimeMap.jsx renders pin at city coordinates
```

---

## 8. Environment Variables

Create a `.env` file in `/backend/` with:

```env
# Primary: Fireworks AI (AMD Instinct GPU inference)
FIREWORKS_API_KEY=fw_xxxxxxxxxxxxxxxx
FIREWORKS_BASE_URL=https://api.fireworks.ai/inference/v1

# Fallback 1: Google Gemini
GEMINI_API_KEY=AIzaSy_xxxxxxxxxxxxxxxx

# Fallback 2: OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx

# App Config
ENVIRONMENT=development
FRONTEND_DIST_PATH=
```

For **Vercel deployment**, add these same keys in:
> Vercel Dashboard → Your Project → Settings → Environment Variables

---

## 9. Local Development Setup

### Prerequisites
- Node.js 18+
- Python 3.11+
- Git

### Step 1: Clone the repo
```bash
git clone https://github.com/piyushmarkandey1-ui/SafeNet-AI.git
cd SafeNet-AI
```

### Step 2: Start the backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# or: source .venv/bin/activate # Mac/Linux

pip install -r requirements.txt
cp .env.example .env            # then add your API keys

uvicorn app.main:app --reload --port 8000
```

Backend → http://localhost:8000  
Swagger docs → http://localhost:8000/docs

### Step 3: Start the frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend → http://localhost:5173

### Step 4: Using Docker (all-in-one)
```bash
docker-compose up --build
```

App → http://localhost:8000

---

## 10. Deployment (Vercel)

The project is configured for **zero-config Vercel deployment**.

### How it works
1. `vercel.json` tells Vercel to:
   - Build the React frontend with `cd frontend && npm run build`
   - Serve the built files from `frontend/dist/`
   - Route all `/api/*` requests to `/api/index.py` (FastAPI via Mangum)

2. `api/index.py` is the Vercel serverless entry point — it imports the FastAPI app and wraps it with Mangum for serverless compatibility.

### Deploy command
```bash
vercel --prod
```

Or simply push to `main` — Vercel auto-deploys on every git push.

---

## 11. Integrating Fireworks AI into Your Own Project

Since Fireworks AI is **OpenAI-API compatible**, integration is extremely simple.

### Python
```bash
pip install openai python-dotenv
```

```python
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("FIREWORKS_API_KEY"),
    base_url="https://api.fireworks.ai/inference/v1"
)

response = client.chat.completions.create(
    model="accounts/fireworks/models/glm-5p1",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=600
)

print(response.choices[0].message.content)
```

### JavaScript / Node.js
```bash
npm install openai dotenv
```

```javascript
import { OpenAI } from 'openai';
import 'dotenv/config';

const client = new OpenAI({
  apiKey: process.env.FIREWORKS_API_KEY,
  baseURL: 'https://api.fireworks.ai/inference/v1',
});

const response = await client.chat.completions.create({
  model: 'accounts/fireworks/models/glm-5p1',
  messages: [{ role: 'user', content: 'Hello!' }],
  temperature: 0.7,
  max_tokens: 600,
});

console.log(response.choices[0].message.content);
```

---

## 📁 Project File Structure

```
SafeNet-AI/
├── frontend/                    # React + Vite SPA
│   └── src/
│       ├── pages/
│       │   ├── LandingPage/     # / route
│       │   ├── NoteChecker/     # /note-checker route
│       │   └── NumberChecker/   # /number-checker route
│       ├── components/
│       │   ├── dashboard/       # All dashboard components
│       │   │   ├── Dashboard.jsx
│       │   │   ├── CrimeMap.jsx
│       │   │   ├── RiskFeed.jsx
│       │   │   ├── CitizenShieldChat.jsx
│       │   │   ├── EvidencePanel.jsx
│       │   │   ├── TopBar.jsx
│       │   │   ├── AmdStatusPanel.jsx
│       │   │   └── ReportIncidentModal.jsx
│       │   └── ui/              # Reusable UI components
│       └── lib/
│           ├── api.js           # All backend API calls
│           └── motion.js        # Framer Motion variants
│
├── backend/                     # FastAPI Python backend
│   └── app/
│       ├── citizen_shield/      # Module E: Conversational AI agent
│       ├── counterfeit_vision/  # Module B: Currency note image AI
│       ├── fraud_graph/         # Module C: Fraud entity network
│       ├── geospatial/          # Module D: Crime hotspot mapping
│       ├── number_checker/      # Module F: Scam number lookup
│       ├── orchestrator/        # Multi-agent coordination
│       ├── scam_detector/       # Module A: Text scam detection
│       ├── fireworks_client.py  # Centralised AI inference wrapper
│       └── main.py              # FastAPI app + route registration
│
├── api/
│   └── index.py                 # Vercel serverless entry point (Mangum)
│
├── vercel.json                  # Vercel build + routing config
├── docker-compose.yml           # Docker all-in-one setup
├── requirements.txt             # Python dependencies (Vercel/prod)
└── guide.md                     # This file
```

---

*Built with love for the ET Hackathon · SafeNet AI — Protecting every citizen.*
