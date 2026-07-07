"""
SafeNet AI — Citizen Shield: Conversational Agent

Entry point: ask(query, language) → AgentResponse

Pipeline:
  1. Intent classification  — keyword + embedding routing to one of four intents:
       suspicious_call | upi_fraud_check | counterfeit_note_query | general_question
  2. Intent handler         — calls Module A/C functions directly (no HTTP hop)
       and queries the knowledge base for supporting context.
  3. Response composition   — structured {risk_level, explanation, next_steps}
       assembled into a chat-friendly string.
  4. Translation (optional) — if language != "en" and LLM_API_KEY is set, the
       English response is translated by the LLM. Falls back to English + note.
       Adding a new language is a single dict entry in SUPPORTED_LANGUAGES.

Module contract (safenet.md §3):
  ask(query, language) is the plain Python function.
  POST /ask is a thin wrapper.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Literal

# ── Supported languages ────────────────────────────────────────────────────────
# Extend by adding entries here — no code changes elsewhere.
SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
}

IntentType = Literal[
    "suspicious_call",
    "upi_fraud_check",
    "counterfeit_note_query",
    "general_question",
]

# ── Intent keyword signatures ──────────────────────────────────────────────────
# Each entry: (intent, [trigger_words/phrases]).
# Checked in order — first match wins.  Kept simple and auditable.
# UPI/transaction keywords checked BEFORE suspicious_call so "enter UPI PIN"
# routes to upi_fraud_check, not suspicious_call.
_INTENT_RULES: list[tuple[IntentType, list[str]]] = [
    ("counterfeit_note_query", [
        "fake note", "counterfeit", "fake currency", "fake rupee", "forged note",
        "note is fake", "currency note", "500 note", "2000 note", "old note",
        "suspicious note", "check note",
    ]),
    ("upi_fraud_check", [
        "upi", "gpay", "google pay", "phonepe", "paytm", "qr code", "qr",
        "collect request", "receive money",
        "bank transfer", "neft", "imps", "money transferred", "deducted",
        "account debited", "transaction", "paisa gaya", "paise", "rupee sent",
        "enter my upi", "enter upi pin", "upi pin", "scan and pay",
    ]),
    ("suspicious_call", [
        "call", "called me", "phone", "caller", "rang", "said they are", "arrest",
        "warrant", "cbi", "police", "customs", "irs", "microsoft", "anydesk",
        "teamviewer", "stay on the line", "don't tell", "do not tell", "spoofed",
        "threatening", "threatening me", "claiming to be",
    ]),
]


def _classify_intent(text: str) -> IntentType:
    """
    Classifies a user query into one of four intents via keyword matching.

    Falls through to general_question if no trigger fires.

    Args:
        text: Lowercased user query.

    Returns:
        IntentType string.
    """
    lower = text.lower()
    for intent, keywords in _INTENT_RULES:
        if any(kw in lower for kw in keywords):
            return intent
    return "general_question"


# ── Response builders ──────────────────────────────────────────────────────────

def _handle_suspicious_call(query: str) -> dict:
    """
    Handles suspicious_call intent.

    Runs Module A's score_call() on the user's description, queries the
    knowledge base for matching scam patterns, and checks if any phone
    numbers mentioned appear in the blocklist.

    Returns:
        { risk_level, explanation, next_steps, is_actionable }
    """
    from app.scam_detector.classifier import score_call
    from app.citizen_shield.knowledge_base import search_knowledge_base, check_blocklist

    # Run the classifier treating the user's description as a transcript
    result = score_call(query, call_metadata={"is_spoofed": False})
    score = result["risk_score"]
    patterns = result["triggered_patterns"]

    # Pull relevant KB context
    kb_hits = search_knowledge_base(query, top_k=2, doc_type_filter="SCAM_PATTERN")

    # Phone number extraction — simple regex
    phones = re.findall(r'[\+]?[\d\-\s]{10,15}', query)
    blocklist_hit = None
    for ph in phones:
        hit = check_blocklist(ph.strip())
        if hit:
            blocklist_hit = hit
            break

    # Build risk narrative
    if score >= 85:
        risk_level = "HIGH"
        verdict = "⚠️ HIGH RISK — This call matches multiple active scam patterns."
    elif score >= 40:
        risk_level = "MEDIUM"
        verdict = "⚠️ SUSPICIOUS — Some scam signals detected. Stay cautious."
    else:
        risk_level = "LOW"
        verdict = "✅ LOW RISK — No strong scam indicators found in your description."

    explanation_parts = [verdict]

    if patterns:
        tactic_names = {
            "IMPERSONATION": "government/authority impersonation",
            "URGENCY_THREAT": "urgency/threat pressure",
            "ISOLATION": "isolation instruction (don't tell anyone)",
            "ACTION_REQUEST": "request to share OTP/install software/transfer money",
        }
        tactic_list = ", ".join(
            tactic_names.get(p, p.lower().replace("_", " ")) for p in patterns
            if p in tactic_names
        )
        if tactic_list:
            explanation_parts.append(f"Detected tactics: {tactic_list}.")

    if blocklist_hit:
        count = blocklist_hit.get("report_count", "multiple")
        explanation_parts.append(
            f"⛔ The number you mentioned has been reported {count} times in "
            "the SafeNet demo database for similar fraud. (⚠️ SYNTHETIC DATA)"
        )

    if kb_hits:
        explanation_parts.append(kb_hits[0]["text"][:200] + "…")

    next_steps = (
        "1. Hang up immediately. Do not call back.\n"
        "2. Do not share any OTP, PIN, or personal information.\n"
        "3. Report the number at cybercrime.gov.in or call helpline 1930.\n"
        "4. Tell a trusted family member about the call."
        if risk_level in ("HIGH", "MEDIUM")
        else
        "1. Trust your instincts — if something felt wrong, it may be.\n"
        "2. You can report any suspicious call at cybercrime.gov.in.\n"
        "3. See our safety guide for warning signs to watch for."
    )

    return {
        "risk_level": risk_level,
        "explanation": "\n\n".join(explanation_parts),
        "next_steps": next_steps,
        "is_actionable": risk_level in ("HIGH", "MEDIUM"),
    }


def _handle_upi_fraud(query: str) -> dict:
    """
    Handles upi_fraud_check intent.

    Checks UPI IDs mentioned against the blocklist, queries the KB for
    UPI fraud patterns, and provides recovery guidance if money was sent.
    """
    from app.citizen_shield.knowledge_base import search_knowledge_base, check_blocklist

    # Extract UPI IDs — format: word@word
    upi_ids = re.findall(r'[\w.\-]+@[\w.\-]+', query)
    blocklist_hit = None
    for uid in upi_ids:
        hit = check_blocklist(uid)
        if hit:
            blocklist_hit = hit
            break

    kb_hits = search_knowledge_base(query, top_k=2, doc_type_filter="SCAM_PATTERN")
    report_hits = search_knowledge_base("UPI fraud report bank", top_k=1, doc_type_filter="REPORTING_GUIDE")

    money_sent = any(w in query.lower() for w in [
        "sent", "transferred", "deducted", "lost", "paid", "gone", "gaya",
    ])

    if blocklist_hit:
        risk_level = "HIGH"
        verdict = (
            f"⚠️ HIGH RISK — The UPI ID you mentioned has been flagged "
            f"{blocklist_hit.get('report_count', 'multiple')} times. "
            "(⚠️ SYNTHETIC DATA)"
        )
    elif money_sent:
        risk_level = "HIGH"
        verdict = "⚠️ URGENT — You may have been defrauded. Act immediately."
    else:
        risk_level = "MEDIUM"
        verdict = "⚠️ CAUTION — UPI fraud is common. Here is what to check."

    explanation_parts = [verdict]
    if kb_hits:
        explanation_parts.append(kb_hits[0]["text"][:250] + "…")

    if money_sent:
        next_steps = (
            "1. Call your bank's fraud helpline RIGHT NOW (number on back of card).\n"
            "2. Ask them to freeze the destination account and initiate a chargeback.\n"
            "3. Call the Cyber Crime Helpline: 1930 — report within 24h for best chance of recovery.\n"
            "4. File a complaint at cybercrime.gov.in with transaction ID and screenshots.\n"
            "5. File an FIR at your local police station."
        )
    else:
        next_steps = (
            "1. Never enter your UPI PIN to 'receive' money — that sends money, it doesn't receive it.\n"
            "2. Verify any QR code recipient before paying.\n"
            "3. If unsure about a transaction, call your bank first.\n"
            "4. Report suspicious UPI IDs at cybercrime.gov.in."
        )

    if report_hits:
        explanation_parts.append(report_hits[0]["text"][:200] + "…")

    return {
        "risk_level": risk_level,
        "explanation": "\n\n".join(explanation_parts),
        "next_steps": next_steps,
        "is_actionable": True,
    }


def _handle_counterfeit_note(query: str) -> dict:
    """
    Handles counterfeit_note_query intent.

    Retrieves currency verification guidance and reporting steps from KB.
    """
    from app.citizen_shield.knowledge_base import search_knowledge_base

    kb_hits = search_knowledge_base(query, top_k=2)

    explanation_parts = [
        "🔍 Here is how to check if a note is genuine and what to do if it is not."
    ]
    for hit in kb_hits[:2]:
        explanation_parts.append(hit["text"][:300] + "…")

    next_steps = (
        "1. Do not fold, write on, or damage the suspect note.\n"
        "2. Take it to your bank — they have UV scanners and will impound it.\n"
        "3. Ask the bank for a receipt confirming they received it.\n"
        "4. File a complaint at cybercrime.gov.in or your local police station.\n"
        "5. You will NOT be penalised for receiving a fake note in good faith."
    )

    return {
        "risk_level": "MEDIUM",
        "explanation": "\n\n".join(explanation_parts),
        "next_steps": next_steps,
        "is_actionable": False,
    }


def _handle_general_question(query: str) -> dict:
    """
    Handles general_question intent — broad semantic search over the full KB.
    """
    from app.citizen_shield.knowledge_base import search_knowledge_base

    hits = search_knowledge_base(query, top_k=3)

    if not hits:
        explanation = (
            "I didn't find a specific answer in my knowledge base for that question. "
            "For general fraud queries, you can visit cybercrime.gov.in or call 1930."
        )
        next_steps = "Visit cybercrime.gov.in or call the helpline: 1930."
    else:
        top = hits[0]
        doc_type = top["metadata"].get("doc_type", "")
        explanation_parts = []

        if doc_type == "REPORTING_GUIDE":
            explanation_parts.append("Here is the relevant guidance from the SafeNet knowledge base:")
        elif doc_type == "SCAM_PATTERN":
            explanation_parts.append("Here is what the SafeNet knowledge base says about this type of scam:")
        else:
            explanation_parts.append("Here is what I found:")

        for h in hits[:2]:
            explanation_parts.append(h["text"][:300] + "…")

        explanation = "\n\n".join(explanation_parts)
        next_steps = (
            "If you believe you have been a victim of fraud:\n"
            "1. Report at cybercrime.gov.in\n"
            "2. Call the Cyber Crime Helpline: 1930\n"
            "3. Contact your bank immediately if money was involved."
        )

    return {
        "risk_level": "INFO",
        "explanation": explanation,
        "next_steps": next_steps,
        "is_actionable": False,
    }


# ── Translation ────────────────────────────────────────────────────────────────

def _translate(text: str, target_language: str) -> str:
    """
    Translates text into the target language using an LLM (Gemini or OpenAI).

    Tries GEMINI_API_KEY first (preferred), then LLM_API_KEY / OPENAI_API_KEY.
    Falls back to English + disclaimer if neither key is configured.

    Args:
        text:            English text to translate.
        target_language: Language code from SUPPORTED_LANGUAGES keys.

    Returns:
        Translated string, or original English with a note on failure.
    """
    lang_name = SUPPORTED_LANGUAGES.get(target_language, target_language)

    translate_prompt = (
        f"Translate the following text into {lang_name}. "
        "Keep formatting (line breaks, bullet points) intact. "
        "Preserve proper nouns like 'SafeNet AI', 'cybercrime.gov.in', "
        "and phone numbers unchanged. Return ONLY the translated text.\n\n"
        f"{text}"
    )

    # ── Try Gemini first ──────────────────────────────────────────────────────
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            from google.genai import types as genai_types
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=translate_prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1000,
                ),
            )
            return response.text.strip()
        except Exception as e:
            # Fall through to OpenAI fallback
            pass

    # ── Try OpenAI / LLM_API_KEY ─────────────────────────────────────────────
    openai_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a helpful translator. Translate the following text "
                            f"into {lang_name}. Keep formatting (line breaks, bullet points) "
                            "intact. Preserve proper nouns like 'SafeNet AI', 'cybercrime.gov.in', "
                            "and phone numbers unchanged."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                max_tokens=1000,
                temperature=0.1,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return (
                f"{text}\n\n"
                f"[Translation to {lang_name} failed ({e}). Response shown in English.]"
            )

    # ── No LLM key available ─────────────────────────────────────────────────
    return (
        f"{text}\n\n"
        f"[Translation to {lang_name} unavailable — GEMINI_API_KEY not set. "
        "Response shown in English.]"
    )


# ── Public API ─────────────────────────────────────────────────────────────────

def ask(query: str, language: str = "en") -> dict:
    """
    Main entry point for the Citizen Shield conversational agent.

    Routes to the correct intent handler, composes a response, and
    optionally translates it.

    Args:
        query:    User's natural-language question.
        language: ISO 639-1 language code (default "en").
                  Supported: en, hi, ta, te, bn, mr.
                  Others fall back to English with a note.

    Returns:
        dict matching the chat widget schema:
          {
            id            (str)   — unique message ID,
            sender        (str)   — always "bot",
            text          (str)   — chat-ready response string,
            timestamp     (str)   — ISO datetime,
            isActionable  (bool)  — True for high/medium risk items,
            intent        (str)   — classified intent,
            risk_level    (str)   — HIGH | MEDIUM | LOW | INFO,
            language      (str)   — language code used,
          }
    """
    intent = _classify_intent(query)

    handlers = {
        "suspicious_call": _handle_suspicious_call,
        "upi_fraud_check": _handle_upi_fraud,
        "counterfeit_note_query": _handle_counterfeit_note,
        "general_question": _handle_general_question,
    }

    result = handlers[intent](query)

    # Compose the chat text
    risk_prefix = {
        "HIGH": "⚠️ HIGH RISK",
        "MEDIUM": "⚠️ SUSPICIOUS",
        "LOW": "✅ LOW RISK",
        "INFO": "ℹ️ INFO",
    }.get(result["risk_level"], result["risk_level"])

    text_en = (
        f"{result['explanation']}\n\n"
        f"📋 Next steps:\n{result['next_steps']}\n\n"
        f"─────────────────────────────\n"
        f"SafeNet AI · Powered by synthetic data · Not legal advice"
    )

    # Translate if needed
    if language != "en" and language in SUPPORTED_LANGUAGES:
        text_final = _translate(text_en, language)
    else:
        text_final = text_en

    return {
        "id": f"cs-{abs(hash(query + str(datetime.now(timezone.utc).timestamp()))) % 10**9:09d}",
        "sender": "bot",
        "text": text_final,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "isActionable": result.get("is_actionable", False),
        "intent": intent,
        "risk_level": result["risk_level"],
        "language": language,
    }
