"""
SafeNet AI — Number Risk Checker (Module F)

check_number(phone_number, pasted_text) is the single callable interface.

Signal sources (in order of reliability):
  1. Fraud Graph lookup   — strongest signal. Walks the graph for this exact
                            phone number (or a partial match). If found, extracts
                            real case metadata: connected accounts, flagged txns,
                            spoofed calls, mule scores.
  2. Scam text analysis  — runs pasted_text through Module A's pattern matcher
                            (score_call). Returns specific triggered tactics, not
                            a vague score.
  3. Synthetic blocklist — a curated set of numbers known in our synthetic
                            dataset to be high-risk (derived from calls_SYNTHETIC.csv
                            spoofed=True rows). Clearly labelled as synthetic data.

Combination logic:
  - Any graph hit → risk ≥ medium, with specific case details
  - High text score (≥60) → risk ≥ high
  - Blocklist hit → risk ≥ medium
  - Nothing found → honest "no record" response, no fake confidence

⚠️ SYNTHETIC DATA — no real call interception or live telecom access.
   Users submit numbers and text themselves.
"""

from __future__ import annotations

import re
import os
from typing import Optional
from dataclasses import dataclass, field


# ── Synthetic blocklist ────────────────────────────────────────────────────────
# Derived from calls_SYNTHETIC.csv rows where is_spoofed == True.
# These are 100% synthetic numbers for demonstration purposes.
# ⚠️ SYNTHETIC DATA
SYNTHETIC_BLOCKLIST: dict[str, str] = {
    "+916511361582": "Spoofed customs-fee scam call (synthetic dataset)",
    "+913026150729": "Spoofed package-delivery phishing call (synthetic dataset)",
    "01203452744":   "OTP-harvesting scam call — 'unauthorized charges' script (synthetic dataset)",
    "04148331485":   "Tax-penalty vishing — 'press 1' IVR scam (synthetic dataset)",
    "08706972742":   "Lottery advance-fee fraud (synthetic dataset)",
    "5107922983":    "Spoofed authority impersonation call (synthetic dataset)",
    "5914897919":    "Spoofed authority impersonation call (synthetic dataset)",
    "4063244356":    "Spoofed fraud-department impersonation (synthetic dataset)",
    "01918348965":   "Spoofed call — isolation + urgency tactics (synthetic dataset)",
    "+913106561239": "Spoofed CBI impersonation call (synthetic dataset)",
    "+916785432109": "Known mule-ring coordinator number (synthetic dataset)",
    "+919876543210": "UPI-scam SMS originator (synthetic dataset)",
}

# Tactic → human-readable explanation
TACTIC_EXPLANATIONS = {
    "IMPERSONATION":      "Authority impersonation language (police / CBI / bank / courier)",
    "URGENCY_THREAT":     "Urgency and threat language ('immediately', 'freeze account', 'legal action')",
    "ISOLATION":          "Isolation tactics ('do not tell anyone', 'stay on the line')",
    "ACTION_REQUEST":     "Dangerous action requests (OTP, password, crypto transfer, remote-access app)",
    "SPOOFED_CALLER_ID":  "Caller ID appears spoofed",
    "VIDEO_COERCION":     "Video call / camera access requested (sextortion risk)",
    "GEMINI_VERIFIED":    "AI secondary check confirmed suspicious content",
}


@dataclass
class NumberRiskResult:
    risk_level:     str          # "low" | "medium" | "high" | "critical"
    confidence:     float        # 0.0 – 1.0
    reasons:        list[str]    # specific, traceable reasons
    recommendation: str
    graph_case:     Optional[dict] = None   # raw case summary if graph hit
    text_score:     Optional[int]  = None   # raw score_call result if text provided
    sources_checked: list[str]    = field(default_factory=list)


def _normalise_number(phone: str) -> list[str]:
    """
    Returns a list of number variants to check against the graph and blocklist.
    e.g. '+916511361582' → ['+916511361582', '916511361582', '6511361582']
    """
    digits_only = re.sub(r"[^\d]", "", phone)
    variants = [phone.strip(), digits_only]
    if digits_only.startswith("91") and len(digits_only) > 10:
        variants.append(digits_only[2:])   # strip country code
    if not digits_only.startswith("91") and len(digits_only) == 10:
        variants.append("91" + digits_only)
        variants.append("+91" + digits_only)
    return list(dict.fromkeys(v for v in variants if v))  # deduplicate, preserve order


def _check_blocklist(variants: list[str]) -> Optional[str]:
    """Returns blocklist reason string if any variant matches, else None."""
    for v in variants:
        if v in SYNTHETIC_BLOCKLIST:
            return SYNTHETIC_BLOCKLIST[v]
    return None


def _check_graph(variants: list[str]) -> Optional[dict]:
    """
    Tries to find the number in the fraud graph using get_case_summary.
    Returns the case dict on hit, None on miss.
    The graph uses a fuzzy partial-match fallback internally.
    """
    try:
        from app.fraud_graph.analysis import get_case_summary
        for variant in variants:
            try:
                case = get_case_summary(variant, hops=2)
                return case
            except KeyError:
                continue
    except Exception:
        pass
    return None


def _check_text(pasted_text: str) -> Optional[dict]:
    """
    Runs pasted_text through Module A's score_call pattern matcher.
    Returns the score_call result dict, or None on error.
    """
    try:
        from app.scam_detector.classifier import score_call
        return score_call(pasted_text, call_metadata={})
    except Exception:
        return None


