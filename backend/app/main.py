# SafeNet AI — FastAPI Application Entry Point

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file (no-op if file doesn't exist)
load_dotenv()

from app.scam_detector.api import router as scam_router, live_feed_events
from app.counterfeit_vision.api import router as vision_router, vision_feed_events
from app.fraud_graph.api import router as graph_router
from app.geospatial.api import router as geo_router
from app.citizen_shield.api import router as shield_router
from app.orchestrator.api import router as orchestrator_router
from app.number_checker.api import router as number_checker_router

app = FastAPI(
    title="SafeNet AI Backend",
    description="Unified digital public safety intelligence platform",
    version="0.1.0"
)

# Configure CORS for Vite frontend and Vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "https://safenet-ai.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All routers are mounted under /api prefix so that local development and
# Vercel serverless routing are identical.
app.include_router(scam_router, prefix="/api")
app.include_router(vision_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(geo_router, prefix="/api")
app.include_router(shield_router, prefix="/api")
app.include_router(orchestrator_router, prefix="/api")
app.include_router(number_checker_router, prefix="/api")


@app.get("/api/dashboard/feed", summary="Aggregated live risk feed (all modules)")
def get_dashboard_feed():
    """
    Orchestrator-level feed endpoint.

    Merges events from all active modules.
    Module feeds plug in here — the frontend URL never changes.

    Returns:
        List of risk-feed events sorted newest-first, capped at 50.
    """
    all_events: list = []
    all_events.extend(live_feed_events)       # scam_detector
    all_events.extend(vision_feed_events)     # counterfeit_vision
    # TODO: extend with fraud_graph, geospatial events

    all_events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return all_events[:50]


@app.get("/")
def read_root():
    return {"status": "ok", "message": "SafeNet AI backend is running."}
