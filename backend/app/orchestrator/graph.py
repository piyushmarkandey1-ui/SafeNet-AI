"""
SafeNet AI — LangGraph Orchestration Agent

State machine that correlates signals from all 5 modules into a single
Compound Risk Score (CRS) and drives escalation automatically.

Graph nodes (in execution order):
  ingest         → validates and normalises the incoming event
  enrich_graph   → Module C: get_case_summary() for any entity in the event
  enrich_geo     → Module D: nearest hotspot density for event location
  score          → computes CRS from weighted module signals
  decide         → routes on CRS: escalate | warn | info | ignore
  escalate       → generates incident report (JSON + PDF) + citizen alert
  emit_feed      → writes the compound event to the orchestrator feed + audit log

All module calls are direct Python function calls — no HTTP hops.

Public API:
  process_event(raw_event: dict) → OrchestratorResult
"""

from __future__ import annotations

import json
import math
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from app.orchestrator.settings import (
    W_SCAM, W_GRAPH, W_GEO, W_RECENCY,
    ESCALATION_THRESHOLD, WARNING_THRESHOLD, INFO_THRESHOLD,
    RECENCY_FULL_WINDOW_HOURS, RECENCY_HALF_WINDOW_HOURS, RECENCY_MIN_FACTOR,
    REPORTS_DIR, AUDIT_LOG_PATH, MAX_FEED_EVENTS,
)

# ── Orchestrator event feed (in-memory, replaces per-module feeds) ─────────────
orchestrator_feed: list[dict] = []


# ── LangGraph State ────────────────────────────────────────────────────────────

class OrchState(TypedDict):
    """Complete state carried through every node of the graph."""
    # Input
    raw_event: dict

    # Enrichment outputs
    scam_score: float           # 0–100 from Module A classifier
    graph_case: dict            # Module C case summary (may be empty)
    graph_anomaly_score: float  # 0–100 mule/ring score from graph
    nearest_hotspot: dict       # nearest geospatial cluster
    geo_density: float          # 0–1 hotspot intensity

    # Scoring
    recency_factor: float       # 0–1 decay based on event age
    crs: float                  # Compound Risk Score 0–100
    crs_breakdown: dict         # full weight × component breakdown for audit

    # Decision
    action: str                 # "escalate" | "warn" | "info" | "ignore"
    severity: str               # "critical" | "high" | "medium" | "low"

    # Escalation outputs
    incident_report: dict
    report_path_json: str
    report_path_pdf: str
    citizen_alert_sent: bool

    # Feed event (final shape consumed by frontend)
    feed_event: dict

    # Audit
    audit_entry: dict


# ── Helper: geo distance ───────────────────────────────────────────────────────

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns great-circle distance in km between two GPS points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


# ── Node 1: ingest ─────────────────────────────────────────────────────────────

def node_ingest(state: OrchState) -> OrchState:
    """
    Validates and normalises the incoming raw event.

    Expected raw_event fields (all optional with defaults):
      type          (str)  — SCAM_CALL | COUNTERFEIT | FRAUD_NETWORK | GEO_ALERT
      entities      (list) — phone numbers, account IDs, etc.
      location      (dict) — {lat, lng, name}
      scam_score    (float)— pre-computed score from Module A (0–100)
      timestamp     (str)  — ISO datetime of the original event
      transcript    (str)  — raw text for re-scoring if needed
      title         (str)
      description   (str)
    """
    ev = state["raw_event"]
    now = datetime.now(timezone.utc)

    # Parse or default timestamp
    ts_str = ev.get("timestamp", now.isoformat())
    try:
        ev_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if ev_time.tzinfo is None:
            ev_time = ev_time.replace(tzinfo=timezone.utc)
    except ValueError:
        ev_time = now

    # Recency factor: 1.0 within 1h, linear decay to RECENCY_MIN_FACTOR at 6h
    age_hours = (now - ev_time).total_seconds() / 3600
    if age_hours <= RECENCY_FULL_WINDOW_HOURS:
        recency = 1.0
    elif age_hours >= RECENCY_HALF_WINDOW_HOURS:
        recency = RECENCY_MIN_FACTOR
    else:
        span = RECENCY_HALF_WINDOW_HOURS - RECENCY_FULL_WINDOW_HOURS
        recency = 1.0 - (1.0 - RECENCY_MIN_FACTOR) * (age_hours - RECENCY_FULL_WINDOW_HOURS) / span

    # Use pre-computed scam score if provided, else 0 (no re-score in ingest)
    scam_score = float(ev.get("scam_score", ev.get("score", 0.0)))
    # Re-score from transcript if scam_score absent but transcript present
    if scam_score == 0 and ev.get("transcript"):
        try:
            from app.scam_detector.classifier import score_call
            result = score_call(ev["transcript"], {
                "is_spoofed": ev.get("is_spoofed", False),
                "duration_sec": ev.get("duration_sec", 0),
                "video_requested": ev.get("video_requested", False),
            })
            scam_score = float(result["risk_score"])
        except Exception:
            pass

    return {
        **state,
        "scam_score": scam_score,
        "recency_factor": round(recency, 4),
        # Defaults — will be filled by enrichment nodes
        "graph_case": {},
        "graph_anomaly_score": 0.0,
        "nearest_hotspot": {},
        "geo_density": 0.0,
    }


