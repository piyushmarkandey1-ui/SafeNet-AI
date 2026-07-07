"""
SafeNet AI — Fraud Graph RAG Query Layer

Embeds fraud-ring cluster descriptions into ChromaDB using a local
sentence-transformers model (all-MiniLM-L6-v2, ~80 MB — no API key needed).

Supports natural-language queries ("show accounts linked to this number in
30 days") answered by:
  1. Semantic retrieval  — top-K cluster/case chunks from ChromaDB.
  2. LLM synthesis       — optional: if GEMINI_API_KEY is set,
                           passes retrieved context to Gemini
                           for a polished narrative. Falls back to a structured
                           template-based response when no key is present.

The response always includes citations: specific node/edge references sourced
from the retrieved chunks so the output reads like an evidence report.

Usage (standalone):
    python -m app.fraud_graph.rag_query

Module contract (safenet.md §3):
    query_fraud_graph(query_text) is the plain Python function.
    The /graph/query POST endpoint is a thin wrapper.
"""

from __future__ import annotations

import json
import os
import re
import textwrap
import warnings
from datetime import datetime, timezone
from typing import Optional

# Suppress noisy tokenizer parallelism warning from HuggingFace
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# ── Lazy singletons ────────────────────────────────────────────────────────────
_chroma_client = None
_collection = None
_embedder = None
_index_built = False

COLLECTION_NAME = "fraud_graph_clusters"
EMBED_MODEL = "all-MiniLM-L6-v2"   # small, fast, good retrieval quality


def _get_embedder():
    """Lazy-loads the SentenceTransformer embedding model."""
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer(EMBED_MODEL)
        except Exception as e:
            raise RuntimeError(
                f"sentence-transformers required for RAG. "
                f"Install: pip install sentence-transformers\n{e}"
            )
    return _embedder


