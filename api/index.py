"""
SafeNet AI — Vercel Serverless Entry Point

Vercel's Python runtime requires `app` to be defined at the ABSOLUTE module
top level (not inside try/except). Routes are added gracefully below.
"""

import os
import sys
from pathlib import Path

# ── Python path & env setup ───────────────────────────────────────────────────
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
os.environ.setdefault("VERCEL_ENV", "production")

# ── TOP-LEVEL app definition (required by Vercel's Python runtime) ────────────
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SafeNet AI",
    description="Unified digital public safety intelligence platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api")
@app.get("/")
def health():
    return {"status": "ok", "message": "SafeNet AI backend is running."}


# ── Provider Status (used by AMD status panel) ────────────────────────────────
@app.get("/api/provider-status", summary="LLM provider and AMD inference status")
def get_provider_status_endpoint():
    """Returns LLM providers and AMD ROCm status. Used by dashboard status panel."""
    try:
        from app.fireworks_client import get_provider_status
        return get_provider_status()
    except Exception as e:
        return {
            "active_provider": "none",
            "active_model": "template-fallback",
            "amd_inference": False,
            "error": str(e)
        }



# ── LLM Debug Endpoint ────────────────────────────────────────────────────────
@app.get("/api/debug-llm")
def debug_llm():
    """Temporary diagnostic endpoint to debug Fireworks API failures in production."""
    import os
    from openai import OpenAI
    
    fw_key = os.getenv("FIREWORKS_API_KEY", "")
    masked_key = f"{fw_key[:6]}...{fw_key[-4:]}" if len(fw_key) > 10 else "not set or too short"
    
    diagnostic = {
        "env_keys_present": {
            "FIREWORKS_API_KEY": bool(fw_key),
            "GEMINI_API_KEY": bool(os.getenv("GEMINI_API_KEY")),
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
            "LLM_API_KEY": bool(os.getenv("LLM_API_KEY")),
        },
        "masked_fireworks_key": masked_key,
        "test_call_result": None,
        "test_call_error": None
    }
    
    if not fw_key:
        diagnostic["test_call_error"] = "FIREWORKS_API_KEY is missing from environment variables."
        return diagnostic
        
    try:
        client = OpenAI(
            api_key=fw_key,
            base_url="https://api.fireworks.ai/inference/v1",
        )
        response = client.chat.completions.create(
            model="accounts/fireworks/models/glm-5p1",
            messages=[{"role": "user", "content": "Say 'Active'"}],
            temperature=0.1,
            max_tokens=10
        )
        diagnostic["test_call_result"] = response.choices[0].message.content.strip()
    except Exception as e:
        diagnostic["test_call_error"] = f"{type(e).__name__}: {str(e)}"
        
    return diagnostic



# ── Counterfeit Note Checker ──────────────────────────────────────────────────
# Attempt to load the full router; if not possible, add a minimal inline route.
try:
    from app.counterfeit_vision.api import router as vision_router
    app.include_router(vision_router, prefix="/api")
except Exception as _vision_err:
    @app.post("/api/vision/check-note")
    async def check_note_inline(file: UploadFile = File(...)):
        if not (file.content_type or "").startswith("image/"):
            raise HTTPException(400, detail="Expected an image file.")
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(400, detail="Empty file uploaded.")
        try:
            from app.counterfeit_vision.indian_note_detector import check_indian_note
            result = check_indian_note(image_bytes)
        except Exception as ex:
            raise HTTPException(500, detail=f"Inference error: {ex}")
        from datetime import datetime
        from uuid import uuid4
        return {
            "event_id": f"cv-{str(uuid4())[:8]}",
            "is_fake": result["is_fake"],
            "confidence": result["confidence"],
            "denomination": result["denomination"],
            "denomination_raw": result["denomination_raw"],
            "auth_class": result["auth_class"],
            "gradcam_overlay": result.get("gradcam_overlay", ""),
            "recommendation": result.get("recommendation", ""),
            "severity": result.get("severity", ""),
            "timestamp": datetime.now().isoformat(),
            "verification_method": result.get("verification_method", "rule-based"),
            "detected_issues": result.get("detected_issues", []),
            "gemini_verification": result.get("gemini_verification", ""),
        }


# ── Scam Detector ─────────────────────────────────────────────────────────────
try:
    from app.scam_detector.api import router as scam_router
    app.include_router(scam_router, prefix="/api")
except Exception:
    pass


# ── Fraud Graph ───────────────────────────────────────────────────────────────
try:
    from app.fraud_graph.api import router as graph_router
    app.include_router(graph_router, prefix="/api")
except Exception:
    pass


# ── Geospatial ────────────────────────────────────────────────────────────────
try:
    from app.geospatial.api import router as geo_router
    app.include_router(geo_router, prefix="/api")
except Exception:
    @app.get("/api/geo/hotspots")
    async def geo_fallback():
        return []


# ── Citizen Shield ────────────────────────────────────────────────────────────
try:
    from app.citizen_shield.api import router as shield_router
    app.include_router(shield_router, prefix="/api")
except Exception:
    pass


# ── Number Checker ────────────────────────────────────────────────────────────
try:
    from app.number_checker.api import router as number_checker_router
    app.include_router(number_checker_router, prefix="/api")
except Exception:
    pass


# ── Orchestrator (requires langgraph — optional) ──────────────────────────────
try:
    from app.orchestrator.api import router as orchestrator_router
    app.include_router(orchestrator_router, prefix="/api")
except Exception:
    @app.get("/api/orchestrator/dashboard-feed")
    async def dashboard_fallback():
        return []

    @app.post("/api/orchestrator/simulate")
    async def simulate_fallback():
        return {"status": "fallback", "message": "Orchestrator unavailable."}


# ── Dashboard aggregate feed ──────────────────────────────────────────────────
try:
    from app.main import get_dashboard_feed
    app.get("/api/dashboard/feed")(get_dashboard_feed)
except Exception:
    pass