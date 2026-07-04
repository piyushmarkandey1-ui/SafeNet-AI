# SafeNet AI

**Unified Digital Public Safety Intelligence Platform**

> Built for the ET Hackathon — a single platform that brings together five AI-powered
> modules behind one orchestration agent to help citizens and law enforcement detect,
> visualize, and respond to fraud and financial crime.

---

## Modules

| # | Module | Description |
|---|--------|-------------|
| 1 | **Scam Call Detector** | Real-time analysis of phone call transcripts to flag social-engineering and vishing patterns. |
| 2 | **Counterfeit Currency Vision** | On-device image classification (PyTorch / TFLite) to identify counterfeit banknotes. |
| 3 | **Fraud Network Graph** | Interactive NetworkX-powered graph revealing hidden relationships between suspicious entities. |
| 4 | **Geospatial Crime Heatmap** | Map-based visualization of fraud hotspots using reported incident data. |
| 5 | **Citizen Fraud-Shield Chatbot** | RAG-powered conversational assistant (ChromaDB + LangChain) that answers fraud-prevention questions. |
| 🔗 | **Orchestrator** | LangGraph agent that routes user intent to the right module and composes multi-step answers. |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI · Pydantic v2 · Python 3.11+ |
| Frontend | React · Vite |
| AI / ML | PyTorch · TFLite · LangChain · LangGraph |
| Vector DB | ChromaDB |
| Graph | NetworkX |
| Infra | Docker (planned) · `.env`-based config |

## Repo Structure

```
├── backend/
│   └── app/
│       ├── main.py                 # FastAPI entry point
│       ├── scam_detector/          # Module 1
│       ├── counterfeit_vision/     # Module 2
│       ├── fraud_graph/            # Module 3
│       ├── geospatial/             # Module 4
│       ├── citizen_shield/         # Module 5
│       └── orchestrator/           # LangGraph orchestration agent
├── frontend/                       # React + Vite SPA
├── data/
│   └── synthetic/                  # Mock datasets (clearly labeled SYNTHETIC)
├── docs/                           # Architecture diagrams & deck assets
├── .agents/rules/safenet.md        # Workspace AI-agent rules
└── .gitignore
```

## Quickstart

```bash
# 1. Clone & enter
git clone <repo-url> && cd safenet-ai

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn app.main:app --reload

# 3. Frontend
cd ../frontend
npm install && npm run dev
```

## Rules & Conventions

See [`.agents/rules/safenet.md`](.agents/rules/safenet.md) for the full set of workspace
rules that all contributors (human and AI) must follow.

---

*SafeNet AI — Making digital safety accessible to every citizen.*