# ── Node 2: enrich_graph ───────────────────────────────────────────────────────

def node_enrich_graph(state: OrchState) -> OrchState:
    """
    Module C enrichment: gets case summary + mule anomaly score for any
    entity mentioned in the event.

    Uses the first entity in event.entities that resolves in the graph.
    Silently skips if no entities or graph is unreachable.
    """
    entities = state["raw_event"].get("entities", [])
    graph_case = {}
    graph_anomaly_score = 0.0

    for entity_id in entities:
        try:
            from app.fraud_graph.analysis import get_case_summary
            case = get_case_summary(str(entity_id), hops=2)
            graph_case = case
            graph_anomaly_score = float(case.get("riskScore", 0.0))
            break
        except (KeyError, Exception):
            continue

    return {**state, "graph_case": graph_case, "graph_anomaly_score": graph_anomaly_score}


# ── Node 3: enrich_geo ─────────────────────────────────────────────────────────

def node_enrich_geo(state: OrchState) -> OrchState:
    """
    Module D enrichment: finds the nearest DBSCAN hotspot cluster to the
    event's location and reads its intensity as geo_density.

    Falls back to 0 density if location is missing or hotspots unavailable.
    """
    location = state["raw_event"].get("location", {})
    lat = location.get("lat")
    lng = location.get("lng")

    nearest_hotspot = {}
    geo_density = 0.0

    if lat is not None and lng is not None:
        try:
            from app.geospatial.hotspots import detect_hotspots, load_raw_complaints
            hotspots = detect_hotspots(load_raw_complaints())
            if hotspots:
                closest = min(
                    hotspots,
                    key=lambda h: _haversine_km(lat, lng, h["lat"], h["lng"]),
                )
                dist_km = _haversine_km(lat, lng, closest["lat"], closest["lng"])
                # Only count hotspot if event is within its radius + 1 km buffer
                effective_radius_km = (closest["radius"] / 1000) + 1.0
                if dist_km <= effective_radius_km:
                    nearest_hotspot = closest
                    geo_density = float(closest["intensity"])
        except Exception:
            pass

    return {**state, "nearest_hotspot": nearest_hotspot, "geo_density": geo_density}


# ── Node 4: score ──────────────────────────────────────────────────────────────

def node_score(state: OrchState) -> OrchState:
    """
    Computes the Compound Risk Score (CRS) from weighted module signals.

    Formula:
      CRS = (W_SCAM  * scam_norm +
             W_GRAPH * graph_norm +
             W_GEO   * geo_norm  +
             W_RECENCY * recency) * 100

    All inputs are already in [0, 1] range (scores divided by 100 where needed).
    Full breakdown is logged in crs_breakdown for the audit trail.
    """
    scam_norm   = min(state["scam_score"] / 100.0, 1.0)
    graph_norm  = min(state["graph_anomaly_score"] / 100.0, 1.0)
    geo_norm    = min(state["geo_density"], 1.0)
    recency     = state["recency_factor"]

    weighted_scam   = W_SCAM   * scam_norm
    weighted_graph  = W_GRAPH  * graph_norm
    weighted_geo    = W_GEO    * geo_norm
    weighted_recency = W_RECENCY * recency

    crs = round((weighted_scam + weighted_graph + weighted_geo + weighted_recency) * 100, 2)

    breakdown = {
        "scam":     {"raw": state["scam_score"],            "norm": round(scam_norm, 4),  "weighted": round(weighted_scam * 100, 2),    "weight": W_SCAM},
        "graph":    {"raw": state["graph_anomaly_score"],   "norm": round(graph_norm, 4), "weighted": round(weighted_graph * 100, 2),   "weight": W_GRAPH},
        "geo":      {"raw": state["geo_density"],           "norm": round(geo_norm, 4),   "weighted": round(weighted_geo * 100, 2),     "weight": W_GEO},
        "recency":  {"raw": state["recency_factor"],        "norm": round(recency, 4),    "weighted": round(weighted_recency * 100, 2), "weight": W_RECENCY},
        "crs": crs,
        "formula": f"({W_SCAM}×{scam_norm:.2f} + {W_GRAPH}×{graph_norm:.2f} + {W_GEO}×{geo_norm:.2f} + {W_RECENCY}×{recency:.2f}) × 100 = {crs}",
    }

    return {**state, "crs": crs, "crs_breakdown": breakdown}


