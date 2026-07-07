"""
# ⚠️  SYNTHETIC DATA — Not derived from real incidents or persons.

SafeNet AI — Orchestrator: Demo Scenario

Feeds a coordinated three-event sequence through the orchestrator,
showing the Compound Risk Score climb as correlated signals arrive:

  Step 1 — Scam Call (Module A)
           A spoofed call from a known-scam number with a CBI impersonation
           transcript.  CRS starts moderate (~35).

  Step 2 — Fraud Graph Cluster (Module C)
           The same phone number resolves to a money-mule ring in the graph.
           Graph anomaly score spikes.  CRS climbs to ~65.

  Step 3 — Geospatial Hotspot (Module D)
           A complaint cluster is reported at the same location, pushing the
           geospatial density signal high.  CRS crosses the ESCALATION_THRESHOLD
           and an incident report is auto-generated.

At the end, prints the full audit trail and incident report path.

Usage:
    python -m app.orchestrator.demo_scenario
    or imported and called as run_scenario() from the API's /simulate endpoint.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

DIVIDER = "═" * 64


def _print_step(step: int, title: str, result: dict) -> None:
    crs = result["crs"]
    action = result["action"]
    bd = result["crs_breakdown"]

    bar_filled = int(crs / 100 * 40)
    bar = "█" * bar_filled + "░" * (40 - bar_filled)

    print(f"\n{'─' * 64}")
    print(f"  STEP {step}: {title}")
    print(f"{'─' * 64}")
    print(f"  CRS  [{bar}] {crs:.1f}/100")
    print(f"  Action:   {action.upper()}")
    print(f"  Severity: {result['severity'].upper()}")
    print()
    print("  Score breakdown:")
    print(f"    Scam     {bd['scam']['raw']:5.1f} raw  × {bd['scam']['weight']:.2f}  = {bd['scam']['weighted']:5.2f} pts")
    print(f"    Graph    {bd['graph']['raw']:5.1f} raw  × {bd['graph']['weight']:.2f}  = {bd['graph']['weighted']:5.2f} pts")
    print(f"    Geo      {bd['geo']['raw']:5.2f} raw  × {bd['geo']['weight']:.2f}  = {bd['geo']['weighted']:5.2f} pts")
    print(f"    Recency  {bd['recency']['raw']:5.2f} raw  × {bd['recency']['weight']:.2f}  = {bd['recency']['weighted']:5.2f} pts")
    print(f"    ─────────────────────────────────────────")
    print(f"    TOTAL                              {crs:5.1f} / 100")
    if result.get("incident_id"):
        print(f"\n  📄 Incident Report generated: {result['incident_id']}")
    if result.get("report_path_json"):
        print(f"     JSON: {result['report_path_json']}")
    if result.get("report_path_pdf"):
        print(f"     PDF:  {result['report_path_pdf']}")


def run_scenario(delay_between_steps: float = 2.0) -> list[dict]:
    """
    Runs the three-step demo scenario.

    Args:
        delay_between_steps: Seconds to wait between events (for UI animation).
                             Set to 0 for instant (test mode).

    Returns:
        List of three result dicts from process_event().
    """
    from app.orchestrator.graph import process_event
    from app.fraud_graph.analysis import score_mule_accounts

    print(f"\n{DIVIDER}")
    print("  SafeNet AI — Orchestrator Demo Scenario")
    print(f"  ⚠️  SYNTHETIC DATA — not derived from real incidents")
    print(DIVIDER)

    now = datetime.now(timezone.utc)

    # ── Pick a real mule account from the graph for realism ───────────────────
    try:
        mules = score_mule_accounts(top_n=1)
        mule_account = mules[0]["node_id"] if mules else "DEMO-ACCOUNT-001"
    except Exception:
        mule_account = "DEMO-ACCOUNT-001"

    results: list[dict] = []

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 1: Scam Call detected (Module A signal only)
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n⏱  {now.strftime('%H:%M:%S')}  Ingesting SCAM CALL event…")
    step1_event = {
        "type": "SCAM_CALL",
        "timestamp": now.isoformat(),
        "title": "Scam Call Intercepted — CBI Impersonation",
        "description": "Spoofed call claiming arrest warrant, demanding immediate transfer.",
        "entities": ["+91-98001-DEMO", mule_account],
        "location": {"lat": 28.6139, "lng": 77.2090, "name": "Central Delhi"},
        "transcript": (
            "This is the CBI. There is an arrest warrant issued against you. "
            "Do not tell anyone. Stay on the line. "
            "You must transfer the penalty amount immediately to clear your name."
        ),
        "is_spoofed": True,
        "scam_score": 0,   # let the orchestrator score it from the transcript
    }
    r1 = process_event(step1_event)
    results.append(r1)
    _print_step(1, "Scam Call — Module A signal", {
        "crs": r1["crs"], "action": r1["action"], "severity": r1["severity"],
        "crs_breakdown": r1["crs_breakdown"],
        "incident_id": r1["incident_report"].get("incident_id", ""),
        "report_path_json": r1["report_path_json"],
        "report_path_pdf": r1["report_path_pdf"],
    })

    if delay_between_steps > 0:
        time.sleep(delay_between_steps)

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2: Same entity resolves to fraud graph cluster (Module C signal added)
    # ─────────────────────────────────────────────────────────────────────────
    now2 = datetime.now(timezone.utc)
    print(f"\n⏱  {now2.strftime('%H:%M:%S')}  Ingesting FRAUD GRAPH correlation…")
    step2_event = {
        "type": "FRAUD_NETWORK",
        "timestamp": now2.isoformat(),
        "title": "Fraud Ring Linked to Call Entity",
        "description": f"Mule account {mule_account[:20]}… resolved in active fraud ring.",
        "entities": [mule_account],
        "location": {"lat": 28.6139, "lng": 77.2090, "name": "Central Delhi"},
        "scam_score": r1["crs"],   # carry forward escalating score
    }
    r2 = process_event(step2_event)
    results.append(r2)
    _print_step(2, "Fraud Graph Cluster — Module C signal added", {
        "crs": r2["crs"], "action": r2["action"], "severity": r2["severity"],
        "crs_breakdown": r2["crs_breakdown"],
        "incident_id": r2["incident_report"].get("incident_id", ""),
        "report_path_json": r2["report_path_json"],
        "report_path_pdf": r2["report_path_pdf"],
    })

    if delay_between_steps > 0:
        time.sleep(delay_between_steps)

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 3: Geo hotspot complaint at same location — full escalation
    # ─────────────────────────────────────────────────────────────────────────
    now3 = datetime.now(timezone.utc)
    print(f"\n⏱  {now3.strftime('%H:%M:%S')}  Ingesting GEOSPATIAL HOTSPOT event…")
    step3_event = {
        "type": "SCAM_CALL",
        "timestamp": now3.isoformat(),
        "title": "⚡ COORDINATED ATTACK — All Signals Converged",
        "description": (
            "Scam call + fraud ring + geospatial hotspot all correlated at same entity and location."
        ),
        "entities": ["+91-98001-DEMO", mule_account],
        # Place event squarely inside the CRITICAL Delhi hotspot
        "location": {"lat": 28.717435, "lng": 77.120113, "name": "North Delhi — CRITICAL Zone"},
        "scam_score": max(r1["crs"], r2["crs"]),   # compound score carries forward
        "is_spoofed": True,
    }
    r3 = process_event(step3_event)
    results.append(r3)
    _print_step(3, "Geo Hotspot — ALL SIGNALS CONVERGED 🚨", {
        "crs": r3["crs"], "action": r3["action"], "severity": r3["severity"],
        "crs_breakdown": r3["crs_breakdown"],
        "incident_id": r3["incident_report"].get("incident_id", ""),
        "report_path_json": r3["report_path_json"],
        "report_path_pdf": r3["report_path_pdf"],
    })

    # ── Final summary ──────────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("  SCENARIO COMPLETE")
    print(DIVIDER)
    print(f"  Step 1 CRS:  {r1['crs']:5.1f}  ({r1['action']})")
    print(f"  Step 2 CRS:  {r2['crs']:5.1f}  ({r2['action']})")
    print(f"  Step 3 CRS:  {r3['crs']:5.1f}  ({r3['action']})")

    final_inc = r3["incident_report"]
    if final_inc.get("incident_id"):
        print(f"\n  📄 FINAL INCIDENT REPORT")
        print(f"     ID:       {final_inc['incident_id']}")
        print(f"     Severity: {final_inc['severity'].upper()}")
        print(f"     Threat:   {final_inc['graph_context']['primary_threat']}")
        print(f"     Action:   {str(final_inc['recommended_action'])[:80]}…")

    from app.orchestrator.settings import AUDIT_LOG_PATH
    print(f"\n  📋 Audit log: {AUDIT_LOG_PATH}")
    print(f"{DIVIDER}\n")

    return results


if __name__ == "__main__":
    run_scenario(delay_between_steps=1.0)
