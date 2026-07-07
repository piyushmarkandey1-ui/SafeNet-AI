"""
SafeNet AI — Fraud Graph Analysis

Provides three core capabilities:

1. Community detection  — clusters accounts/phones into fraud rings using
   NetworkX's greedy_modularity_communities (Louvain-like, no extra dep).

2. Mule anomaly scoring — fan-in (many senders → one receiver), tight time
   window, sub-threshold amounts → composite 0-100 score.

3. Case summary builder — get_case_summary(entity_id) walks up to N hops
   from any node and returns connected entities with edge metadata, shaped
   to match the Evidence Panel schema.

Module contract (safenet.md §3):
  - Plain Python functions are the source of truth.
  - FastAPI router wraps them without business logic.
"""

from __future__ import annotations

import os
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import networkx as nx
    _NX_AVAILABLE = True
except ImportError:
    _NX_AVAILABLE = False


# ── Path constants ─────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = _REPO_ROOT / "data" / "synthetic"
CALLS_CSV = DATA_DIR / "calls_SYNTHETIC.csv"
TRANSACTIONS_CSV = DATA_DIR / "transactions_SYNTHETIC.csv"

# ── Singleton graph ────────────────────────────────────────────────────────────
_graph_instance: Optional["FraudGraphWrapper"] = None


class FraudGraphWrapper:
    """
    Thin wrapper around the existing FraudGraph loader that adds analysis methods.

    Attributes:
        G: The underlying NetworkX MultiDiGraph.
        undirected: Cached undirected projection used for community detection.
    """

    def __init__(self) -> None:
        from app.fraud_graph.graph_loader import FraudGraph
        fg = FraudGraph()
        if CALLS_CSV.exists():
            fg.load_call_records(str(CALLS_CSV))
        else:
            print(f"[fraud_graph] Warning: {CALLS_CSV} not found — call edges skipped.")
        if TRANSACTIONS_CSV.exists():
            fg.load_transactions(str(TRANSACTIONS_CSV))
        else:
            print(f"[fraud_graph] Warning: {TRANSACTIONS_CSV} not found — tx edges skipped.")
        self.G: nx.MultiDiGraph = fg.G
        self._undirected: Optional[nx.Graph] = None

    @property
    def undirected(self) -> nx.Graph:
        """Lazy undirected projection (collapses multi-edges to single weight)."""
        if self._undirected is None:
            self._undirected = nx.Graph()
            for u, v, data in self.G.edges(data=True):
                if self._undirected.has_edge(u, v):
                    self._undirected[u][v]["weight"] += 1
                else:
                    self._undirected.add_edge(u, v, weight=1)
            for n, d in self.G.nodes(data=True):
                if n in self._undirected:
                    self._undirected.nodes[n].update(d)
        return self._undirected


