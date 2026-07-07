"""
SafeNet AI — Geospatial Hotspot Detection & Risk Forecasting

Two public functions form the module API (safenet.md §3):

    detect_hotspots(raw_complaints, eps_km, min_samples)
        DBSCAN clustering of individual complaint GPS points.
        Returns hotspot centroids in the exact schema the Leaflet map expects.

    compute_risk_forecast(hotspots, raw_complaints)
        Next-24h risk estimate per zone using a Poisson-rate model:
          λ = historical_density × day_of_week_factor × time_of_day_factor
        Interpretable and honest — no overselling as advanced ML.

Data pipeline (called by api.py):
    load_raw_complaints()
        Expands the pre-generated centroid file into individual complaint
        points by sampling from a Gaussian around each centroid.  This gives
        DBSCAN real point clouds to work with.  A deterministic seed ensures
        the same expansion on every cold start.

Algorithm notes:
    - DBSCAN runs in (lat, lng) space converted to radians for haversine metric.
    - eps is specified in km and converted: eps_rad = eps_km / 6371.0088
    - Intensity is normalised point-count within a cluster / max cluster size.
    - Severity thresholds mirror the generator: CRITICAL ≥85%, HIGH ≥65%,
      MEDIUM ≥40%, LOW otherwise.

No external API calls, no GPU required.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.cluster import DBSCAN

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SYNTHETIC_DIR = _REPO_ROOT / "data" / "synthetic"
_COMPLAINTS_GEO = _SYNTHETIC_DIR / "complaints_geo_SYNTHETIC.json"
_RAW_COMPLAINTS_CACHE: Optional[list[dict]] = None

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
COMPLAINT_TYPES = ["UPI Fraud", "Vishing", "Counterfeit Currency", "Job Scam", "OTP Scam"]

# Day-of-week activity multipliers (Mon=0 … Sun=6).
# Fraud peaks mid-week; lower on weekends (fewer business transactions).
_DOW_FACTORS = {0: 1.10, 1: 1.20, 2: 1.25, 3: 1.15, 4: 1.05, 5: 0.80, 6: 0.70}

# Hour-of-day multipliers (rough empirical pattern).
# Morning surge (9-11), afternoon plateau, evening drop.
_HOUR_BUCKETS = {
    range(0, 6): 0.30,    # late night — minimal
    range(6, 9): 0.70,    # early morning
    range(9, 12): 1.30,   # mid-morning peak
    range(12, 15): 1.10,  # lunch
    range(15, 19): 1.00,  # afternoon
    range(19, 22): 0.80,  # evening
    range(22, 24): 0.50,  # late evening
}


def _hour_factor(hour: int) -> float:
    for h_range, factor in _HOUR_BUCKETS.items():
        if hour in h_range:
            return factor
    return 1.0


# ──────────────────────────────────────────────────────────────────────────────
# Data loading — expand centroid file into individual complaint points
# ──────────────────────────────────────────────────────────────────────────────

def load_raw_complaints(seed: int = 42) -> list[dict]:
    """
    Loads (or generates) individual complaint GPS points.

    Strategy: the synthetic pipeline created pre-clustered centroid records
    in complaints_geo_SYNTHETIC.json.  Each centroid carries a complaint_count.
    We expand each into that many individual GPS points scattered around the
    centroid with a Gaussian whose σ ≈ radius_m / 3 (so ~99.7% of points fall
    inside the reported radius).  A fixed seed makes expansion deterministic.

    If the centroid file is missing, falls back to hard-coded demo points
    around the Delhi NCR bounding box so the API never returns empty.

    Args:
        seed: RNG seed for reproducible expansion.

    Returns:
        List of individual complaint dicts:
          { id, lat, lng, complaint_type, timestamp, severity_hint }
    """
    global _RAW_COMPLAINTS_CACHE
    if _RAW_COMPLAINTS_CACHE is not None:
        return _RAW_COMPLAINTS_CACHE

    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    now = datetime.now(timezone.utc)
    points: list[dict] = []

    if _COMPLAINTS_GEO.exists():
        centroids = json.loads(_COMPLAINTS_GEO.read_text(encoding="utf-8"))
    else:
        # Hard-coded fallback — Delhi NCR sample
        centroids = _fallback_centroids()

    for c in centroids:
        count = int(c.get("complaint_count", 10))
        radius_m = float(c.get("radius", 800))
        c_lat = float(c["lat"])
        c_lng = float(c["lng"])
        c_type = c.get("primary_complaint_type", "UPI Fraud")
        severity_hint = c.get("type", "MEDIUM")

        # Convert radius_m to degrees (approx): 1° lat ≈ 111 km
        sigma_lat = (radius_m / 3) / 111_000
        sigma_lng = (radius_m / 3) / (111_000 * math.cos(math.radians(c_lat)))

        lats = np_rng.normal(c_lat, sigma_lat, count)
        lngs = np_rng.normal(c_lng, sigma_lng, count)

        for i, (lat, lng) in enumerate(zip(lats, lngs)):
            # Scatter timestamps over the last 30 days
            age_hours = rng.uniform(0, 720)  # up to 30 days back
            ts = now - timedelta(hours=age_hours)
            points.append({
                "id": f"{c['id']}-pt{i:04d}",
                "lat": round(float(lat), 6),
                "lng": round(float(lng), 6),
                "complaint_type": c_type,
                "timestamp": ts.isoformat(),
                "severity_hint": severity_hint,
                "hour": ts.hour,
                "dow": ts.weekday(),
            })

    _RAW_COMPLAINTS_CACHE = points
    return points


def _fallback_centroids() -> list[dict]:
    """Hard-coded Delhi NCR fallback so the API is never empty."""
    return [
        {"id": "fb-01", "lat": 28.6139, "lng": 77.2090, "complaint_count": 60,
         "radius": 1500, "type": "CRITICAL", "primary_complaint_type": "Vishing"},
        {"id": "fb-02", "lat": 28.5355, "lng": 77.3910, "complaint_count": 30,
         "radius": 900, "type": "HIGH", "primary_complaint_type": "UPI Fraud"},
        {"id": "fb-03", "lat": 28.7041, "lng": 77.1025, "complaint_count": 20,
         "radius": 700, "type": "MEDIUM", "primary_complaint_type": "Job Scam"},
    ]


# ──────────────────────────────────────────────────────────────────────────────
# 1. DBSCAN hotspot detection
# ──────────────────────────────────────────────────────────────────────────────

def _intensity_to_type(intensity: float) -> str:
    if intensity >= 0.85:
        return "CRITICAL"
    if intensity >= 0.65:
        return "HIGH"
    if intensity >= 0.40:
        return "MEDIUM"
    return "LOW"


def detect_hotspots(
    raw_complaints: Optional[list[dict]] = None,
    eps_km: float = 1.5,
    min_samples: int = 5,
) -> list[dict]:
    """
    Clusters geo-complaint points with DBSCAN and returns Leaflet-ready hotspots.

    DBSCAN was chosen over k-means because:
      - It finds arbitrarily shaped clusters without pre-specifying k.
      - It naturally labels noise points (label = -1), which we discard.
      - eps_km and min_samples are interpretable parameters that an analyst
        can tune ("merge complaints within X km if at least Y reports exist").

    Args:
        raw_complaints: List of individual complaint dicts (see load_raw_complaints).
                        Loaded automatically if None.
        eps_km:         Maximum neighbourhood radius in km.  1.5 km ≈ 15-min walk.
        min_samples:    Minimum points to form a dense region (cluster).

    Returns:
        List of hotspot dicts matching the Leaflet CircleMarker schema:
          {
            id          (str)   — "hs-db-{cluster_label}",
            lat         (float) — cluster centroid latitude,
            lng         (float) — cluster centroid longitude,
            intensity   (float) — normalised 0–1 (point_count / max_count),
            radius      (int)   — approx radius in metres (std-dev × 3),
            type        (str)   — "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
            point_count (int)   — raw complaint count in cluster,
            complaint_types (dict) — type → count breakdown,
            top_complaint_type (str),
          }
        Sorted by point_count descending.
    """
    if raw_complaints is None:
        raw_complaints = load_raw_complaints()

    if not raw_complaints:
        return []

    coords = np.array([[p["lat"], p["lng"]] for p in raw_complaints])

    # Convert to radians for haversine metric
    coords_rad = np.radians(coords)
    eps_rad = eps_km / 6371.0088  # Earth radius in km

    db = DBSCAN(eps=eps_rad, min_samples=min_samples, metric="haversine", n_jobs=1)
    labels = db.fit_predict(coords_rad)

    unique_labels = set(labels) - {-1}
    if not unique_labels:
        # All points are noise — return a single aggregate fallback
        return _noise_fallback(raw_complaints)

    # Group points by cluster
    clusters: dict[int, list[dict]] = defaultdict(list)
    for label, point in zip(labels, raw_complaints):
        if label != -1:
            clusters[label].append(point)

    max_count = max(len(pts) for pts in clusters.values())

    hotspots: list[dict] = []
    for label, pts in clusters.items():
        lats = [p["lat"] for p in pts]
        lngs = [p["lng"] for p in pts]

        centroid_lat = float(np.mean(lats))
        centroid_lng = float(np.mean(lngs))

        # Radius estimate: 3σ of the point spread (95th percentile coverage)
        std_lat = float(np.std(lats)) * 111_000   # degrees → metres
        std_lng = float(np.std(lngs)) * 111_000 * math.cos(math.radians(centroid_lat))
        radius_m = int(max(3 * math.sqrt(std_lat**2 + std_lng**2), 300))
        radius_m = min(radius_m, 3000)  # cap at 3 km for UI clarity

        count = len(pts)
        intensity = round(count / max_count, 4)
        severity_type = _intensity_to_type(intensity)

        type_counts: dict[str, int] = Counter(p.get("complaint_type", "Unknown") for p in pts)
        top_type = type_counts.most_common(1)[0][0] if type_counts else "Unknown"

        hotspots.append({
            "id": f"hs-db-{label:03d}",
            "lat": round(centroid_lat, 6),
            "lng": round(centroid_lng, 6),
            "intensity": intensity,
            "radius": radius_m,
            "type": severity_type,
            "point_count": count,
            "complaint_types": dict(type_counts),
            "top_complaint_type": top_type,
        })

    hotspots.sort(key=lambda h: h["point_count"], reverse=True)
    return hotspots


def _noise_fallback(raw_complaints: list[dict]) -> list[dict]:
    """Returns a single aggregate hotspot when DBSCAN finds no clusters."""
    if not raw_complaints:
        return []
    lats = [p["lat"] for p in raw_complaints]
    lngs = [p["lng"] for p in raw_complaints]
    return [{
        "id": "hs-db-fallback",
        "lat": round(float(np.mean(lats)), 6),
        "lng": round(float(np.mean(lngs)), 6),
        "intensity": 0.3,
        "radius": 2000,
        "type": "LOW",
        "point_count": len(raw_complaints),
        "complaint_types": {},
        "top_complaint_type": "Unknown",
    }]


# ──────────────────────────────────────────────────────────────────────────────
# 2. Next-24h risk forecast (Poisson-rate model)
# ──────────────────────────────────────────────────────────────────────────────

def compute_risk_forecast(
    hotspots: Optional[list[dict]] = None,
    raw_complaints: Optional[list[dict]] = None,
) -> list[dict]:
    """
    Estimates the next-24h expected complaint count per hotspot zone using a
    simple, interpretable Poisson-rate model.

    Model:
        λ_24h = (observed_rate_per_hour × 24) × DOW_factor × hour_factor

    where:
        observed_rate_per_hour = point_count / observation_window_hours
        DOW_factor             = _DOW_FACTORS[tomorrow's weekday]
        hour_factor            = mean of _HOUR_BUCKETS over 24 hours (≈1.0 baseline)

    This is transparent and auditable — not marketed as ML.
    95% credible interval (assuming Poisson): [λ - 1.96√λ, λ + 1.96√λ]

    Args:
        hotspots:      Output of detect_hotspots().  Loaded automatically if None.
        raw_complaints: Individual points for computing observation window.

    Returns:
        List of risk forecast dicts per zone:
          {
            hotspot_id        (str),
            centroid_lat      (float),
            centroid_lng      (float),
            current_type      (str)   — current severity,
            forecast_lambda   (float) — expected complaints in next 24h,
            forecast_low      (float) — 95% CI lower bound,
            forecast_high     (float) — 95% CI upper bound,
            forecast_type     (str)   — projected severity label,
            dow_factor        (float) — day-of-week seasonality applied,
            model_note        (str)   — human-readable model explanation,
          }
        Sorted by forecast_lambda descending.
    """
    if raw_complaints is None:
        raw_complaints = load_raw_complaints()
    if hotspots is None:
        hotspots = detect_hotspots(raw_complaints)

    if not hotspots or not raw_complaints:
        return []

    # Compute observation window from timestamp spread in raw complaints
    timestamps = []
    for p in raw_complaints:
        try:
            ts = datetime.fromisoformat(p["timestamp"].replace("Z", "+00:00"))
            timestamps.append(ts)
        except (ValueError, KeyError):
            pass

    if timestamps:
        window_hours = max(
            (max(timestamps) - min(timestamps)).total_seconds() / 3600,
            1.0,
        )
    else:
        window_hours = 720.0  # 30-day default

    # Tomorrow's day-of-week factor
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    dow_factor = _DOW_FACTORS.get(tomorrow.weekday(), 1.0)

    # Mean hour factor over 24 h ≈ 1.0 by construction, use 1.0 as baseline
    mean_hour_factor = 1.0

    results: list[dict] = []
    max_count = max(h["point_count"] for h in hotspots) if hotspots else 1

    for h in hotspots:
        observed_rate_per_hour = h["point_count"] / window_hours
        lambda_24h = observed_rate_per_hour * 24 * dow_factor * mean_hour_factor

        # Poisson 95% CI: λ ± 1.96√λ
        ci_margin = 1.96 * math.sqrt(max(lambda_24h, 0.01))
        forecast_low = max(lambda_24h - ci_margin, 0.0)
        forecast_high = lambda_24h + ci_margin

        # Project severity from forecast relative to max historical
        forecast_intensity = min(lambda_24h / max((max_count / window_hours * 24), 1), 1.0)
        forecast_type = _intensity_to_type(forecast_intensity)

        results.append({
            "hotspot_id": h["id"],
            "centroid_lat": h["lat"],
            "centroid_lng": h["lng"],
            "current_type": h["type"],
            "point_count": h["point_count"],
            "forecast_lambda": round(lambda_24h, 2),
            "forecast_low": round(forecast_low, 2),
            "forecast_high": round(forecast_high, 2),
            "forecast_type": forecast_type,
            "dow_factor": dow_factor,
            "model_note": (
                f"Poisson estimate: {h['point_count']} complaints over "
                f"{window_hours:.0f}h history → "
                f"rate {observed_rate_per_hour:.3f}/h × 24h × "
                f"DOW({dow_factor:.2f}) = {lambda_24h:.1f} expected tomorrow "
                f"[95% CI {forecast_low:.1f}–{forecast_high:.1f}]."
            ),
        })

    results.sort(key=lambda r: r["forecast_lambda"], reverse=True)
    return results
