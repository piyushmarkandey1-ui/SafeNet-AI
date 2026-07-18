from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import traceback

from .classifier import score_call

router = APIRouter(prefix="/scam", tags=["Scam Detector"])

# In-memory store for the feed demo (will be replaced by orchestrator later)
live_feed_events = []

class CallEvent(BaseModel):
    caller_number: str
    callee_number: str
    transcript_window: str
    is_spoofed: bool = False
    duration_sec: int = 0
    video_requested: bool = False
    location: Optional[dict] = {"lat": 28.6139, "lng": 77.2090, "name": "Delhi"}

@router.post("/score-call")
async def process_call(event: CallEvent):
    # Score the call
    metadata = {
        "is_spoofed": event.is_spoofed,
        "duration_sec": event.duration_sec,
        "video_requested": event.video_requested
    }
    
    try:
        result = score_call(event.transcript_window, metadata)
    except Exception as e:
        print(f"Error scoring call: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to score call")
    
    # Create feed item if it's suspicious enough
    if result["risk_score"] > 20:
        feed_item = {
            "id": f"evt-{str(uuid4())[:8]}",
            "type": "SCAM_CALL",
            "severity": result["severity"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "title": "Suspicious Call Detected",
            "description": f"Match on: {', '.join(result['triggered_patterns'])}",
            "location": event.location,
            "entities": [event.caller_number, event.callee_number],
            "score": float(result["risk_score"])
        }
        # Prepend to feed
        live_feed_events.insert(0, feed_item)
        
        # Keep feed short
        if len(live_feed_events) > 50:
            live_feed_events.pop()
            
    return result

@router.get("/feed")
async def get_feed():
    """
    Endpoint mimicking the exact structure the React UI expects.
    """
    return live_feed_events
