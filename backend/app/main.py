# SafeNet AI — FastAPI Application Entry Point

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# Load environment variables from .env file (no-op if file doesn't exist)
load_dotenv()

from app.scam_detector.api import router as scam_router, live_feed_events
from app.counterfeit_vision.api import router as vision_router, vision_feed_events
from app.fraud_graph.api import router as graph_router
from app.geospatial.api import router as geo_router
from app.citizen_shield.api import router as shield_router
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
try:
    from app.orchestrator.api import router as orchestrator_router
    app.include_router(orchestrator_router, prefix="/api")
except ImportError as e:
    print(f"Warning: Orchestrator module disabled due to missing dependencies ({e})")

app.include_router(number_checker_router, prefix="/api")


# ── Provider status endpoint (used by AMD status panel) ───────────────────────

@app.get("/api/provider-status", summary="LLM provider and AMD inference status")
def get_provider_status():
    """
    Returns which LLM providers are configured and whether AMD inference is active.
    Used by the frontend AMD Status Panel on the dashboard.
    """
    from app.fireworks_client import get_provider_status
    return get_provider_status()


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


@app.get("/health", summary="Health check")
def health_check():
    """Used by Docker HEALTHCHECK and load balancers."""
    return {"status": "ok", "message": "SafeNet AI backend is running."}


@app.get("/")
def read_root():
    """Root — serves the React SPA when running in Docker, or health info otherwise."""
    frontend_dist = Path(os.getenv("FRONTEND_DIST_PATH", ""))
    index_html = frontend_dist / "index.html"
    if frontend_dist and index_html.exists():
        return FileResponse(str(index_html))
    return {"status": "ok", "message": "SafeNet AI backend is running."}


# ── Serve built frontend static assets (Docker / production mode) ─────────────
_frontend_dist = Path(os.getenv("FRONTEND_DIST_PATH", ""))
if _frontend_dist.exists():
    # Serve /assets, /icons, etc. from the Vite build output
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")
    app.mount("/public", StaticFiles(directory=str(_frontend_dist)), name="public")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        """Catch-all: return index.html for any non-API path (SPA routing)."""
        # Don't intercept /api routes
        if full_path.startswith("api"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404)
        index_html = _frontend_dist / "index.html"
        if index_html.exists():
            return FileResponse(str(index_html))
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
