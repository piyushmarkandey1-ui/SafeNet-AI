"""
# ⚠️  SYNTHETIC DATA — Not derived from real incidents or persons.

SafeNet AI — RAG Query Verification

Builds the ChromaDB index and runs two natural-language queries.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    print("\n" + "=" * 60)
    print("  SafeNet AI — RAG Query Verification")
    print("=" * 60)

    print("\n📚  Building ChromaDB index (embedding clusters + cases)…")
    from app.fraud_graph.rag_query import build_index, query_fraud_graph
    n = build_index(force=True)
    print(f"  ✅  Index ready: {n} document(s) embedded\n")

    queries = [
        "show accounts with high fan-in suspicious transfers in the last 30 days",
        "which fraud rings have the highest mule network activity and what accounts are at the center?",
    ]

    for q in queries:
        print("─" * 60)
        print(f"  QUERY: {q}")
        print("─" * 60)
        result = query_fraud_graph(q, top_k=3)
        print(result["answer"])
        print(f"\n  [Retrieved {result['retrieved_docs']} doc(s) | LLM: {result['llm_used']}]")
        print()

    print("=" * 60)
    print("  ✅  RAG query verification complete.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