# ── Node 5: decide ─────────────────────────────────────────────────────────────

def node_decide(state: OrchState) -> OrchState:
    """Routes the event to the correct action branch based on CRS thresholds."""
    crs = state["crs"]
    if crs >= ESCALATION_THRESHOLD:
        action, severity = "escalate", "critical"
    elif crs >= WARNING_THRESHOLD:
        action, severity = "warn", "high"
    elif crs >= INFO_THRESHOLD:
        action, severity = "info", "medium"
    else:
        action, severity = "ignore", "low"
    return {**state, "action": action, "severity": severity}


def _route_decision(state: OrchState) -> str:
    """LangGraph conditional edge: maps action to next node name."""
    return state["action"]   # "escalate" | "warn" | "info" | "ignore"


# ── Node 6a: escalate ──────────────────────────────────────────────────────────

def node_escalate(state: OrchState) -> OrchState:
    """
    Triggered when CRS ≥ ESCALATION_THRESHOLD.

    Actions:
      1. Builds a structured incident report (JSON + PDF).
      2. If a victim phone number is identifiable, calls Module E (Citizen Shield)
         to compose a warning message (logged, not actually sent in demo).
      3. Returns paths to the generated artefacts.
    """
    ev = state["raw_event"]
    case = state["graph_case"]
    crs  = state["crs"]
    bd   = state["crs_breakdown"]

    incident_id = f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:6].upper()}"

    report = {
        "incident_id": incident_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_classification": "SYNTHETIC — DEMO ONLY",
        "disclaimer": "⚠️ SYNTHETIC DATA — This report was auto-generated from artificial data for demonstration purposes. Not legally valid.",
        "compound_risk_score": crs,
        "severity": state["severity"],
        "score_breakdown": bd,
        "source_event": {
            "type": ev.get("type", "UNKNOWN"),
            "title": ev.get("title", ""),
            "entities": ev.get("entities", []),
            "location": ev.get("location", {}),
            "timestamp": ev.get("timestamp", ""),
        },
        "graph_context": {
            "case_id": case.get("caseId", "N/A"),
            "primary_threat": case.get("primaryThreat", "N/A"),
            "risk_score": case.get("riskScore", 0),
            "connected_nodes": case.get("connected_nodes", 0),
            "evidence_items": case.get("evidenceItems", []),
            "linked_entities": case.get("linkedEntities", [])[:10],
        },
        "geo_context": {
            "nearest_hotspot_id": state["nearest_hotspot"].get("id", "N/A"),
            "hotspot_type": state["nearest_hotspot"].get("type", "N/A"),
            "hotspot_intensity": state["nearest_hotspot"].get("intensity", 0),
        },
        "recommended_action": case.get("recommendedAction") or (
            f"CRS={crs:.1f} exceeds escalation threshold ({ESCALATION_THRESHOLD}). "
            "Immediate review required. Freeze associated accounts and file SAR."
        ),
    }

    # ── Save JSON ──────────────────────────────────────────────────────────────
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / f"{incident_id}.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    # ── Generate PDF ───────────────────────────────────────────────────────────
    pdf_path = _generate_pdf(report, incident_id)

    # ── Citizen Shield warning (Module E — no HTTP hop) ────────────────────────
    citizen_alert_sent = False
    victim_entities = ev.get("entities", [])
    if victim_entities:
        try:
            from app.citizen_shield.agent import ask
            warning_query = (
                f"There is an active scam targeting this number: "
                f"{victim_entities[0]}. CBI impersonation with arrest warrant threat detected."
            )
            alert_response = ask(warning_query, language="en")
            # In a real system this would push via SMS/notification API
            # For demo: log it
            report["citizen_alert"] = {
                "status": "COMPOSED_NOT_SENT",
                "message": alert_response["text"][:200] + "…",
                "note": "Demo system — alert composed but not transmitted.",
            }
            citizen_alert_sent = True
        except Exception:
            pass

    return {
        **state,
        "incident_report": report,
        "report_path_json": str(json_path),
        "report_path_pdf": str(pdf_path),
        "citizen_alert_sent": citizen_alert_sent,
    }