def get_graph() -> FraudGraphWrapper:
    """Returns the lazily-loaded singleton FraudGraphWrapper."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = FraudGraphWrapper()
    return _graph_instance


# ── 1. Community Detection ─────────────────────────────────────────────────────

def detect_communities(min_size: int = 3) -> list[dict]:
    """
    Clusters the fraud graph into communities (fraud rings) using
    greedy_modularity_communities — a fast Louvain-style algorithm included
    in NetworkX with no extra dependencies.

    Args:
        min_size: Discard communities smaller than this (noise filtering).

    Returns:
        List of community dicts, sorted by size descending:
          {
            cluster_id     (str)   — deterministic "RING-<rank>-<size>" label,
            size           (int)   — number of nodes,
            nodes          (list)  — node IDs,
            node_types     (dict)  — type → count breakdown,
            edge_count     (int)   — internal edge count,
            risk_score     (float) — mean mule-anomaly score of member nodes,
            top_entities   (list)  — top-3 nodes by degree,
          }
    """
    wrapper = get_graph()
    # greedy_modularity_communities requires an undirected, connected-ish graph
    communities_raw = list(
        nx.community.greedy_modularity_communities(wrapper.undirected, weight="weight")
    )
    communities_raw.sort(key=len, reverse=True)

    results = []
    for rank, comm_set in enumerate(communities_raw):
        if len(comm_set) < min_size:
            continue

        nodes = list(comm_set)
        subgraph = wrapper.undirected.subgraph(nodes)

        node_types: dict[str, int] = defaultdict(int)
        for n in nodes:
            t = wrapper.G.nodes[n].get("type", "Unknown")
            node_types[t] += 1

        # Degree within the full graph (not just subgraph)
        degrees = [(n, wrapper.undirected.degree(n)) for n in nodes]
        degrees.sort(key=lambda x: x[1], reverse=True)

        # Compute a quick ring risk score: mean mule-anomaly for member accounts
        scores = [_mule_score_for_node(wrapper, n) for n in nodes
                  if wrapper.G.nodes[n].get("type") == "BankAccount"]
        ring_risk = round(sum(scores) / len(scores), 1) if scores else 0.0

        results.append({
            "cluster_id": f"RING-{rank + 1:02d}-{len(nodes)}",
            "size": len(nodes),
            "nodes": nodes,
            "node_types": dict(node_types),
            "edge_count": subgraph.number_of_edges(),
            "risk_score": ring_risk,
            "top_entities": [n for n, _ in degrees[:3]],
        })

    return results


# ── 2. Mule Anomaly Scoring ────────────────────────────────────────────────────

def _mule_score_for_node(wrapper: FraudGraphWrapper, node_id: str) -> float:
    """
    Computes a mule anomaly score (0-100) for a single BankAccount node.

    Signals:
      - Fan-in degree:  many distinct senders   → +score
      - Time window:    all credits in <2 hours → +score
      - Amount pattern: transactions in 40k-50k "structuring" band → +score
      - flagged_mule:   already labelled by generator → caps at 100

    Args:
        wrapper:  FraudGraphWrapper instance.
        node_id:  Node identifier string.

    Returns:
        Float score 0-100.
    """
    in_edges = list(wrapper.G.in_edges(node_id, data=True))
    if not in_edges:
        return 0.0

    tx_edges = [
        d for _, _, d in in_edges
        if d.get("edge_type") == "TRANSFERRED_TO"
    ]
    if not tx_edges:
        return 0.0

    # Already flagged?
    if any(d.get("flagged_mule") for d in tx_edges):
        return 100.0

    score = 0.0

    # Fan-in: 5+ senders is unusual
    fan_in = len(set(u for u, _, _ in in_edges))
    if fan_in >= 10:
        score += 40
    elif fan_in >= 5:
        score += 25
    elif fan_in >= 3:
        score += 10

    # Structuring band: amounts 40,000-50,000
    amounts = [d["amount"] for d in tx_edges if "amount" in d]
    if amounts:
        in_band = sum(1 for a in amounts if 40_000 <= float(a) <= 50_000)
        frac = in_band / len(amounts)
        score += frac * 35

    # Tight time window: all transactions within 2 hours
    timestamps = []
    for d in tx_edges:
        ts = d.get("timestamp")
        if ts:
            try:
                timestamps.append(datetime.fromisoformat(str(ts)))
            except ValueError:
                pass
    if len(timestamps) >= 2:
        timestamps.sort()
        span_hours = (timestamps[-1] - timestamps[0]).total_seconds() / 3600
        if span_hours < 2:
            score += 25
        elif span_hours < 6:
            score += 10

    return min(round(score, 1), 100.0)


def score_mule_accounts(top_n: int = 20) -> list[dict]:
    """
    Scores all BankAccount nodes and returns the top-N most suspicious.

    Args:
        top_n: Maximum results to return.

    Returns:
        List of dicts sorted by mule_score descending:
          { node_id, mule_score, fan_in, flagged_by_generator, in_degree }
    """
    wrapper = get_graph()
    results = []

    for node_id, data in wrapper.G.nodes(data=True):
        if data.get("type") != "BankAccount":
            continue
        score = _mule_score_for_node(wrapper, node_id)
        in_edges = list(wrapper.G.in_edges(node_id, data=True))
        tx_edges = [d for _, _, d in in_edges if d.get("edge_type") == "TRANSFERRED_TO"]
        results.append({
            "node_id": node_id,
            "mule_score": score,
            "fan_in": len(set(u for u, _, _ in in_edges)),
            "flagged_by_generator": any(d.get("flagged_mule") for d in tx_edges),
            "in_degree": wrapper.G.in_degree(node_id),
        })

    results.sort(key=lambda x: x["mule_score"], reverse=True)
    return results[:top_n]


# ── 3. Case Summary ────────────────────────────────────────────────────────────

def get_case_summary(entity_id: str, hops: int = 2) -> dict:
    """
    Builds a structured case evidence package for one entity.

    Walks up to `hops` in the graph (both directions) from entity_id,
    collecting all reachable nodes and the edges between them.
    Returns a dict shaped to match the EvidencePanel schema exactly.

    Args:
        entity_id: A node ID in the graph (account number, phone, device hash).
        hops:      Maximum graph distance to traverse.

    Returns:
        EvidencePanel-compatible dict:
          {
            caseId, status, riskScore, primaryThreat, summary,
            evidenceItems: [{type, snippet, confidence}],
            linkedEntities: [{id, type, risk}],
            recommendedAction,
            # bonus fields for the evidence JSON export
            entity_id, hop_depth, connected_nodes, edges, generated_at,
          }

    Raises:
        KeyError: If entity_id is not present in the graph.
    """
    wrapper = get_graph()

    if entity_id not in wrapper.G:
        # Fuzzy fallback: partial match
        candidates = [n for n in wrapper.G.nodes if str(entity_id) in str(n)]
        if not candidates:
            raise KeyError(f"Entity '{entity_id}' not found in fraud graph.")
        entity_id = candidates[0]

    # BFS up to `hops` in the undirected projection
    reachable: set[str] = set()
    frontier = {entity_id}
    for _ in range(hops):
        next_frontier: set[str] = set()
        for n in frontier:
            for nbr in wrapper.undirected.neighbors(n):
                if nbr not in reachable and nbr != entity_id:
                    next_frontier.add(nbr)
        reachable.update(frontier)
        frontier = next_frontier - reachable
    reachable.update(frontier)

    subgraph = wrapper.G.subgraph(reachable)

    # ── Collect edge metadata ─────────────────────────────────────────────────
    edges_raw: list[dict] = []
    for u, v, data in subgraph.edges(data=True):
        edges_raw.append({
            "from": u,
            "to": v,
            "edge_type": data.get("edge_type", "UNKNOWN"),
            "timestamp": str(data.get("timestamp", "")),
            "amount": data.get("amount"),
            "is_spoofed": data.get("is_spoofed"),
            "flagged_mule": data.get("flagged_mule"),
            "duration_sec": data.get("duration_sec"),
            "transcript_snippet": data.get("transcript_snippet"),
        })

    # ── Risk scoring ──────────────────────────────────────────────────────────
    node_scores = {
        n: _mule_score_for_node(wrapper, n)
        for n in reachable
        if wrapper.G.nodes[n].get("type") == "BankAccount"
    }
    center_score = node_scores.get(entity_id, 0.0)

    # Also boost score if any connected call is spoofed
    spoofed_calls = sum(
        1 for e in edges_raw
        if e.get("is_spoofed") is True
    )
    flagged_txns = sum(1 for e in edges_raw if e.get("flagged_mule") is True)

    compound_score = min(
        center_score
        + spoofed_calls * 5
        + flagged_txns * 8,
        100.0,
    )
    compound_score = round(compound_score, 1)

    # ── Severity mapping ──────────────────────────────────────────────────────
    if compound_score >= 85:
        severity = "critical"
        status = "OPEN_INVESTIGATION"
    elif compound_score >= 60:
        severity = "high"
        status = "OPEN_INVESTIGATION"
    elif compound_score >= 30:
        severity = "medium"
        status = "PENDING_REVIEW"
    else:
        severity = "low"
        status = "MONITORING"

    # ── Evidence items ────────────────────────────────────────────────────────
    evidence_items: list[dict] = []

    # Transaction evidence
    tx_edges = [e for e in edges_raw if e["edge_type"] == "TRANSFERRED_TO"]
    if tx_edges:
        amounts = [e["amount"] for e in tx_edges if e.get("amount") is not None]
        flagged = [e for e in tx_edges if e.get("flagged_mule")]
        snippet = (
            f"{len(tx_edges)} transaction(s) linked. "
            f"{len(flagged)} flagged as mule activity. "
            f"Amounts range ₹{min(amounts):,.0f}–₹{max(amounts):,.0f}."
            if amounts else f"{len(tx_edges)} transaction(s) linked."
        )
        evidence_items.append({
            "type": "TRANSACTION_GRAPH",
            "snippet": snippet,
            "confidence": min(0.65 + 0.05 * len(flagged), 0.99),
        })

    # Call/transcript evidence
    call_edges = [e for e in edges_raw if e["edge_type"] == "CALLED"]
    spoofed_snippets = [
        e["transcript_snippet"] for e in call_edges
        if e.get("is_spoofed") and e.get("transcript_snippet")
    ]
    if call_edges:
        snippet_text = (
            f'"{spoofed_snippets[0][:120]}…"'
            if spoofed_snippets
            else f"{len(call_edges)} call(s) traversed — no spoofed calls detected."
        )
        evidence_items.append({
            "type": "AUDIO_TRANSCRIPT",
            "snippet": snippet_text,
            "confidence": 0.92 if spoofed_snippets else 0.55,
        })

    # Shared-device evidence
    device_edges = [e for e in edges_raw if e["edge_type"] == "SHARED_DEVICE"]
    if device_edges:
        devices = list({e["to"] for e in device_edges})
        evidence_items.append({
            "type": "NETWORK_NODE",
            "snippet": (
                f"{len(devices)} shared device hash(es) link accounts in this ring: "
                f"{', '.join(devices[:2])}{'…' if len(devices) > 2 else ''}."
            ),
            "confidence": 0.88,
        })

    # ── Linked entities ───────────────────────────────────────────────────────
    linked: list[dict] = []
    for n in reachable:
        n_type = wrapper.G.nodes[n].get("type", "Unknown")
        n_score = node_scores.get(n, 0.0)
        if n_score >= 85 or (n == entity_id and flagged_txns > 0):
            risk = "critical"
        elif n_score >= 50:
            risk = "high"
        else:
            risk = "safe"
        linked.append({"id": n, "type": n_type, "risk": risk})

    # Sort: high-risk first, then by node ID
    linked.sort(key=lambda x: ({"critical": 0, "high": 1, "safe": 2}.get(x["risk"], 3), x["id"]))

    # ── Determine primary threat ──────────────────────────────────────────────
    if flagged_txns > 0 and spoofed_calls > 0:
        primary_threat = "Coordinated Fraud Ring (Calls + Transactions)"
    elif flagged_txns > 0:
        primary_threat = "Money Mule Network"
    elif spoofed_calls > 0:
        primary_threat = "Vishing / Spoofed Call Campaign"
    else:
        primary_threat = "Suspicious Activity Cluster"

    # ── Recommended action ────────────────────────────────────────────────────
    if severity == "critical":
        rec = (
            f"Freeze accounts in cluster and file SAR. "
            f"{len(reachable)} entities connected within {hops} hops of {entity_id}."
        )
    elif severity == "high":
        rec = (
            f"Flag accounts for enhanced due diligence. "
            f"Review {len(tx_edges)} transactions and {len(call_edges)} call records."
        )
    else:
        rec = f"Continue monitoring. No immediate action required."

    # ── Summary ───────────────────────────────────────────────────────────────
    summary = (
        f"Entity {entity_id} is connected to {len(reachable) - 1} other node(s) "
        f"within {hops} graph hops. "
        f"Detected {flagged_txns} flagged transaction(s) and {spoofed_calls} spoofed "
        f"call(s) in the subgraph. "
        f"Compound risk score: {compound_score}/100 ({severity.upper()})."
    )

    return {
        # ── EvidencePanel-required fields ─────────────────────────────────────
        "caseId": f"CASE-FG-{abs(hash(entity_id)) % 100000:05d}",
        "status": status,
        "riskScore": compound_score,
        "primaryThreat": primary_threat,
        "summary": summary,
        "evidenceItems": evidence_items or [{
            "type": "NETWORK_NODE",
            "snippet": f"Entity {entity_id} found in graph with {len(reachable)} connected nodes.",
            "confidence": 0.5,
        }],
        "linkedEntities": linked[:20],   # cap for UI
        "recommendedAction": rec,
        # ── Bonus fields for evidence package export ──────────────────────────
        "entity_id": entity_id,
        "hop_depth": hops,
        "connected_nodes": len(reachable),
        "edges": edges_raw,
        "severity": severity,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
