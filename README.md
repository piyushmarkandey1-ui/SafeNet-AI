# SafeNet AI 🛡️

**One Intelligence Layer. Five Threat Surfaces.**

> SafeNet AI is a unified digital public-safety intelligence platform built for the **ET Hackathon**.  
> It combines five AI-powered threat-detection modules behind a single LangGraph orchestration agent, enabling citizens and law enforcement to detect, visualize, and respond to fraud and financial crime in real time.

🌐 **Live Demo:** [safe-net-ai-sandy.vercel.app](https://safe-net-ai-sandy.vercel.app)

---

## ✨ Features

### 1. 🏦 Counterfeit Currency Note Checker
Upload a photo of any Indian Rupee note (₹10 – ₹2000). The AI analyses the image using:
- **Rule-based image analysis** — dominant color profiling, aspect-ratio validation, and sharpness detection tuned to each denomination's physical dimensions.
- **Gemini 2.0 Flash** — multimodal AI verification that examines watermarks, security threads, latent images, micro-lettering, and print quality.
- **Grad-CAM style heatmap overlay** — highlights the exact regions that triggered the verdict.

**Result:** Real / Fake verdict + confidence score + denomination detection + actionable recommendation.

---

### 2. 📞 Scam Call Detector
Paste a suspicious SMS, call transcript, or UPI payment description. The module:
- Matches against **known scam patterns** (vishing, KYC fraud, lottery scams, fake government impersonation).
- Scores risk level: `low / medium / high / critical`.
- Provides step-by-step advice on what to do.

---

### 3. 🕸️ Fraud Network Graph
Interactive graph visualization of hidden relationships between suspicious entities:
- Nodes: phone numbers, bank accounts, UPI IDs.
- Edges: call records, transactions, shared device fingerprints.
- **Community detection** to surface coordinated fraud rings.
- **Anomaly scoring** — fan-in mule patterns, sub-threshold smurfing, tight time-window bursts.

---

### 4. 🗺️ Geospatial Crime Heatmap
Real-time map overlay of fraud hotspots:
- Clusters incident reports by geographic proximity (H3 hexagonal grid).
- Color-coded by severity and incident density.
- Drill-down into individual complaint details.

---

### 5. 🤖 Citizen Fraud-Shield Chatbot
Conversational AI assistant in English and Hindi:
- Answers questions about common scams, RBI advisories, and cybercrime helplines.
- Detects intent and provides actionable, traceable guidance.
- Supports voice-style natural-language queries.

---

### 🔗 LangGraph Orchestrator
All five modules are wired together through a **LangGraph state machine**:
- Routes user intent to the correct module.
- Composes multi-step reasoning (e.g., "is this number in the fraud graph AND linked to a hotspot?").
- Drives the live dashboard feed with correlated risk events.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI · Pydantic v2 · Python 3.11+ · Uvicorn |
| **Frontend** | React 18 · Vite · Vanilla CSS |
| **AI / ML** | Google Gemini 2.0 Flash (multimodal) · Rule-based CV |
| **Orchestration** | LangGraph · LangChain |
| **Graph Analysis** | NetworkX · Community Detection |
| **Geospatial** | H3 · Folium / Leaflet.js |
| **Image Processing** | Pillow · NumPy |
| **Deployment** | Vercel (frontend + Python serverless) |
| **Config** | `.env`-based · python-dotenv |

---

## 📁 Project Structure

```
SafeNet-AI/
├── api/
│   └── index.py                    # Vercel serverless entry point (Mangum/ASGI)
├── backend/
│   └── app/
│       ├── main.py                 # FastAPI application root
│       ├── counterfeit_vision/     # Module 1 — Note Checker
│       │   ├── api.py              # FastAPI router
│       │   ├── indian_note_detector.py   # Rule-based + Gemini detector
│       │   └── inference.py        # PyTorch inference (optional)
│       ├── scam_detector/          # Module 2 — Scam Call Detector
│       ├── fraud_graph/            # Module 3 — Fraud Network Graph
│       ├── geospatial/             # Module 4 — Crime Heatmap
│       ├── citizen_shield/         # Module 5 — Fraud-Shield Chatbot
│       ├── number_checker/         # Phone number risk lookup
│       └── orchestrator/           # LangGraph orchestration agent
├── frontend/
│   ├── src/
│   │   ├── components/             # UI components (NoteChecker, Dashboard, etc.)
│   │   ├── lib/api.js              # API layer with auto-detect base URL
│   │   └── mocks/                  # Offline-mode fallback data
│   └── vite.config.js
├── data/
│   └── synthetic/                  # Clearly-labelled synthetic datasets
├── requirements.txt                # Production Python deps (Vercel)
└── vercel.json                     # Vercel build + routing config
```

---

## 🚀 Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey) (optional — falls back to rule-based analysis)

### Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

# Create .env file:
echo "GEMINI_API_KEY=your_key_here" > .env

uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

The frontend auto-detects whether to call `localhost:8000` (local) or the current Vercel origin (production) — no environment variable needed.

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Optional | Google Gemini API key for AI-powered note verification. Falls back to rule-based analysis if absent. |

Set in Vercel: **Project Settings → Environment Variables**

---

## 🏗️ Architecture

```
User
 │
 ▼
Frontend (React/Vite)  ──── /api/* ────►  Vercel Serverless (api/index.py)
                                                    │
                                          ┌─────────▼──────────┐
                                          │   FastAPI App        │
                                          │                      │
                              ┌───────────┤  LangGraph           │
                              │           │  Orchestrator        │
                              │           └──────────────────────┘
                              │
              ┌───────────────┼───────────────────────────────┐
              │               │               │               │
              ▼               ▼               ▼               ▼
    Note Checker        Scam Detector    Fraud Graph    Citizen Shield
   (Gemini + CV)       (NLP patterns)   (NetworkX)     (RAG chatbot)
```

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api` | Health check |
| `POST` | `/api/vision/check-note` | Counterfeit note detection |
| `POST` | `/api/scam/detect` | Scam text/call analysis |
| `GET` | `/api/graph/case/{id}` | Fraud network for entity |
| `GET` | `/api/geo/hotspots` | Active crime hotspots |
| `POST` | `/api/shield/ask` | Citizen Shield chatbot |
| `POST` | `/api/check-number` | Phone number risk check |
| `GET` | `/api/orchestrator/dashboard-feed` | Live risk event feed |

---

## 🏆 Built For

**ET Hackathon** — Economic Times AI Hackathon  
Theme: AI for Public Safety & Financial Security

---

*SafeNet AI — Making digital safety accessible to every citizen.*