def _get_collection():
    """Lazy-loads (or creates) the ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is None:
        import chromadb
        _chroma_client = chromadb.EphemeralClient()
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


# ── Index building ─────────────────────────────────────────────────────────────

def build_index(force: bool = False) -> int:
    """
    Embeds all fraud-ring cluster descriptions and loads them into ChromaDB.

    Each document is a rich textual description of one cluster, including
    node types, counts, top entities, and risk score. Also adds individual
    case summaries for any entity with a mule score ≥ 80.

    Args:
        force: Rebuild even if the index already exists.

    Returns:
        Total number of documents indexed.
    """
    global _index_built
    collection = _get_collection()

    if _index_built and not force:
        return collection.count()

    from app.fraud_graph.analysis import detect_communities, score_mule_accounts, get_case_summary

    docs: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    # 1. Cluster documents
    communities = detect_communities(min_size=2)
    for c in communities:
        node_type_str = ", ".join(f"{v} {k}" for k, v in c["node_types"].items())
        top_str = ", ".join(str(e) for e in c["top_entities"])
        text = (
            f"Fraud ring cluster {c['cluster_id']} contains {c['size']} entities "
            f"({node_type_str}). "
            f"Internal edge count: {c['edge_count']}. "
            f"Ring risk score: {c['risk_score']}/100. "
            f"Top connected entities: {top_str}. "
            f"Nodes in cluster: {', '.join(str(n) for n in c['nodes'][:10])}"
            f"{'…' if len(c['nodes']) > 10 else ''}."
        )
        docs.append(text)
        metadatas.append({
            "doc_type": "cluster",
            "cluster_id": c["cluster_id"],
            "risk_score": c["risk_score"],
            "size": c["size"],
            "top_entities": json.dumps(c["top_entities"]),
        })
        ids.append(f"cluster-{c['cluster_id']}")

    # 2. High-risk mule account case summaries
    top_mules = score_mule_accounts(top_n=15)
    for m in top_mules:
        if m["mule_score"] < 60:
            break
        try:
            case = get_case_summary(m["node_id"], hops=1)
        except KeyError:
            continue
        text = (
            f"Case {case['caseId']} — entity {m['node_id']} "
            f"(mule score {m['mule_score']}/100, fan-in {m['fan_in']}). "
            f"Primary threat: {case['primaryThreat']}. "
            f"Summary: {case['summary']} "
            f"Recommended action: {case['recommendedAction']}"
        )
        docs.append(text)
        metadatas.append({
            "doc_type": "case",
            "entity_id": m["node_id"],
            "mule_score": m["mule_score"],
            "case_id": case["caseId"],
        })
        ids.append(f"case-{m['node_id'][:32]}")

    if not docs:
        _index_built = True
        return 0

    # Embed and upsert
    embedder = _get_embedder()
    embeddings = embedder.encode(docs, show_progress_bar=False).tolist()

    collection.upsert(
        ids=ids,
        documents=docs,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    _index_built = True
    return len(docs)


# ── Query ──────────────────────────────────────────────────────────────────────

def query_fraud_graph(
    query_text: str,
    top_k: int = 4,
) -> dict:
    """
    Answers a natural-language query about the fraud graph using RAG.

    Args:
        query_text: Free-text question, e.g.
                    "show accounts linked to this number in 30 days"
                    "which rings have the highest mule activity?"
        top_k:      Number of evidence chunks to retrieve.

    Returns:
        dict:
          {
            query          (str)   — original query,
            answer         (str)   — narrative response (LLM or template),
            citations      (list)  — [{doc_id, text_snippet, metadata}],
            retrieved_docs (int)   — number of chunks retrieved,
            llm_used       (bool)  — whether an LLM was called,
            generated_at   (str)   — ISO timestamp,
          }
    """
    # Ensure index is populated
    build_index()

    collection = _get_collection()
    embedder = _get_embedder()

    # Embed the query
    q_embedding = embedder.encode([query_text], show_progress_bar=False).tolist()[0]

    # Retrieve top-K
    results = collection.query(
        query_embeddings=[q_embedding],
        n_results=min(top_k, max(collection.count(), 1)),
        include=["documents", "metadatas", "distances"],
    )

    retrieved_docs: list[str] = results["documents"][0] if results["documents"] else []
    retrieved_meta: list[dict] = results["metadatas"][0] if results["metadatas"] else []
    distances: list[float] = results["distances"][0] if results["distances"] else []

    citations = []
    for i, (doc, meta, dist) in enumerate(zip(retrieved_docs, retrieved_meta, distances)):
        citations.append({
            "doc_id": f"chunk-{i + 1}",
            "text_snippet": doc[:200] + ("…" if len(doc) > 200 else ""),
            "metadata": meta,
            "similarity": round(1 - dist, 4),
        })

    # ── Gemini synthesis (optional) ───────────────────────────────────────────────
    gemini_used = False
    gemini_key = os.getenv("GEMINI_API_KEY")

    if gemini_key and retrieved_docs:
        try:
            answer = _gemini_synthesise(query_text, retrieved_docs, citations, gemini_key)
            gemini_used = True
        except Exception as e:
            warnings.warn(f"Gemini synthesis failed ({e}). Using template response.")
            answer = _template_response(query_text, citations)
    else:
        answer = _template_response(query_text, citations)

    return {
        "query": query_text,
        "answer": answer,
        "citations": citations,
        "retrieved_docs": len(retrieved_docs),
        "llm_used": gemini_used,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _gemini_synthesise(
    query_text: str,
    retrieved_docs: list[str],
    citations: list[dict],
    api_key: str,
) -> str:
    """
    Calls Gemini to synthesise a narrative evidence report from retrieved fraud graph chunks.

    Args:
        query_text:     Original query.
        retrieved_docs: Top-K raw text chunks from ChromaDB.
        citations:      Citation metadata list.
        api_key:        Gemini API key.

    Returns:
        Gemini-generated evidence narrative string.
    """
    import textwrap
    from google import genai
    from google.genai import types as genai_types

    client = genai.Client(api_key=api_key)

    context = "\n\n".join(
        f"[Source {i + 1}]\n{doc}" for i, doc in enumerate(retrieved_docs)
    )
    citation_list = "\n".join(
        f"[{i + 1}] {c['metadata'].get('cluster_id') or c['metadata'].get('case_id', 'N/A')}"
        for i, c in enumerate(citations)
    )

    system_prompt = textwrap.dedent("""
        You are a financial crime analyst writing structured evidence reports for law enforcement.
        Use only the provided source documents. Cite sources as [1], [2], etc.
        Format your response as:
          FINDINGS: 2-3 sentences summarising what the graph shows.
          KEY ENTITIES: Bullet list of the most suspicious nodes with their risk scores.
          RECOMMENDED ACTION: One concrete next step.
        Be factual and concise. This is SYNTHETIC data for a demo system.
    """).strip()

    prompt = (
        f"{system_prompt}\n\n"
        f"Query: {query_text}\n\n"
        f"Source documents:\n{context}\n\n"
        f"Citation index:\n{citation_list}"
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=600,
        ),
    )
    return response.text.strip()


def _template_response(query_text: str, citations: list[dict]) -> str:
    """
    Generates a structured evidence-report style response without an LLM.

    Args:
        query_text: Original query string.
        citations:  Retrieved evidence chunks with metadata.

    Returns:
        Multi-line string formatted as an investigator's evidence report.
    """
    if not citations:
        return (
            "No relevant evidence found in the fraud graph for this query. "
            "The graph may not contain entities matching the described pattern. "
            "Consider broadening the search or loading additional data."
        )

    # Extract key facts from citations
    cluster_refs = [c for c in citations if c["metadata"].get("doc_type") == "cluster"]
    case_refs = [c for c in citations if c["metadata"].get("doc_type") == "case"]

    lines = [
        f"EVIDENCE REPORT — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Query: {query_text}",
        "",
        "FINDINGS",
        "─" * 48,
    ]

    if cluster_refs:
        for cr in cluster_refs:
            cid = cr["metadata"].get("cluster_id", "N/A")
            risk = cr["metadata"].get("risk_score", 0)
            size = cr["metadata"].get("size", 0)
            top = json.loads(cr["metadata"].get("top_entities", "[]"))
            lines.append(
                f"• Cluster {cid}: {size} entities, ring risk {risk}/100. "
                f"Central nodes: {', '.join(top[:2]) or 'N/A'}."
            )

    if case_refs:
        for cr in case_refs:
            eid = cr["metadata"].get("entity_id", "N/A")
            ms = cr["metadata"].get("mule_score", 0)
            cid = cr["metadata"].get("case_id", "N/A")
            lines.append(
                f"• Case {cid}: Entity {eid} has mule score {ms}/100. "
                f"High fan-in and sub-threshold transaction pattern detected."
            )

    lines += [
        "",
        "CITATIONS",
        "─" * 48,
    ]
    for i, c in enumerate(citations, 1):
        lines.append(f"[{i}] (sim={c['similarity']:.3f}) {c['text_snippet']}")

    lines += [
        "",
        "NOTE: This report is generated from synthetic data for demonstration "
        "purposes. No real persons or financial institutions are implicated.",
    ]

    return "\n".join(lines)


def _llm_synthesise(
    query_text: str,
    retrieved_docs: list[str],
    citations: list[dict],
    api_key: str,
) -> str:
    """
    Calls OpenAI (or compatible) to synthesise a narrative evidence report.

    Args:
        query_text:     Original query.
        retrieved_docs: Top-K raw text chunks.
        citations:      Citation metadata list.
        api_key:        LLM API key.

    Returns:
        LLM-generated evidence narrative string.
    """
    from openai import OpenAI

    context = "\n\n".join(
        f"[Source {i + 1}]\n{doc}" for i, doc in enumerate(retrieved_docs)
    )
    citation_list = "\n".join(
        f"[{i + 1}] {c['metadata'].get('cluster_id') or c['metadata'].get('case_id', 'N/A')}"
        for i, c in enumerate(citations)
    )

    system_prompt = textwrap.dedent("""
        You are a financial crime analyst writing structured evidence reports for law enforcement.
        Use only the provided source documents. Cite sources as [1], [2], etc.
        Format your response as:
          FINDINGS: 2-3 sentences summarising what the graph shows.
          KEY ENTITIES: Bullet list of the most suspicious nodes with their risk scores.
          RECOMMENDED ACTION: One concrete next step.
        Be factual and concise. This is SYNTHETIC data for a demo system.
    """).strip()

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": (
                f"Query: {query_text}\n\n"
                f"Source documents:\n{context}\n\n"
                f"Citation index:\n{citation_list}"
            )},
        ],
        max_tokens=600,
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


# ── CLI demo ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
        "show accounts with high fan-in suspicious transfers in the last 30 days"

    print("Building index…")
    n = build_index()
    print(f"Index ready: {n} documents\n")

    print(f"Query: {query}\n")
    result = query_fraud_graph(query)

    print("=" * 60)
    print(result["answer"])
    print("=" * 60)
    print(f"\nRetrieved {result['retrieved_docs']} doc(s)  |  LLM used: {result['llm_used']}")
