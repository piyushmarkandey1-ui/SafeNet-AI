"""
SafeNet AI — Scam Call Classifier

Baseline deterministic pattern-matching engine for detecting scam tactics
in call transcripts. Designed for high explainability and low latency.
"""
import re
import os
from typing import Optional

# Tactic Categories and their associated regex patterns
TACTIC_PATTERNS = {
    "IMPERSONATION": [
        r"\b(?:police|cbi|customs|fedex|interpol|narcotics)\b",
        r"\b(?:arrest warrant|warrant for your arrest)\b",
        r"\b(?:bank manager|fraud department)\b"
    ],
    "URGENCY_THREAT": [
        r"\b(?:immediately|right now|within \d+ hours)\b",
        r"\b(?:freeze your account|frozen|suspend your)\b",
        r"\b(?:penalty|pay a fine|legal action)\b"
    ],
    "ISOLATION": [
        r"\b(?:do not tell anyone|stay on the line|don't disconnect)\b",
        r"\b(?:go to a quiet room|alone)\b"
    ],
    "ACTION_REQUEST": [
        r"\b(?:download|anydesk|teamviewer|quicksupport)\b",
        r"\b(?:otp|pin|password|read the code)\b",
        r"\b(?:transfer|crypto|bitcoin|gift card)\b",
        r"\b(?:skype|video call|camera)\b"
    ]
}

# Base points awarded when a tactic pattern is found
TACTIC_WEIGHTS = {
    "IMPERSONATION": 25,
    "URGENCY_THREAT": 20,
    "ISOLATION": 30,
    "ACTION_REQUEST": 35
}

def _llm_secondary_check(transcript_window: str, base_score: int) -> Optional[float]:
    """
    Optional LLM pass for secondary confidence scoring.

    Uses Fireworks AI (AMD-hosted) as primary, Gemini as fallback.
    Only triggers when at least one API key is configured.

    Args:
        transcript_window: The call transcript text
        base_score: The pattern-matching base score (0-100)

    Returns:
        Adjusted score if any LLM is available, None otherwise
    """
    # Check if any provider is available before building the prompt
    has_fireworks = bool(os.getenv("FIREWORKS_API_KEY"))
    has_gemini    = bool(os.getenv("GEMINI_API_KEY"))
    has_openai    = bool(os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))

    if not (has_fireworks or has_gemini or has_openai):
        return None

    try:
        from app.fireworks_client import call_llm

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a fraud detection expert. "
                    "Rate the scam likelihood of a call transcript on a scale of 0-100. "
                    "Return ONLY a single integer number, nothing else."
                ),
            },
            {
                "role": "user",
                "content": f"Transcript: {transcript_window[:800]}\n\nScam likelihood (0-100):",
            },
        ]

        result = call_llm(messages, task="classification", temperature=0, max_tokens=10)
        if result:
            # Strip any extra text and parse the number
            num_str = result.strip().split()[0].replace(".", "")
            if num_str.isdigit():
                llm_score = float(num_str)
                # Weighted average: 70% pattern matching, 30% LLM
                adjusted = int(base_score * 0.7 + llm_score * 0.3)
                return min(max(adjusted, 0), 100)

    except Exception as e:
        print(f"LLM secondary check failed: {e}")

    return None


def score_call(transcript_window: str, call_metadata: dict) -> dict:
    """
    Evaluates a transcript snippet and metadata to produce a risk score.
    """
    text = transcript_window.lower()
    score = 0
    triggered_patterns = []
    
    # 1. NLP Pattern Matching
    for tactic, patterns in TACTIC_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                score += TACTIC_WEIGHTS[tactic]
                if tactic not in triggered_patterns:
                    triggered_patterns.append(tactic)
                # Don't add weight multiple times for the same tactic to prevent runaway scores
                break 
                
    # 2. Metadata Modifiers
    is_spoofed = call_metadata.get('is_spoofed', False)
    duration = call_metadata.get('duration_sec', 0)
    video_requested = call_metadata.get('video_requested', False)
    
    if is_spoofed:
        score *= 1.5
        triggered_patterns.append("SPOOFED_CALLER_ID")
        
    if video_requested:
        score += 40
        triggered_patterns.append("VIDEO_COERCION")
        
    # Standardize score (0 - 100)
    final_score = min(max(int(score), 0), 100)
    
    # 3. Optional Gemini Secondary Check
    gemini_adjusted = _llm_secondary_check(transcript_window, final_score)
    if gemini_adjusted is not None:
        final_score = gemini_adjusted
        triggered_patterns.append("GEMINI_VERIFIED")
    
    # Generate Recommendation
    recommendation = "Call appears normal. No immediate action required."
    severity = "safe"
    if final_score >= 85:
        recommendation = "CRITICAL: High probability of active scam. Recommend immediate intercept and block."
        severity = "critical"
    elif final_score >= 60:
        recommendation = "WARNING: Suspicious tactics detected. Issue real-time warning to victim."
        severity = "high"
    elif final_score >= 30:
        recommendation = "MONITOR: Some unusual patterns. Continue listening for escalation."
        severity = "medium"
        
    return {
        "risk_score": final_score,
        "severity": severity,
        "triggered_patterns": triggered_patterns,
        "recommendation": recommendation,
        "transcript_snippet": transcript_window
    }
