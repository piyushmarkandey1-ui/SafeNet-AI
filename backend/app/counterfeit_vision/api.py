"""
SafeNet AI — Counterfeit Vision: FastAPI Router

Exposes:
  POST /vision/check-note  — Upload a currency image, get authenticity verdict + Grad-CAM

Follows SafeNet module contract (safenet.md rule 3):
  - REST endpoint is a thin wrapper around inference.check_note().
  - The plain Python function is the source of truth.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import uuid4

from app.counterfeit_vision.inference import check_note

router = APIRouter(prefix="/vision", tags=["Counterfeit Vision"])

# In-memory event store — same pattern as scam_detector
vision_feed_events: list[dict] = []

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class NoteCheckResponse(BaseModel):
    """Response schema for POST /vision/check-note."""

    model_config = ConfigDict(populate_by_name=True)

    event_id: str
    is_fake: bool
    confidence: float
    denomination: str
    denomination_raw: str
    auth_class: str
    gradcam_overlay: str   # base64-encoded PNG
    recommendation: str
    severity: str
    timestamp: str


def _build_recommendation(is_fake: bool, confidence: float) -> tuple[str, str]:
    """
    Derives a human-readable recommendation and severity level.

    Args:
        is_fake:     Model prediction.
        confidence:  Softmax confidence of the predicted class.

    Returns:
        (recommendation, severity)
    """
    if is_fake:
        if confidence >= 0.90:
            return ("ALERT: High-confidence counterfeit detected. Seize note and file report.",
                    "critical")
        elif confidence >= 0.70:
            return ("WARNING: Likely counterfeit. Refer to bank verification counter.",
                    "high")
        else:
            return ("SUSPICIOUS: Low-confidence counterfeit flag. Manual inspection advised.",
                    "medium")
    else:
        if confidence >= 0.85:
            return ("Note appears genuine.", "safe")
        else:
            return ("Likely genuine, but low model confidence. Manual check recommended.", "low")


@router.post(
    "/check-note",
    response_model=NoteCheckResponse,
    summary="Classify a currency note image as real or fake",
)
async def check_note_endpoint(file: UploadFile = File(...)) -> NoteCheckResponse:
    """
    Accepts a currency note image (JPEG/PNG/WEBP) and returns:
      - Authenticity verdict (real/fake)
      - Denomination prediction
      - Confidence score
      - Grad-CAM heatmap overlay (base64 PNG)

    Args:
        file: Uploaded image file.

    Returns:
        NoteCheckResponse with full classification result.

    Raises:
        HTTPException 400: If the file is not a valid image or exceeds size limit.
        HTTPException 422: If the image cannot be decoded.
        HTTPException 500: Internal model error.
    """
    # ── Validate upload ───────────────────────────────────────────────────────
    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Expected an image file, got: {content_type}",
        )

    image_bytes = await file.read()

    if len(image_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_BYTES // (1024*1024)} MB.",
        )

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    # ── Run inference ─────────────────────────────────────────────────────────
    try:
        result = check_note(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

    # ── Build response ────────────────────────────────────────────────────────
    recommendation, severity = _build_recommendation(
        result["is_fake"], result["confidence"]
    )
    event_id = f"cv-{str(uuid4())[:8]}"
    timestamp = datetime.now().isoformat()

    # ── Append to vision feed (for dashboard integration) ─────────────────────
    score = result["confidence"] * 100 if result["is_fake"] else (1 - result["confidence"]) * 100
    feed_item = {
        "id": event_id,
        "type": "COUNTERFEIT",
        "severity": severity,
        "timestamp": timestamp,
        "title": f"{'⚠ Counterfeit' if result['is_fake'] else '✓ Genuine'} Note — {result['denomination']}",
        "description": recommendation,
        "location": {"lat": 28.6139, "lng": 77.2090, "name": "Note Check Station"},
        "entities": [result["denomination"]],
        "score": round(score, 1),
    }

    if result["is_fake"] or result["confidence"] < 0.90:
        vision_feed_events.insert(0, feed_item)
        if len(vision_feed_events) > 50:
            vision_feed_events.pop()

    return NoteCheckResponse(
        event_id=event_id,
        is_fake=result["is_fake"],
        confidence=result["confidence"],
        denomination=result["denomination"],
        denomination_raw=result["denomination_raw"],
        auth_class=result["auth_class"],
        gradcam_overlay=result["gradcam_overlay"],
        recommendation=recommendation,
        severity=severity,
        timestamp=timestamp,
    )


@router.get("/feed", summary="Recent counterfeit detection events")
async def get_vision_feed() -> list[dict]:
    """
    Returns the in-memory list of recent counterfeit detection events.
    Same shape as the scam detector feed, consumable by the dashboard.
    """
    return vision_feed_events
