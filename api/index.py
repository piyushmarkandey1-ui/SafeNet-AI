"""
SafeNet AI — Vercel Serverless Function Entry Point

This file adapts the FastAPI app for Vercel's serverless architecture.
Vercel will automatically handle routing to this file for /api/* requests.
"""

import os
import sys
from pathlib import Path
from mangum import Mangum

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set environment for production
os.environ["VERCEL_ENV"] = "production"

# Import and configure the FastAPI app
try:
    from app.main import app as fastapi_app
    
    # The app is already configured in main.py with all routers
    app = fastapi_app
    
except ImportError as e:
    # Fallback minimal app if imports fail
    from fastapi import FastAPI
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
            "status": "error",
            "message": f"Backend import failed: {str(e)}",
            "note": "Some dependencies may be missing in serverless environment. Using fallback API.",
            "available_endpoints": [
                "GET /api/orchestrator/dashboard-feed (fallback data)",
                "POST /api/orchestrator/simulate (fallback response)",
                "GET /api/geo/hotspots (fallback data)"
            ]
        }
    
    # Fallback endpoints with mock data
    @app.get("/orchestrator/dashboard-feed")
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
    async def fallback_simulate():
        return {
            "status": "fallback",
            "message": "Simulation unavailable - using fallback mode",
            "note": "Backend dependencies not loaded in serverless environment"
        }
    
    @app.get("/geo/hotspots")
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

# Wrap the FastAPI app with Mangum for AWS Lambda/Vercel compatibility
handler = Mangum(app, lifespan="off")