def _generate_pdf(report: dict, incident_id: str) -> Path:
    """
    Generates a minimal PDF incident report using fpdf2.

    Keeps it simple — title, metadata table, score breakdown, key findings.
    No external fonts required (uses fpdf2's built-in core fonts).
    """
    from fpdf import FPDF

    def pdf_text(value: Any, max_len: int | None = None) -> str:
        text = str(value)
        if max_len is not None:
            text = text[:max_len]
        return text.encode("latin-1", errors="replace").decode("latin-1")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Header ─────────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, pdf_text("SafeNet AI - Incident Report"), ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, pdf_text(report["disclaimer"], 110), ln=True, align="C")
    pdf.ln(4)

    # ── Metadata ───────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Incident Details", ln=True)
    pdf.set_font("Helvetica", "", 10)
    meta = [
        ("Incident ID",   incident_id),
        ("Generated",     report["generated_at"]),
        ("Severity",      report["severity"].upper()),
        ("CRS",           f"{report['compound_risk_score']:.1f} / 100"),
        ("Case ID",       report["graph_context"]["case_id"]),
        ("Primary Threat",report["graph_context"]["primary_threat"]),
    ]
    for label, value in meta:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(50, 7, pdf_text(f"{label}:"))
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, pdf_text(value, 80), ln=True)

    pdf.ln(4)

    # ── Score Breakdown ────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Compound Risk Score Breakdown", ln=True)
    pdf.set_font("Helvetica", "", 10)
    bd = report["score_breakdown"]
    components = [
        ("Scam Signal",      bd["scam"]["raw"],    bd["scam"]["weighted"],    bd["scam"]["weight"]),
        ("Graph Anomaly",    bd["graph"]["raw"],   bd["graph"]["weighted"],   bd["graph"]["weight"]),
        ("Geo Density",      bd["geo"]["raw"],     bd["geo"]["weighted"],     bd["geo"]["weight"]),
        ("Recency Factor",   bd["recency"]["raw"], bd["recency"]["weighted"], bd["recency"]["weight"]),
    ]
    for name, raw, wt_score, weight in components:
        pdf.cell(0, 7,
            pdf_text(f"  {name:20s}  raw={float(raw):.2f}  weight={weight:.2f}  contribution={float(wt_score):.2f}"),
            ln=True)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, pdf_text(f"  TOTAL CRS = {report['compound_risk_score']:.2f}"), ln=True)

    pdf.ln(4)

    # ── Recommended Action ──────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Recommended Action", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 7, pdf_text(report["recommended_action"], 400))

    # ── Evidence Items ─────────────────────────────────────────────────────────
    evidence = report["graph_context"].get("evidence_items", [])
    if evidence:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Evidence Items", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for item in evidence[:5]:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 7,
                pdf_text(
                    f"  [{item.get('type', '?')}] conf={item.get('confidence', 0):.2f}  "
                    f"{str(item.get('snippet', ''))[:120]}"
                )
            )

    pdf_path = REPORTS_DIR / f"{incident_id}.pdf"
    pdf.output(str(pdf_path))
    return pdf_path


# ── Node 6b/6c: warn / info ────────────────────────────────────────────────────

def node_warn(state: OrchState) -> OrchState:
    """Warning path — no full report, but event is flagged HIGH."""
    return {
        **state,
        "incident_report": {},
        "report_path_json": "",
        "report_path_pdf": "",
        "citizen_alert_sent": False,
    }


def node_info(state: OrchState) -> OrchState:
    """Info path — event added to feed as MEDIUM."""
    return {
        **state,
        "incident_report": {},
        "report_path_json": "",
        "report_path_pdf": "",
        "citizen_alert_sent": False,
    }


def node_ignore(state: OrchState) -> OrchState:
    """Ignore path — event does not reach the feed."""
    return {
        **state,
        "incident_report": {},
        "report_path_json": "",
        "report_path_pdf": "",
        "citizen_alert_sent": False,
    }


# ── Node 7: emit_feed ──────────────────────────────────────────────────────────

