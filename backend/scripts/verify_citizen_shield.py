"""
# ⚠️  SYNTHETIC DATA — Not derived from real incidents or persons.

SafeNet AI — Citizen Shield: Verification Script

Runs 3 example conversations (clear scam, ambiguous, general question)
in both English and Hindi (template fallback when no LLM key set).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.citizen_shield.agent import ask
from app.citizen_shield.knowledge_base import build_kb

DIVIDER = "─" * 62


def show_response(label: str, query: str, language: str = "en") -> None:
    print(f"\n{DIVIDER}")
    print(f"  [{label}]  lang={language}")
    print(f"  Q: {query}")
    print(DIVIDER)
    resp = ask(query, language=language)
    print(f"  Intent    : {resp['intent']}")
    print(f"  Risk Level: {resp['risk_level']}")
    print(f"  Actionable: {resp['isActionable']}")
    print()
    for line in resp["text"].split("\n"):
        print(f"  {line}")


def main() -> None:
    print("\n" + "=" * 62)
    print("  SafeNet AI — Citizen Shield Verification")
    print("=" * 62)

    print("\n📚  Building knowledge base…")
    n = build_kb()
    print(f"  KB ready: {n} documents")

    # ── Conversation 1: Clear scam (suspicious_call) ───────────────────────
    print("\n\n══════ CONVERSATION 1: CLEAR SCAM CALL ══════")
    show_response(
        "CLEAR SCAM · English",
        "Someone called me claiming to be from CBI. "
        "They said there is an arrest warrant and I must not tell anyone. "
        "They want me to transfer money immediately to clear my name.",
        language="en",
    )
    show_response(
        "CLEAR SCAM · Hindi",
        "Someone called me claiming to be from CBI. "
        "They said there is an arrest warrant and I must not tell anyone. "
        "They want me to transfer money immediately to clear my name.",
        language="hi",
    )

    # ── Conversation 2: Ambiguous (upi_fraud_check) ────────────────────────
    print("\n\n══════ CONVERSATION 2: AMBIGUOUS UPI QUERY ══════")
    show_response(
        "AMBIGUOUS · English",
        "I got a notification on PhonePe asking me to enter my UPI PIN "
        "to receive a refund of ₹5000. Is this safe?",
        language="en",
    )
    show_response(
        "AMBIGUOUS · Hindi",
        "I got a notification on PhonePe asking me to enter my UPI PIN "
        "to receive a refund of ₹5000. Is this safe?",
        language="hi",
    )

    # ── Conversation 3: General question ──────────────────────────────────
    print("\n\n══════ CONVERSATION 3: GENERAL QUESTION ══════")
    show_response(
        "GENERAL · English",
        "How do I report a cyber fraud in India?",
        language="en",
    )
    show_response(
        "GENERAL · Hindi",
        "How do I report a cyber fraud in India?",
        language="hi",
    )

    print("\n\n" + "=" * 62)
    print("  ✅  Citizen Shield verification complete.")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    main()
