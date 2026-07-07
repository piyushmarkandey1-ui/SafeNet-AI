import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.scam_detector.classifier import score_call

def test_high_risk_scam_call():
    transcript = "This is the CBI. We have an arrest warrant for you. Do not tell anyone and stay on the line. You need to transfer the penalty fee immediately."
    metadata = {"is_spoofed": True, "video_requested": False}
    
    result = score_call(transcript, metadata)
    
    assert result["risk_score"] >= 85
    assert result["severity"] == "critical"
    assert "IMPERSONATION" in result["triggered_patterns"]
    assert "URGENCY_THREAT" in result["triggered_patterns"]
    assert "ISOLATION" in result["triggered_patterns"]
    assert "SPOOFED_CALLER_ID" in result["triggered_patterns"]

def test_low_risk_benign_call():
    transcript = "Hey, what time are we meeting for dinner? The weather is supposed to be nice this weekend."
    metadata = {"is_spoofed": False, "video_requested": False}
    
    result = score_call(transcript, metadata)
    
    assert result["risk_score"] < 20
    assert result["severity"] == "safe"
    assert len(result["triggered_patterns"]) == 0

def test_mid_risk_ambiguous_call():
    transcript = "Can you read the code to me? The OTP you just received?"
    metadata = {"is_spoofed": False, "video_requested": False}
    
    result = score_call(transcript, metadata)
    
    assert 30 <= result["risk_score"] < 60
    assert result["severity"] == "medium"
    assert "ACTION_REQUEST" in result["triggered_patterns"]
