"""
SafeNet AI — Orchestrator: Configurable Weights & Thresholds

All tunable parameters live here. Changing a weight or threshold requires
editing only this file — the graph.py logic is untouched.

Compound Risk Score formula:
    CRS = (
        W_SCAM   * scam_score_norm        +
        W_GRAPH  * graph_anomaly_norm     +
        W_GEO    * geo_density_norm       +
        W_RECENCY * recency_factor
    ) * 100

Each component is normalised to [0, 1] before weighting.
Weights must sum to 1.0 — a startup assertion enforces this.
"""

# ── Compound Risk Score weights ────────────────────────────────────────────────
W_SCAM    = 0.40   # Module A: scam call pattern score
W_GRAPH   = 0.30   # Module C: fraud graph anomaly / mule score
W_GEO     = 0.20   # Module D: geospatial hotspot density
W_RECENCY = 0.10   # Recency bonus — events in last 1h score higher

assert abs(W_SCAM + W_GRAPH + W_GEO + W_RECENCY - 1.0) < 1e-9, \
    "Orchestrator weights must sum to 1.0"

# ── Escalation thresholds ──────────────────────────────────────────────────────
ESCALATION_THRESHOLD  = 70.0   # CRS ≥ this → generate incident report + alert
WARNING_THRESHOLD     = 40.0   # CRS ≥ this → add to feed as HIGH
INFO_THRESHOLD        = 20.0   # CRS ≥ this → add to feed as MEDIUM

# ── Recency config ─────────────────────────────────────────────────────────────
RECENCY_FULL_WINDOW_HOURS  = 1    # Within this window → full recency bonus (1.0)
RECENCY_HALF_WINDOW_HOURS  = 6    # Beyond this → recency factor decays linearly
RECENCY_MIN_FACTOR         = 0.1  # Floor for recency factor

# ── PDF report output directory ────────────────────────────────────────────────
from pathlib import Path
REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "reports"

# ── Audit log ─────────────────────────────────────────────────────────────────
AUDIT_LOG_PATH = Path(__file__).parent / "audit_log.jsonl"

# ── Feed retention ─────────────────────────────────────────────────────────────
MAX_FEED_EVENTS = 100   # Keep last N events in the orchestrator feed
