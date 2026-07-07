"""
# ⚠️  SYNTHETIC DATA — Not derived from real incidents or persons.

SafeNet AI — Fraud Graph: Verification Script

Runs community detection, mule scoring, and a case summary.
Used for the Prompt 6 verification step.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.fraud_graph.analysis import (
    detect_communities,
    score_mule_accounts,
    get_case_summary,
)

def run_verification():
    print("\n" + "=" * 60)
    print("  SafeNet AI — Fraud Graph Verification")
    print("=" * 60)

    # ── 1. Community detection ─────────────────────────────────────────────
    print("\n📊  COMMUNITY DETECTION (greedy_modularity_communities)")
    print("-" * 60)
    communities = detect_communities(min_size=3)
    print(f"  Total clusters (min_size=3): {len(communities)}")
    for i, c in enumerate(communities[:2]):
        print(f"\n  Cluster #{i+1}: {c['cluster_id']}")
        print(f"    Size:         {c['size']} nodes")
        print(f"    Node types:   {c['node_types']}")
        print(f"    Edge count:   {c['edge_count']}")
        print(f"    Ring risk:    {c['risk_score']}/100")
        print(f"    Top entities: {c['top_entities']}")

    # ── 2. Mule scoring ────────────────────────────────────────────────────
    print("\n\n🎯  MULE ACCOUNT ANOMALY SCORES (top 5)")
    print("-" * 60)
    mules = score_mule_accounts(top_n=5)
    for m in mules:
        flag = " ⚠ FLAGGED" if m["flagged_by_generator"] else ""
        print(f"  {m['node_id'][:28]:28s}  score={m['mule_score']:5.1f}  "
              f"fan_in={m['fan_in']:3d}  in_deg={m['in_degree']:3d}{flag}")

    # ── 3. Case summary ────────────────────────────────────────────────────
    target = mules[0]["node_id"] if mules else (communities[0]["top_entities"][0] if communities else None)
    if not target:
        print("\n❌  No entities available for case summary.")
        return

    print(f"\n\n📋  CASE SUMMARY for: {target}")
    print("-" * 60)
    case = get_case_summary(target, hops=2)
    print(f"  Case ID:        {case['caseId']}")
    print(f"  Status:         {case['status']}")
    print(f"  Risk Score:     {case['riskScore']}/100")
    print(f"  Severity:       {case['severity'].upper()}")
    print(f"  Primary Threat: {case['primaryThreat']}")
    print(f"  Summary:        {case['summary'][:100]}…")
    print(f"  Evidence items: {len(case['evidenceItems'])}")
    for ev in case["evidenceItems"]:
        print(f"    [{ev['type']}] conf={ev['confidence']:.2f}  {ev['snippet'][:70]}…")
    print(f"  Linked entities ({len(case['linkedEntities'])}):")
    for ent in case["linkedEntities"][:5]:
        print(f"    {ent['id'][:28]:28s}  type={ent['type']:12s}  risk={ent['risk']}")
    print(f"  Action:         {case['recommendedAction'][:80]}…")
    print(f"  Generated at:   {case['generated_at']}")

    print("\n" + "=" * 60)
    print("  ✅  Verification complete.")
    print("=" * 60 + "\n")

    return target


if __name__ == "__main__":
    run_verification()
