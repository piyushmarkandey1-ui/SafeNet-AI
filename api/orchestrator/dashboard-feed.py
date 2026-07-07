"""
Vercel Serverless Function: GET /api/orchestrator/dashboard-feed
"""

import json
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

app = FastAPI()

@app.get("/api/orchestrator/dashboard-feed")
async def get_dashboard_feed():
    """
    Returns the orchestrator's live feed events.
    Serverless-compatible version with fallback data.
    """
    try:
        # Try to import and get real feed
        from app.orchestrator.graph import orchestrator_feed
        return orchestrator_feed
    except Exception as e:
        # Fallback to mock data for demo
        return [
            {
                "id": "demo-001",
                "type": "SCAM_CALL",
                "severity": "high",
                "timestamp": "2026-07-07T10:30:00Z",
                "title": "Suspicious Call Pattern Detected",
                "description": "CBI impersonation attempt blocked",
                "location": {"lat": 28.6139, "lng": 77.2090, "name": "Delhi, India"},
                "entities": ["+91-98001-DEMO"],
                "score": 78.5,
                "crs": 78.5,
                "action": "warn"
            }
        ]

# Vercel handler
def handler(request: Request):
    return app(request)