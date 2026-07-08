# SafeNet AI — Slide Deck Outline
## AMD Developer Hackathon: ACT II | Track 3 — Unicorn Track

> 10 slides · Pitch-deck format · ~5 minutes spoken

---

### SLIDE 1 — Title
- **SafeNet AI**
- *One Intelligence Layer. Five Threat Surfaces.*
- AMD Developer Hackathon: ACT II | Track 3 — Unicorn Track
- Team name · GitHub link · Live demo URL

---

### SLIDE 2 — The Problem
**Headline:** India loses ₹11,000+ crore to digital fraud every year.

- 1.4 billion citizens, millions targeted daily
- Scam calls, fake currency, UPI fraud, coordinated crime rings
- Law enforcement acts reactively — no unified intelligence layer
- Existing tools are siloed: one app for calls, another for notes, nothing connects them

**Visual:** India map with crime hotspot heatmap

---

### SLIDE 3 — The Solution
**Headline:** Five AI modules. One Compound Risk Score. One dashboard.

Show the 5-module architecture diagram:
```
Scam Detector  ──┐
Counterfeit CV ──┤
Fraud Graph    ──┼── LangGraph Orchestrator ── Compound Risk Score ── Dashboard
Geospatial     ──┤       (AMD / Fireworks AI)
Citizen Shield ──┘
```

- Single platform for law enforcement AND citizens
- Signals correlated automatically — no manual cross-referencing

---

### SLIDE 4 — AMD & Fireworks AI Integration
**Headline:** Every LLM inference call runs on AMD Instinct GPUs.

| Task | Model | Hardware |
|------|-------|----------|
| Critical event summaries | Gemma 2 27B | AMD via Fireworks AI |
| Citizen fraud chat | Gemma 2 9B | AMD via Fireworks AI |
| Scam classification | Llama 3.1 8B | AMD via Fireworks AI |
| Translation (6 languages) | Mixtral 8x7B | AMD via Fireworks AI |

- Automatic model routing: cheapest sufficient model per task
- Live AMD Status Panel in dashboard confirms active inference

---

### SLIDE 5 — LangGraph Orchestrator
**Headline:** Signals don't mean much alone. Correlation is everything.

Show the state machine flow:
```
ingest → enrich_graph → enrich_geo → score → llm_enrich(AMD) → decide → emit/escalate
```

- Compound Risk Score: `0.40×scam + 0.30×graph + 0.20×geo + 0.10×recency`
- `llm_enrich` node: Fireworks AI writes a natural-language narrative per event
- Auto-generates PDF incident reports for critical events
- Full audit log in JSONL format

**Show:** CRS climbing 35 → 65 → 87 across correlated steps (screenshot)

---

### SLIDE 6 — Module Deep Dives (2×2 grid)

**Counterfeit Vision**
- MobileNetV3 + Grad-CAM explainability
- Covers all 7 Indian Rupee denominations (₹10–₹2000)
- Works without PyTorch (rule-based fallback for serverless)

**Scam Detector**
- 4 tactic categories: IMPERSONATION, URGENCY, ISOLATION, ACTION_REQUEST
- Llama 8B secondary scoring via Fireworks AI

**Fraud Graph**
- NetworkX community detection + mule anomaly scoring
- BFS case builder + RAG natural-language query

**Geospatial**
- DBSCAN clustering of complaint GPS points
- Poisson next-24h risk forecast with DOW seasonality

---

### SLIDE 7 — Citizen Shield (Gemma on AMD)
**Headline:** Best AMD-Hosted Gemma Project — $2,000 bonus prize target

- Conversational fraud-prevention agent for Indian citizens
- **Gemma 2 9B** (standard) + **Gemma 2 27B** (complex) via Fireworks AI
- Grounded in live Module A + C signals — not generic advice
- **6 languages**: English, Hindi, Tamil, Telugu, Bengali, Marathi
- Multilingual translation via Mixtral on AMD hardware
- `GET /api/shield/gemma-info` — verifiable proof of Gemma on AMD

**Show:** Chat screenshot with Gemma response to CBI impersonation scenario

---

### SLIDE 8 — Completeness & Engineering Quality
**Headline:** This ships. Right now.

- ✅ Fully containerised (Docker + docker-compose — runs in one command)
- ✅ AMD Developer Cloud ready (ROCm-compatible Python stack)
- ✅ Vercel serverless deployment (live demo running today)
- ✅ All synthetic data clearly labelled (SYNTHETIC in every filename)
- ✅ Pydantic v2 throughout, typed LangGraph state, Google-style docstrings
- ✅ Graceful fallbacks at every level — never crashes on missing dependency

---

### SLIDE 9 — Market Opportunity
**Headline:** ₹11,000 crore problem. Zero unified solutions.

- **Primary buyers:** State cybercrime cells, RBI/FIU-IND, NCRB
- **Secondary buyers:** Banks (fraud operations centres), telecom operators
- **Citizen tier:** Free public app — 1.4B addressable users
- **Comparable:** Sardine.ai ($52M Series B), TrustDecision (Asia-focused) — neither covers India end-to-end
- Revenue model: B2G SaaS (per-agency licence) + B2B API (per-call pricing)

---

### SLIDE 10 — Call to Action
**Headline:** SafeNet AI — Making digital safety accessible to every citizen.

- 🏆 Track 3 — Unicorn Track submission
- 🎯 Best AMD-Hosted Gemma Project (bonus prize)
- 🚀 `docker compose up --build` → live in 3 minutes

Links:
- Live demo: `safe-net-ai-sandy.vercel.app`
- GitHub: `github.com/piyushmarkandey1-ui/SafeNet-AI`
- AMD proof: `[demo-url]/api/provider-status`
- Gemma proof: `[demo-url]/api/shield/gemma-info`

---

## DESIGN NOTES

- Dark theme throughout — match the app's `--bg-base: #0A0E14`
- Accent colours: `#2EC4B6` (trust/AMD green) and `#E05A33` (risk/alert red)
- Use the actual dashboard screenshot for slide 5 and 7
- Keep text minimal — let the demo video carry the detail
- AMD logo + Fireworks AI logo on slide 4
