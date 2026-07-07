"""
SafeNet AI — Orchestrator: FastAPI Router

Exposes:
  POST /orchestrator/event           — ingest any module event for compound scoring
  GET  /orchestrator/dashboard-feed  — the REAL source of truth for the Live Risk Feed
  POST /orchestrator/simulate        — triggers the full demo scenario (wired to the
                                       dashboard's "Simulate Scenario" button)

Module contract (safenet.md §3):
  All handlers are thin wrappers around graph.process_event().
"""

import asyncio
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, ConfigDict
from typing import Any, Optional

from app.orchestrator.graph import process_event, orchestrator_feed

router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"])


class RawEventRequest(BaseModel):
    """Body for POST /orchestrator/event — accepts any event shape."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    type: str = "SCAM_CALL"
    entities: list[str] = []
    location: Optional[dict] = None
    scam_score: float = 0.0
    timestamp: Optional[str] = None
    transcript: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    is_spoofed: bool = False
    duration_sec: int = 0
    video_requested: bool = False


@router.post(
    "/event",
    summary="Ingest a raw module event for compound risk scoring",
)
async def ingest_event(body: RawEventRequest):
    """
    Runs the incoming event through the full LangGraph orchestration pipeline.

    Returns the final state including CRS, severity, action taken, and
    feed_event (the shape the dashboard Live Risk Feed expects).
    """
    raw = body.model_dump(exclude_none=False)
    result = await asyncio.to_thread(process_event, raw)

    # Return a concise summary (not the full state which includes large nested dicts)
    return {
        "event_id": result["feed_event"].get("id", ""),
        "crs": result["crs"],
        "severity": result["severity"],
        "action": result["action"],
        "crs_breakdown": result["crs_breakdown"],
        "incident_id": result["incident_report"].get("incident_id", ""),
        "report_path_json": result["report_path_json"],
        "report_path_pdf": result["report_path_pdf"],
        "citizen_alert_sent": result["citizen_alert_sent"],
        "feed_event": result["feed_event"],
    }


@router.get(
    "/dashboard-feed",
    summary="Live Risk Feed — orchestrated compound events (real source of truth)",
)
async def get_dashboard_feed():
    """
    Returns the orchestrator's in-memory event feed.

    This is the REAL source of truth for the frontend's Live Risk Feed,
    replacing the per-module feeds that were aggregated in /dashboard/feed.
    Shape is identical — the frontend component needs no changes.
    """
    return orchestrator_feed


@router.post(
    "/simulate",
    summary="Trigger the full demo scenario (wires the Simulate Scenario button)",
)
async def trigger_simulation():
    """
    Kicks off the demo scenario synchronously so it works reliably on Vercel 
    Serverless Functions without background tasks being killed prematurely.
    """
    from app.orchestrator.demo_scenario import run_scenario
    from app.orchestrator.graph import orchestrator_feed
    
    # Run the scenario completely before returning so Vercel doesn't kill it.
    # Pass a tiny delay so it completes fast (well under the 10s Vercel limit).
    await asyncio.to_thread(run_scenario, 0.1)
    
    return {
        "status": "simulation_completed",
        "message": "Demo scenario completed.",
        "events": list(orchestrator_feed)
    }
