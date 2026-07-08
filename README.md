# SafeNet AI 🛡️

**One Intelligence Layer. Five Threat Surfaces.**

> SafeNet AI is a unified digital public-safety intelligence platform built for the  
> **AMD Developer Hackathon: ACT II — Track 3 (Unicorn Track)** on lablab.ai.  
> It combines five AI-powered threat-detection modules behind a single LangGraph  
> orchestration agent, enabling citizens and law enforcement to detect, visualise,  
> and respond to fraud and financial crime in real time.

🌐 **Live Demo:** [safe-net-ai-sandy.vercel.app](https://safe-net-ai-sandy.vercel.app)  
📦 **GitHub:** [github.com/piyushmarkandey1-ui/SafeNet-AI](https://github.com/piyushmarkandey1-ui/SafeNet-AI)

---

## 🏆 AMD Hackathon: ACT II — Track 3

SafeNet AI is a **startup-grade product** targeting real fraud at scale in India.  
It is submitted under **Track 3 — Unicorn Track**, which is judged on:

| Criterion | How SafeNet AI addresses it |
|---|---|
| **Creativity & Originality** | First unified platform correlating scam calls + counterfeit notes + fraud rings + geospatial hotspots into one Compound Risk Score |
| **Product / Market Potential** | India sees ₹10,000+ crore in digital fraud annually — this is a real, underserved market |
| **Completeness** | Full frontend + backend + orchestrator + containerisation, all running end-to-end |
| **Use of AMD Platforms** | Fireworks AI (AMD Instinct GPUs) is the primary LLM provider across all 5 modules |

### Bonus Prize Target: Best AMD-Hosted Gemma Project ($2,000)

Citizen Shield (the conversational fraud-prevention agent) uses **Gemma 2** — Google DeepMind's open model — hosted on AMD hardware via Fireworks AI:

- **Gemma 2 9B** (`gemma2-9b-it`) — standard citizen queries
- **Gemma 2 27B** (`gemma2-27b-it`) — complex multi-turn conversations

Verify live: `GET /api/shield/gemma-info`

---

## 🤖 AMD & Fireworks AI Integration

All LLM inference in SafeNet AI runs on **AMD Instinct GPU clusters via Fireworks AI**.

```
FIREWORKS_API_KEY set?
  YES → Fireworks AI (AMD Instinct GPUs)
         ├── Gemma 2 9B   — citizen chat, standard
         ├── Gemma 2 27B  — citizen chat, complex
         ├── Llama 3.1 8B — scam classification, summaries
         └── Mixtral 8x7B — multilingual translation
  NO  → Google Gemini 2.0 Flash (fallback)
  NO  → OpenAI GPT-4o (secondary fallback)
  NO  → Deterministic template (offline fallback)
```

The **AMD Status Panel** in the dashboard top-bar shows which provider is active in real time. When Fireworks AI is configured it displays a green **AMD GPU** badge.

### Where AMD/Fireworks AI is used

| Module | Task | Fireworks Model |
|---|---|---|
| Orchestrator | Event narrative summary | Gemma 2 27B / 9B / Llama 8B (by CRS tier) |
| Citizen Shield | Fraud-prevention chat | Gemma 2 9B / 27B |
| Citizen Shield | Multilingual translation | Mixtral 8x7B |
| Scam Detector | Secondary LLM scoring | Llama 3.1 8B |

---

## ✨ Five Modules

### 1. 🏦 Counterfeit Vision — Note Checker
Upload a photo of any Indian Rupee note (₹10 – ₹2000).

- **MobileNetV3** ML classification with **Grad-CAM** explainability heatmap
- **Gemini 2.0 Flash** multimodal AI verification of security features
- Rule-based fallback (colour profiling, aspect ratio, sharpness) — works serverless
- Covers: watermark, security thread, latent image, micro-lettering, colour-shift

### 2. 📞 Scam Call Detector
Paste a suspicious call transcript or SMS.

- **Deterministic pattern matcher** — IMPERSONATION, URGENCY_THREAT, ISOLATION, ACTION_REQUEST tactics
- **Fireworks AI / Gemini secondary check** — weighted 70/30 blend with pattern score
- Spoofed caller ID and video-coercion metadata modifiers

### 3. 🕸️ Fraud Network Graph
Interactive graph of hidden relationships between suspicious entities.

- **NetworkX** community detection (greedy_modularity_communities)
- Mule anomaly scoring: fan-in degree, sub-threshold structuring, tight time window
- BFS case summary builder — `GET /api/graph/case/{entity_id}`
- RAG query: `POST /api/graph/query` — natural-language questions over the graph

### 4. 🗺️ Geospatial Crime Heatmap
Real-time Leaflet map of fraud hotspots across Indian cities.

- **DBSCAN** clustering of geo-tagged complaints
- **Poisson-rate risk forecast** with day-of-week + hour-of-day seasonality
- 7 hotspot clusters pre-loaded: Delhi, Mumbai, Bengaluru, Kolkata, Hyderabad, Lucknow, Ahmedabad

### 5. 🤖 Citizen Shield — Fraud Prevention Agent
Conversational AI assistant powered by Gemma on AMD.

- Multi-turn conversation with full history context
- Grounded in Module A (scam scores) + Module C (fraud graph) signals
- **6 languages**: English, Hindi, Tamil, Telugu, Bengali, Marathi
- Real-time risk badge: LOW / MEDIUM / HIGH

### 🔗 LangGraph Orchestrator
All five modules wired into a **LangGraph state machine**:

```
ingest → enrich_graph → enrich_geo → score → llm_enrich (AMD) → decide
                                                                    ├── escalate → emit_feed
                                                                    ├── warn     → emit_feed
                                                                    ├── info     → emit_feed
                                                                    └── ignore   → END
```

- `llm_enrich` node calls Fireworks AI to write a human-readable summary of every risk event
- Generates JSON + PDF incident reports for critical events
- Compound Risk Score (CRS) formula: `0.40×scam + 0.30×graph + 0.20×geo + 0.10×recency`

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM (primary)** | Fireworks AI — Gemma 2, Llama 3.1, Mixtral on AMD Instinct GPUs |
| **LLM (fallback)** | Google Gemini 2.0 Flash |
| **Orchestration** | LangGraph + LangChain |
| **Backend** | FastAPI · Pydantic v2 · Python 3.11 · Uvicorn |
| **Frontend** | React 19 · Vite · Tailwind CSS · Framer Motion · Leaflet |
| **ML / CV** | PyTorch MobileNetV3 · Grad-CAM · Pillow · OpenCV |
| **Graph Analysis** | NetworkX · Community Detection · DBSCAN |
| **Containerisation** | Docker (multi-stage) · Docker Compose |
| **Deployment** | Vercel (serverless) · AMD Developer Cloud (Docker) |

---

## 🚀 Quick Start

### Option A — Docker (recommended, AMD Developer Cloud ready)

```bash
# 1. Clone
git clone https://github.com/piyushmarkandey1-ui/SafeNet-AI.git
cd SafeNet-AI

# 2. Create .env at repo root
cp backend/.env.example .env
# Edit .env — add FIREWORKS_API_KEY for AMD inference
# (falls back to Gemini/template without it)

# 3. Build + run
docker compose up --build

# App is live at http://localhost:8000
# API docs at  http://localhost:8000/docs
```

### Option B — Local development

**Backend**
```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env       # fill in API keys
uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `FIREWORKS_API_KEY` | **Recommended** | Fireworks AI key — enables AMD GPU inference (Gemma, Llama, Mixtral) |
| `FIREWORKS_BASE_URL` | Optional | Defaults to `https://api.fireworks.ai/inference/v1` |
| `GEMINI_API_KEY` | Optional | Google Gemini fallback for note verification + chat |
| `OPENAI_API_KEY` | Optional | Secondary LLM fallback |

Get your Fireworks AI key: [fireworks.ai](https://fireworks.ai/)  
Get AMD Developer Cloud access: [AMD AI Developer Program](https://www.amd.com/en/developer/resources/ai-developer-program.html)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check / SPA root |
| `GET` | `/api/provider-status` | LLM provider + AMD inference status |
| `POST` | `/api/vision/check-note` | Counterfeit note detection (MobileNetV3 + Grad-CAM) |
| `POST` | `/api/scam/score-call` | Scam call transcript scoring |
| `GET` | `/api/graph/case/{id}` | Fraud network evidence for entity |
| `GET` | `/api/graph/clusters` | Fraud ring community detection |
| `GET` | `/api/geo/hotspots` | DBSCAN crime hotspot clusters |
| `GET` | `/api/geo/risk-forecast` | Poisson next-24h risk forecast |
| `POST` | `/api/shield/ask` | Citizen Shield chat (Gemma on AMD) |
| `GET` | `/api/shield/gemma-info` | Gemma model status (bonus prize proof) |
| `POST` | `/api/check-number` | Phone number fraud risk analysis |
| `GET` | `/api/orchestrator/dashboard-feed` | Live compound risk event feed |
| `POST` | `/api/orchestrator/simulate` | Trigger 3-step coordinated attack demo |

Interactive docs: `http://localhost:8000/docs`

---

## 🗺️ Project Structure

```
SafeNet-AI/
├── Dockerfile                        # Multi-stage Docker build
├── docker-compose.yml               # Full stack compose
├── api/index.py                     # Vercel serverless entry point
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI root + static serving
│   │   ├── fireworks_client.py      # AMD/Fireworks AI LLM router ★
│   │   ├── counterfeit_vision/      # Module 1 — MobileNetV3 + Grad-CAM
│   │   ├── scam_detector/           # Module 2 — Pattern matching + LLM
│   │   ├── fraud_graph/             # Module 3 — NetworkX + RAG
│   │   ├── geospatial/              # Module 4 — DBSCAN + Poisson
│   │   ├── citizen_shield/          # Module 5 — Gemma chat agent ★
│   │   ├── number_checker/          # Phone number risk lookup
│   │   └── orchestrator/            # LangGraph CRS pipeline ★
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/dashboard/
│       │   ├── AmdStatusPanel.jsx   # AMD GPU inference status widget ★
│       │   └── ...
│       ├── pages/
│       │   ├── LandingPage/
│       │   ├── NoteChecker/
│       │   └── NumberChecker/
│       ├── lib/api.js               # API client (auto base URL)
│       └── mocks/                   # Indian city offline fallback data ★
└── data/synthetic/                  # SYNTHETIC datasets (clearly labelled)
```
★ = modified for AMD Hackathon

---

## 🏗️ Architecture

```
User (Browser)
      │
      ▼
React 19 + Vite (frontend)
      │  /api/*
      ▼
FastAPI Backend (port 8000)
      │
      ├── /api/provider-status ──────────── fireworks_client.py
      │                                     (AMD status to dashboard)
      │
      ├── Orchestrator (LangGraph) ──────── node_llm_enrich
      │   ingest → enrich_graph             ↕ Fireworks AI
      │         → enrich_geo               (Gemma/Llama/Mixtral)
      │         → score                    on AMD Instinct GPUs
      │         → llm_enrich  ◄── AMD ───┘
      │         → decide
      │         → escalate/warn/info
      │         → emit_feed
      │
      ├── Citizen Shield ────────────────── Gemma 2 9B / 27B
      │   POST /shield/ask                  via Fireworks AI (AMD)
      │   GET  /shield/gemma-info
      │
      ├── Counterfeit Vision ─────────────  MobileNetV3 + Gemini
      ├── Scam Detector ──────────────────  Pattern + Llama 8B
      ├── Fraud Graph ────────────────────  NetworkX + DBSCAN
      ├── Geospatial ─────────────────────  DBSCAN + Poisson
      └── Number Checker ─────────────────  Graph + Blocklist
```

---

## 🧪 Demo Walkthrough

### 1. Simulate a Coordinated Attack
1. Open the dashboard → click **Simulate Scenario**
2. Watch the CRS climb: 35 → 65 → 87 across 3 correlated events
3. The AMD LLM node writes a human-readable summary for each event
4. Click the final CRITICAL event → Evidence Panel opens with full incident report

### 2. Test Citizen Shield (Gemma on AMD)
1. Click the chat bubble (bottom-right)
2. Type: *"Someone called saying they are from CBI and I have an arrest warrant"*
3. Gemma 2 9B (AMD) responds with threat assessment + specific next steps
4. Check: `GET /api/shield/gemma-info` to confirm Gemma model is active

### 3. Check a Currency Note
1. Navigate to **Note Checker**
2. Upload any Indian Rupee note photo
3. Get: denomination, real/fake verdict, confidence, Grad-CAM heatmap

### 4. Check a Suspicious Number
1. Navigate to **Number Checker**
2. Enter `+916511361582`
3. Get fraud graph hit + blocklist match + risk verdict with traceable reasons

---

## ⚠️ Synthetic Data Notice

All datasets (`data/synthetic/`) are artificially generated for demonstration.  
Every file is clearly labelled `SYNTHETIC` in its filename.  
Results are not based on real incidents, persons, or telecom records.

---

*SafeNet AI — Built for the AMD Developer Hackathon: ACT II | Track 3 — Unicorn Track*
