"""
# ⚠️  SYNTHETIC DATA — Not derived from real incidents or persons.

SafeNet AI — Geospatial Module: Verification Script

Runs DBSCAN hotspot detection and Poisson risk forecast on the
synthetic complaints data, prints a full summary.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.geospatial.hotspots import load_raw_complaints, detect_hotspots, compute_risk_forecast


def run_verification():
    print("\n" + "=" * 62)
    print("  SafeNet AI — Geospatial Verification")
    print("=" * 62)

    # ── 1. Raw complaint expansion ─────────────────────────────────────────
    print("\n📍  Loading raw complaint points…")
    complaints = load_raw_complaints()
    print(f"  Total individual complaint points: {len(complaints)}")
    lat_range = (min(p["lat"] for p in complaints), max(p["lat"] for p in complaints))
    lng_range = (min(p["lng"] for p in complaints), max(p["lng"] for p in complaints))
    print(f"  Lat range:  {lat_range[0]:.4f} – {lat_range[1]:.4f}")
    print(f"  Lng range:  {lng_range[0]:.4f} – {lng_range[1]:.4f}")
    from collections import Counter
    type_dist = Counter(p["complaint_type"] for p in complaints)
    print("  Complaint type distribution:")
    for t, n in type_dist.most_common():
        print(f"    {t:25s}: {n:4d} ({n/len(complaints)*100:.1f}%)")

    # ── 2. DBSCAN clustering ───────────────────────────────────────────────
    print("\n🗺️   Running DBSCAN (eps=1.5 km, min_samples=5)…")
    hotspots = detect_hotspots(complaints, eps_km=1.5, min_samples=5)
    print(f"  Hotspots detected: {len(hotspots)}")
    print()
    print(f"  {'ID':15s} {'Lat':9s} {'Lng':9s} {'Type':8s} {'Pts':5s} {'Intensity':9s} {'Top Complaint'}")
    print("  " + "-" * 72)
    for h in hotspots:
        print(
            f"  {h['id']:15s} "
            f"{h['lat']:9.5f} "
            f"{h['lng']:9.5f} "
            f"{h['type']:8s} "
            f"{h['point_count']:5d} "
            f"{h['intensity']:9.4f}  "
            f"{h['top_complaint_type']}"
        )

    type_counts = Counter(h["type"] for h in hotspots)
    print(f"\n  Severity breakdown: {dict(type_counts)}")

    # ── 3. Risk forecast ───────────────────────────────────────────────────
    print("\n📈  Computing next-24h Poisson risk forecast…")
    forecast = compute_risk_forecast(hotspots=hotspots, raw_complaints=complaints)
    print(f"  Zones forecast: {len(forecast)}")
    print()
    print(f"  {'Zone':15s} {'Now':8s} {'λ_24h':7s} {'CI Low':7s} {'CI High':8s} {'Tomorrow':8s} {'DOW':5s}")
    print("  " + "-" * 66)
    for f in forecast[:8]:
        print(
            f"  {f['hotspot_id']:15s} "
            f"{f['current_type']:8s} "
            f"{f['forecast_lambda']:7.2f} "
            f"{f['forecast_low']:7.2f} "
            f"{f['forecast_high']:8.2f} "
            f"{f['forecast_type']:8s} "
            f"×{f['dow_factor']:.2f}"
        )

    print(f"\n  Model explanation for top zone:")
    if forecast:
        print(f"  {forecast[0]['model_note']}")

    # ── 4. Schema check (matches Leaflet CircleMarker contract) ───────────
    print("\n🔍  Schema validation against Leaflet contract…")
    required_keys = {"id", "lat", "lng", "intensity", "radius", "type"}
    for h in hotspots:
        missing = required_keys - set(h.keys())
        if missing:
            print(f"  ❌  {h['id']} missing keys: {missing}")
            break
    else:
        print(f"  ✅  All {len(hotspots)} hotspots have required Leaflet fields")
        print(f"      (id, lat, lng, intensity, radius, type)")

    print("\n" + "=" * 62)
    print("  ✅  Verification complete.")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    run_verification()
