"""
Vercel Serverless Function: POST /api/scam/classify
"""

import json
import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

app = FastAPI()

@app.post("/api/scam/classify")
async def classify_scam_call(
    transcript: str = Form(...),
    is_spoofed: bool = Form(False),
    duration_sec: int = Form(0),
    video_requested: bool = Form(False)
):
    """
    Classifies scam call transcript.
    Serverless-compatible version.
    """
    try:
        # Try pattern-based classification
        from app.scam_detector.classifier import score_call
        
        call_metadata = {
            "is_spoofed": is_spoofed,
            "duration_sec": duration_sec,
            "video_requested": video_requested
        }
        
        result = score_call(transcript, call_metadata)
        
        # Add event structure
        event_data = {
            "id": f"scam-{hash(transcript) % 100000:05d}",
            "type": "SCAM_CALL",
            "timestamp": "2026-07-07T10:30:00Z",
            "title": "Scam Call Analysis Complete",
            "description": result["recommendation"],
            "severity": result["severity"],
            "score": result["risk_score"],
            "patterns": result["triggered_patterns"],
            "transcript": transcript[:200] + "..." if len(transcript) > 200 else transcript
        }
        
        return {
            **result,
            "event": event_data
        }
        
    except Exception as e:
        # Fallback basic pattern matching
        score = 50 if any(word in transcript.lower() for word in 
                         ["police", "arrest", "warrant", "transfer", "otp"]) else 10
        
        return {
            "risk_score": score,
            "severity": "high" if score > 70 else "medium" if score > 30 else "low",
            "recommendation": f"Pattern-based analysis: {score}/100 risk score",
            "triggered_patterns": ["BASIC_PATTERN_MATCH"],
            "error": str(e)
        }

# Vercel handler
def handler(request: Request):
    return app(request)