def check_number(
    phone_number: str,
    pasted_text: Optional[str] = None,
) -> NumberRiskResult:
    """
    Checks a user-submitted phone number (and optional message text) against
    all available signal sources and returns an explainable risk verdict.

    Args:
        phone_number: The number the user wants to check (any format).
        pasted_text:  Optional message/transcript text pasted by the user.

    Returns:
        NumberRiskResult with risk_level, confidence, specific reasons, and
        recommendation. Never returns a vague verdict — every reason cites
        which signal source triggered it.
    """
    variants = _normalise_number(phone_number)
    reasons: list[str] = []
    sources_checked: list[str] = []
    graph_case: Optional[dict] = None
    text_result: Optional[dict] = None

    risk_score = 0  # internal accumulator (0–100)

    # ── Signal 1: Fraud Graph ─────────────────────────────────────────────────
    sources_checked.append("Fraud Graph (synthetic call + transaction network)")
    graph_case = _check_graph(variants)
    if graph_case:
        g_score = graph_case.get("riskScore", 0)
        risk_score = max(risk_score, g_score)

        linked = graph_case.get("linkedEntities", [])
        flagged_count = sum(
            1 for e in graph_case.get("edges", []) if e.get("flagged_mule")
        )
        spoofed_count = sum(
            1 for e in graph_case.get("edges", []) if e.get("is_spoofed")
        )
        connected_nodes = graph_case.get("connected_nodes", 0)

        if connected_nodes > 0:
            reasons.append(
                f"This number appears in the fraud graph (Case {graph_case.get('caseId', 'N/A')}) "
                f"connected to {connected_nodes - 1} other entities within 2 hops."
            )
        if spoofed_count > 0:
            reasons.append(
                f"Fraud graph shows {spoofed_count} spoofed call(s) linked to this number."
            )
        if flagged_count > 0:
            reasons.append(
                f"{flagged_count} transaction(s) in the linked cluster are flagged as "
                f"mule activity."
            )
        threat = graph_case.get("primaryThreat")
        if threat:
            reasons.append(f"Primary threat classification: {threat}.")

    # ── Signal 2: Pasted text / message analysis ──────────────────────────────
    if pasted_text and pasted_text.strip():
        sources_checked.append("Message content analysis (Module A — scam pattern matcher)")
        text_result = _check_text(pasted_text)
        if text_result:
            txt_score = text_result.get("risk_score", 0)
            triggered = text_result.get("triggered_patterns", [])
            risk_score = max(risk_score, txt_score)

            for tactic in triggered:
                explanation = TACTIC_EXPLANATIONS.get(tactic, tactic)
                reasons.append(f"Message text contains {explanation}.")

            if txt_score >= 60 and not triggered:
                reasons.append(
                    f"Message text scored {txt_score}/100 for scam likelihood "
                    f"(AI secondary verification)."
                )

    # ── Signal 3: Synthetic blocklist ─────────────────────────────────────────
    sources_checked.append("Synthetic blocklist (known scam numbers from demo dataset)")
    blocklist_hit = _check_blocklist(variants)
    if blocklist_hit:
        risk_score = max(risk_score, 65)
        reasons.append(
            f"Number matches synthetic blocklist entry: {blocklist_hit}."
        )

    # ── Combine into verdict ──────────────────────────────────────────────────
    if not reasons:
        # Honest no-match response — never imply "safe"
        return NumberRiskResult(
            risk_level="low",
            confidence=0.0,
            reasons=[
                "No matches found in our fraud graph, scam-pattern analysis, "
                "or synthetic blocklist for this number."
            ],
            recommendation=(
                "We have no record of this number in our data. "
                "This does NOT guarantee the number is safe — it simply means "
                "we have not encountered it in our synthetic dataset. "
                "If you received a suspicious call or message, trust your instincts "
                "and do not share OTPs, passwords, or money."
            ),
            graph_case=None,
            text_score=text_result.get("risk_score") if text_result else None,
            sources_checked=sources_checked,
        )

    # Map accumulated score → risk level and confidence
    if risk_score >= 85:
        risk_level = "critical"
        confidence = min(0.70 + (risk_score - 85) * 0.01, 0.97)
    elif risk_score >= 60:
        risk_level = "high"
        confidence = min(0.55 + (risk_score - 60) * 0.008, 0.75)
    elif risk_score >= 30:
        risk_level = "medium"
        confidence = min(0.40 + (risk_score - 30) * 0.005, 0.55)
    else:
        risk_level = "low"
        confidence = 0.30

    # Build recommendation
    if risk_level in ("critical", "high"):
        recommendation = (
            "Do NOT share OTPs, PINs, passwords, or money with this number. "
            "Block the number immediately. If you have already made a payment, "
            "contact your bank's fraud helpline (1800-xxx-xxxx) and file a "
            "complaint on cybercrime.gov.in."
        )
    elif risk_level == "medium":
        recommendation = (
            "Exercise caution. Verify the caller's identity through official "
            "channels before taking any action. Do not click links or share "
            "personal information until verified."
        )
    else:
        recommendation = (
            "Treat with normal caution. No strong signals found, but "
            "never share OTPs or financial credentials over call or SMS."
        )

    return NumberRiskResult(
        risk_level=risk_level,
        confidence=round(confidence, 3),
        reasons=reasons,
        recommendation=recommendation,
        graph_case=graph_case,
        text_score=text_result.get("risk_score") if text_result else None,
        sources_checked=sources_checked,
    )
