"""
SafeNet AI — Fraud Graph: FastAPI Router

Exposes:
  GET  /graph/case/{entity_id}   — case summary for any graph entity
  GET  /graph/clusters           — all detected fraud-ring communities
  GET  /graph/mules              — top mule-account anomaly scores
  POST /graph/query              — natural-language RAG query

Module contract (safenet.md §3):
  All route handlers are thin wrappers around analysis.py and rag_query.py.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from app.fraud_graph.analysis import (
    get_case_summary,
    detect_communities,
    score_mule_accounts,
)

router = APIRouter(prefix="/graph", tags=["Fraud Graph"])


# ── Request / Response schemas ─────────────────────────────────────────────────

class NLQueryRequest(BaseModel):
    """Body for POST /graph/query."""
    model_config = ConfigDict(populate_by_name=True)
    query: str
    top_k: int = 4


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get(
    "/case/{entity_id}",
    summary="Get case evidence for a graph entity",
)
async def get_case(
    entity_id: str,
    hops: int = Query(default=2, ge=1, le=4, description="Graph traversal depth"),
):
    """
    Returns a full evidence package for the given entity.

    The response shape matches the EvidencePanel schema exactly:
      caseId, status, riskScore, primaryThreat, summary,
      evidenceItems, linkedEntities, recommendedAction.

    Additional bonus fields (edges, generated_at, etc.) are included but
    ignored by the frontend component — no component changes needed.

    Args:
        entity_id: Any node ID in the fraud graph (account, phone, device).
        hops:      How many hops to walk from the entity (1-4).

    Returns:
        Evidence package dict.

    Raises:
        404: If entity_id is not found in the graph.
    """
    try:
        return get_case_summary(entity_id, hops=hops)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/clusters",
    summary="Detect fraud-ring communities in the graph",
)
async def get_clusters(
    min_size: int = Query(default=3, ge=2, description="Minimum cluster size"),
):
    """
    Runs community detection (greedy_modularity_communities) and returns
    all clusters larger than min_size, sorted by size descending.

    Args:
        min_size: Smallest cluster to include (noise filter).

    Returns:
        List of cluster dicts.
    """
    return detect_communities(min_size=min_size)


@router.get(
    "/mules",
    summary="Top mule-account anomaly scores",
)
async def get_mules(
    top_n: int = Query(default=20, ge=1, le=100),
):
    """
    Returns the top-N bank accounts ranked by mule anomaly score.

    Scoring signals: fan-in degree, sub-threshold amount structuring,
    tight transaction time window.

    Args:
        top_n: Maximum results.

    Returns:
        List of mule score dicts.
    """
    return score_mule_accounts(top_n=top_n)


@router.post(
    "/query",
    summary="Natural-language RAG query over the fraud graph",
)
async def nl_query(body: NLQueryRequest):
    """
    Answers a free-text question about the fraud graph using retrieval-
    augmented generation (ChromaDB + sentence-transformers + optional LLM).

    Args:
        body.query: Natural-language question.
        body.top_k: How many evidence chunks to retrieve.

    Returns:
        RAG response dict with answer, citations, and metadata.
    """
    from app.fraud_graph.rag_query import query_fraud_graph
    return query_fraud_graph(body.query, top_k=body.top_k)
