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
    Only called if GEMINI_API_KEY environment variable is set.
    
    Args:
        transcript_window: The call transcript text
        base_score: The pattern-matching base score (0-100)
        
    Returns:
        Adjusted score if Gemini is available, None otherwise
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        return None
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_api_key)
        
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""You are a fraud detection expert. Rate the scam likelihood of this call transcript on a scale of 0-100.

Transcript: {transcript_window}

Rate scam likelihood (0-100, return ONLY the number):"""
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                max_output_tokens=10,
            )
        )
        
        llm_score_str = response.text.strip()
        llm_score = float(llm_score_str) if llm_score_str.replace('.', '').isdigit() else None
        
        if llm_score is not None:
            # Weighted average: 70% pattern matching, 30% LLM
            adjusted_score = int(base_score * 0.7 + llm_score * 0.3)
            return min(max(adjusted_score, 0), 100)
            
    except Exception as e:
        # Silently fall back to pattern matching if LLM fails
        print(f"Gemini check failed: {e}")
    
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
