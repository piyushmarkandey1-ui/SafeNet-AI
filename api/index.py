"""
SafeNet AI — Vercel Serverless Function Entry Point

This file adapts the FastAPI app for Vercel's serverless architecture.
Vercel auto-detects the `app` ASGI object and routes /api/* here via rewrites.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set environment for production
os.environ["VERCEL_ENV"] = "production"

# ── Try to import the full FastAPI app ────────────────────────────────────────
try:
    from app.main import app as fastapi_app
    app = fastapi_app

except Exception as e:
    import traceback
    error_tb = traceback.format_exc()

    from fastapi import FastAPI, File, UploadFile, HTTPException
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="SafeNet AI - Fallback API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    @app.get("/api")
    def fallback_root():
        return {
            "status": "ok",
            "message": "SafeNet AI backend is running.",
            "note": f"Orchestrator disabled: {str(e)}"
        }

    # ── Note Checker — always available, no langgraph needed ──────────────────
    @app.post("/vision/check-note")
    @app.post("/api/vision/check-note")
    async def fallback_check_note(file: UploadFile = File(...)):
        content_type = file.content_type or ""
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"Expected an image file, got: {content_type}")

        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")

        try:
            from app.counterfeit_vision.indian_note_detector import check_indian_note
            result = check_indian_note(image_bytes)
        except Exception as ex:
            raise HTTPException(status_code=500, detail=f"Inference error: {str(ex)}")

        from datetime import datetime
        from uuid import uuid4

        event_id = f"cv-{str(uuid4())[:8]}"
        timestamp = datetime.now().isoformat()

        return {
            "event_id": event_id,
            "is_fake": result["is_fake"],
            "confidence": result["confidence"],
            "denomination": result["denomination"],
            "denomination_raw": result["denomination_raw"],
            "auth_class": result["auth_class"],
            "gradcam_overlay": result.get("gradcam_overlay", ""),
            "recommendation": result.get("recommendation", ""),
            "severity": result.get("severity", ""),
            "timestamp": timestamp,
            "verification_method": result.get("verification_method", "rule-based"),
            "detected_issues": result.get("detected_issues", []),
            "gemini_verification": result.get("gemini_verification", ""),
        }

    @app.get("/orchestrator/dashboard-feed")
    @app.get("/api/orchestrator/dashboard-feed")
    async def fallback_dashboard_feed():
        return [
            {
                "id": "fallback-001",
                "type": "SCAM_CALL",
                "severity": "high",
                "timestamp": "2026-07-07T10:30:00Z",
                "title": "Demo: Suspicious Call Pattern",
                "description": "Fallback data - backend unavailable",
                "location": {"lat": 28.6139, "lng": 77.2090, "name": "Delhi, India"},
                "entities": ["+91-98001-DEMO"],
                "score": 75.0
            }
        ]

    @app.post("/orchestrator/simulate")
    @app.post("/api/orchestrator/simulate")
    async def fallback_simulate():
        return {"status": "fallback", "message": "Simulation unavailable - using fallback mode"}

    @app.get("/geo/hotspots")
    @app.get("/api/geo/hotspots")
    async def fallback_hotspots():
        return [
            {
                "id": "hotspot-fallback-001",
                "centroid": [28.7175, 77.1201],
                "radius": 2.5,
                "complaint_count": 25,
                "risk_score": 75.0,
                "severity": "high",
                "location_name": "North Delhi (Fallback Data)"
            }
        ]

# ── Vercel ASGI entrypoint: expose `app` directly (no Mangum needed) ─────────
# Vercel's Python runtime natively supports ASGI via the `app` variable.
# The Mangum wrapper below is kept as a fallback for Lambda-style invocation.
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    handler = None