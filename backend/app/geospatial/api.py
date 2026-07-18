"""
SafeNet AI — Geospatial Module: FastAPI Router

Exposes:
  GET /geo/hotspots        — DBSCAN-clustered hotspot centroids (Leaflet schema)
  GET /geo/risk-forecast   — Next-24h Poisson risk estimate per zone
  GET /geo/raw-complaints  — Individual complaint points (debug / admin)

Module contract (safenet.md §3):
  Route handlers are thin wrappers around hotspots.py functions.
  The plain Python functions are the source of truth.
"""

from fastapi import APIRouter, Query
import logging

from app.geospatial.hotspots import (
    load_raw_complaints,
    detect_hotspots,
    compute_risk_forecast,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/geo", tags=["Geospatial"])


@router.get(
    "/hotspots",
    summary="Detected crime hotspot clusters (DBSCAN)",
)
async def get_hotspots(
    eps_km: float = Query(
        default=1.5,
        ge=0.1,
        le=20.0,
        description="DBSCAN neighbourhood radius in km (default 1.5 km).",
    ),
    min_samples: int = Query(
        default=5,
        ge=2,
        le=100,
        description="Minimum complaint points to form a cluster (default 5).",
    ),
):
    """
    Returns DBSCAN-clustered hotspot centroids in the Leaflet CircleMarker schema:
      id, lat, lng, intensity (0-1), radius (metres), type (CRITICAL/HIGH/MEDIUM/LOW).

    Additional fields (point_count, complaint_types, top_complaint_type) are
    included as bonus metadata — the map component ignores unknown fields so
    no component changes are needed.

    Args:
        eps_km:      Neighbourhood radius for DBSCAN.
        min_samples: Density threshold for cluster formation.

    Returns:
        List of hotspot dicts, sorted by point_count descending.
    """
    try:
        complaints = load_raw_complaints()
        return detect_hotspots(complaints, eps_km=eps_km, min_samples=min_samples)
    except Exception as e:
        logger.error(f"[geo/hotspots] DBSCAN computation failed: {e}", exc_info=True)
        return []  # Return empty list instead of propagating 500


@router.get(
    "/risk-forecast",
    summary="Next-24h risk forecast per hotspot zone",
)
async def get_risk_forecast(
    eps_km: float = Query(default=1.5, ge=0.1, le=20.0),
    min_samples: int = Query(default=5, ge=2, le=100),
):
    """
    Returns the next-24h expected complaint count per zone using a
    Poisson-rate model with day-of-week seasonality.

    The model_note field on each result explains the calculation in plain
    language so the estimate is fully auditable.

    Returns:
        List of forecast dicts, sorted by forecast_lambda descending.
    """
    try:
        complaints = load_raw_complaints()
        hotspots = detect_hotspots(complaints, eps_km=eps_km, min_samples=min_samples)
        return compute_risk_forecast(hotspots=hotspots, raw_complaints=complaints)
    except Exception as e:
        logger.error(f"[geo/risk-forecast] Forecast computation failed: {e}", exc_info=True)
        return []


@router.get(
    "/raw-complaints",
    summary="Individual complaint GPS points (debug)",
    include_in_schema=False,   # hide from public docs; admin use only
)
async def get_raw_complaints():
    """Returns expanded individual complaint points. Debug endpoint."""
    return load_raw_complaints()
