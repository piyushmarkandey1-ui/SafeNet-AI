"""
Vercel Serverless Function: POST /api/orchestrator/simulate
"""

import json
import sys
from pathlib import Path
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

app = FastAPI()

@app.post("/api/orchestrator/simulate")
async def trigger_simulation():
    """
    Triggers demo scenario simulation.
    Serverless-compatible version.
    """
    try:
        # Try to run real scenario
        from app.orchestrator.demo_scenario import run_scenario
        
        # Run synchronously for serverless (no background tasks)
        results = run_scenario(delay_between_steps=0.5)
        
        return {
            "status": "simulation_completed",
            "message": "Demo scenario executed successfully",
            "events_generated": len(results),
            "final_crs": results[-1]["crs"] if results else 0
        }
        
    except Exception as e:
        # Fallback response
        return {
            "status": "simulation_started",
            "message": f"Mock simulation (serverless fallback): {str(e)}",
            "note": "Some modules may not be available in serverless environment"
        }

# Vercel handler  
def handler(request: Request):
    return app(request)