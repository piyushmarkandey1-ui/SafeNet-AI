"""
# ⚠️  SYNTHETIC DATA — Not derived from real incidents or persons.

SafeNet AI — Evidence Package Generator

Generates a structured JSON evidence package for one fraud ring.
Suitable for demo/presentation as a "court-admissible evidence" format
(DISCLAIMER: this is SYNTHETIC data only — not legally valid evidence).

Output: data/synthetic/evidence_package_SYNTHETIC.json

Usage:
    python -m backend.scripts.generate_evidence_package
    python scripts/generate_evidence_package.py [--entity-id <id>] [--hops 2]
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.fraud_graph.analysis import (
    detect_communities,
    score_mule_accounts,
    get_case_summary,
)

DISCLAIMER = (
    "⚠️  SYNTHETIC DATA — This evidence package was generated from artificially "
    "constructed data for demonstration purposes only. It does not represent real "
    "persons, financial institutions, or criminal incidents. It has NO legal validity "
    "and MUST NOT be used in actual legal proceedings."
)


def build_evidence_package(entity_id: str | None, hops: int) -> dict:
    """
    Builds a complete evidence package for a single fraud ring entity.

    If entity_id is None, picks the highest-scoring mule account automatically.

    Args:
        entity_id: Target node ID, or None for auto-selection.
        hops:      Graph traversal depth.

    Returns:
        Structured evidence package dict.
    """
    print("\n🔍  Detecting fraud-ring communities…")
    communities = detect_communities(min_size=3)
    print(f"   Found {len(communities)} communities (min_size=3)")
    for i, c in enumerate(communities[:3]):
        print(f"   [{i+1}] {c['cluster_id']}: {c['size']} nodes, risk={c['risk_score']}/100")

    print("\n🎯  Scoring mule accounts…")
    top_mules = score_mule_accounts(top_n=5)
    for m in top_mules[:3]:
        print(f"   {m['node_id'][:20]:20s}  score={m['mule_score']:5.1f}  "
              f"fan_in={m['fan_in']}  flagged={m['flagged_by_generator']}")

    # Pick target entity
    if entity_id is None:
        if top_mules:
            entity_id = top_mules[0]["node_id"]
            print(f"\n✅  Auto-selected highest-risk entity: {entity_id}")
        elif communities:
            entity_id = communities[0]["top_entities"][0]
            print(f"\n✅  Auto-selected top-cluster central node: {entity_id}")
        else:
            print("\n❌  No entities found. Ensure synthetic data exists.")
            sys.exit(1)

    print(f"\n📋  Building case summary for: {entity_id} (hops={hops})…")
    case = get_case_summary(entity_id, hops=hops)
    print(f"   Case ID: {case['caseId']}")
    print(f"   Risk Score: {case['riskScore']}/100 ({case['status']})")
    print(f"   Threat: {case['primaryThreat']}")
    print(f"   Connected nodes: {case['connected_nodes']}")
    print(f"   Evidence items: {len(case['evidenceItems'])}")
    print(f"   Linked entities: {len(case['linkedEntities'])}")

    # ── Assemble full package ─────────────────────────────────────────────────
    package = {
        "package_version": "1.0",
        "disclaimer": DISCLAIMER,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_classification": "SYNTHETIC — DEMO ONLY",

        "case_summary": {
            "case_id": case["caseId"],
            "status": case["status"],
            "primary_threat": case["primaryThreat"],
            "risk_score": case["riskScore"],
            "severity": case["severity"],
            "summary": case["summary"],
            "recommended_action": case["recommendedAction"],
        },

        "evidence": {
            "items": case["evidenceItems"],
            "linked_entities": case["linkedEntities"],
            "raw_edges": case["edges"],
            "hop_depth": case["hop_depth"],
            "connected_node_count": case["connected_nodes"],
            "entity_id": entity_id,
        },

        "ring_context": {
            "total_communities_detected": len(communities),
            "top_communities": [
                {
                    "cluster_id": c["cluster_id"],
                    "size": c["size"],
                    "risk_score": c["risk_score"],
                    "top_entities": c["top_entities"],
                    "node_types": c["node_types"],
                }
                for c in communities[:3]
            ],
            "top_mule_accounts": top_mules[:5],
        },

        "chain_of_custody": {
            "data_source": "SafeNet AI Synthetic Dataset",
            "source_files": [
                "data/synthetic/transactions_SYNTHETIC.csv",
                "data/synthetic/calls_SYNTHETIC.csv",
            ],
            "analysis_method": "NetworkX greedy_modularity_communities + mule fan-in scoring",
            "analyst": "SafeNet AI Automated System (v0.1.0)",
            "note": "All timestamps are synthetic and do not reflect real events.",
        },
    }

    return package


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="SafeNet — Evidence Package Generator")
    parser.add_argument("--entity-id", default=None, help="Target entity ID (auto if omitted)")
    parser.add_argument("--hops", type=int, default=2, help="Graph traversal depth")
    parser.add_argument("--output", default=None, help="Output JSON path")
    args = parser.parse_args()

    package = build_evidence_package(args.entity_id, args.hops)

    # Write output
    out_dir = Path(__file__).parent.parent.parent / "data" / "synthetic"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.output) if args.output else out_dir / "evidence_package_SYNTHETIC.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(package, f, indent=2, default=str)

    print(f"\n✅  Evidence package written to: {out_path}")
    print(f"   Total edges in package: {len(package['evidence']['raw_edges'])}")
    print(f"   Disclaimer: {DISCLAIMER[:80]}…")


if __name__ == "__main__":
    main()