def node_emit_feed(state: OrchState) -> OrchState:
    """
    Builds the final compound feed event and writes it to:
      1. orchestrator_feed (in-memory, served by /orchestrator/dashboard-feed)
      2. audit_log.jsonl (append-only, one JSON object per line)
    """
    ev = state["raw_event"]
    crs = state["crs"]
    bd  = state["crs_breakdown"]

    event_id = f"orch-{str(uuid.uuid4())[:8]}"
    ts = datetime.now(timezone.utc).isoformat()

    # Build feed event in the exact shape the RiskFeed component expects
    feed_event = {
        "id": event_id,
        "type": ev.get("type", "SCAM_CALL"),
        "severity": state["severity"],
        "timestamp": ts,
        "title": ev.get("title") or f"Compound Risk Event — CRS {crs:.0f}",
        "description": (
            f"CRS {crs:.1f}/100 · "
            f"Scam {bd['scam']['raw']:.0f} · "
            f"Graph {bd['graph']['raw']:.0f} · "
            f"Geo {bd['geo']['raw']:.2f}"
        ),
        "location": ev.get("location") or {"lat": 28.6139, "lng": 77.2090, "name": "Delhi"},
        "entities": ev.get("entities", []),
        "score": round(crs, 1),
        # Bonus orchestrator fields (ignored by UI, useful for evidence panel)
        "crs_breakdown": bd,
        "incident_report_id": state["incident_report"].get("incident_id", ""),
        "report_path_json": state["report_path_json"],
        "report_path_pdf": state["report_path_pdf"],
        "graph_case_id": state["graph_case"].get("caseId", ""),
    }

    # ── Update in-memory feed ──────────────────────────────────────────────────
    orchestrator_feed.insert(0, feed_event)
    while len(orchestrator_feed) > MAX_FEED_EVENTS:
        orchestrator_feed.pop()

    # ── Audit log ──────────────────────────────────────────────────────────────
    audit_entry = {
        "timestamp": ts,
        "event_id": event_id,
        "action": state["action"],
        "severity": state["severity"],
        "crs": crs,
        "crs_breakdown": bd,
        "source_event_type": ev.get("type", "UNKNOWN"),
        "entities": ev.get("entities", []),
        "incident_id": state["incident_report"].get("incident_id", ""),
        "citizen_alert_sent": state["citizen_alert_sent"],
    }

    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_entry, default=str) + "\n")
    except Exception as e:
        print(f"[orchestrator] Audit log write failed: {e}")

    return {**state, "feed_event": feed_event, "audit_entry": audit_entry}


# ── Build LangGraph ────────────────────────────────────────────────────────────

def _build_graph():
    """Constructs and compiles the LangGraph state machine."""
    g = StateGraph(OrchState)

    # Add nodes
    g.add_node("ingest",       node_ingest)
    g.add_node("enrich_graph", node_enrich_graph)
    g.add_node("enrich_geo",   node_enrich_geo)
    g.add_node("score",        node_score)
    g.add_node("decide",       node_decide)
    g.add_node("escalate",     node_escalate)
    g.add_node("warn",         node_warn)
    g.add_node("info",         node_info)
    g.add_node("ignore",       node_ignore)
    g.add_node("emit_feed",    node_emit_feed)

    # Entry point
    g.set_entry_point("ingest")

    # Linear pipeline to decision
    g.add_edge("ingest",       "enrich_graph")
    g.add_edge("enrich_graph", "enrich_geo")
    g.add_edge("enrich_geo",   "score")
    g.add_edge("score",        "decide")

    # Conditional branch on decision
    g.add_conditional_edges(
        "decide",
        _route_decision,
        {
            "escalate": "escalate",
            "warn":     "warn",
            "info":     "info",
            "ignore":   "ignore",
        },
    )

    # All branches (except ignore) converge at emit_feed
    g.add_edge("escalate", "emit_feed")
    g.add_edge("warn",     "emit_feed")
    g.add_edge("info",     "emit_feed")
    g.add_edge("ignore",   END)         # ignored events don't appear in feed

    g.add_edge("emit_feed", END)

    return g.compile()


# Compile once at module load
_GRAPH = _build_graph()


# ── Public API ─────────────────────────────────────────────────────────────────

def process_event(raw_event: dict) -> dict:
    """
    Runs a raw event through the full orchestration pipeline.

    Args:
        raw_event: Dict with any combination of:
          type, entities, location, scam_score, timestamp,
          transcript, title, description, is_spoofed, ...

    Returns:
        Final OrchState dict with all enrichment + scoring + decision fields.
        Key fields: crs, severity, action, feed_event, incident_report,
                    report_path_json, report_path_pdf, crs_breakdown.
    """
    initial_state: OrchState = {
        "raw_event": raw_event,
        "scam_score": 0.0,
        "graph_case": {},
        "graph_anomaly_score": 0.0,
        "nearest_hotspot": {},
        "geo_density": 0.0,
        "recency_factor": 1.0,
        "crs": 0.0,
        "crs_breakdown": {},
        "action": "ignore",
        "severity": "low",
        "incident_report": {},
        "report_path_json": "",
        "report_path_pdf": "",
        "citizen_alert_sent": False,
        "feed_event": {},
        "audit_entry": {},
    }
    final = _GRAPH.invoke(initial_state)
    return final
