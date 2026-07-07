"""
# ⚠️  SYNTHETIC DATA — Not derived from real incidents or persons.

SafeNet AI — Streaming Scam Call Demo

Replays synthetic call transcripts with live-updating risk scores.
Useful for demonstration and testing the classifier in real-time.
"""
import asyncio
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.scam_detector.classifier import score_call

# Synthetic scam transcript - classic tech support scam
SCAM_TRANSCRIPT = """
Caller: Hello, this is Microsoft technical support. We're calling because your computer has been sending error signals to our servers.
Victim: Oh really? I didn't know.
Caller: Yes, it's critical. Your IP address has been compromised and hackers are accessing your files. You need to act immediately.
Victim: What should I do?
Caller: Go to your computer now. Do not tell anyone about this call. Stay on the line with me.
Victim: Okay, I'm at my computer.
Caller: Good. Download AnyDesk from anydesk.com. I need to connect to your screen to fix this security breach.
Victim: Is that safe?
Caller: It's the only way to save your data. If you don't act within 10 minutes, your bank accounts will be frozen.
Victim: Alright, I'm downloading it.
Caller: Once installed, give me the 9-digit code so I can connect. This is urgent.
"""

# Synthetic benign transcript - legitimate customer service call
BENIGN_TRANSCRIPT = """
Caller: Hi, this is Sarah from Amazon Customer Service. I'm calling about your recent order.
Victim: Oh, which order?
Caller: Order #123456789 - the package with the books you ordered last week.
Victim: Yes, that arrived yesterday.
Caller: Great! I just wanted to confirm delivery and ask if you'd like to rate your experience.
Victim: It was fine, no issues.
Caller: Wonderful. Is there anything else I can help you with today?
Victim: No, that's all. Thank you for calling.
Caller: You're welcome. Have a great day!
"""

# Synthetic ambiguous transcript - suspicious but not clearly scam
AMBIGUOUS_TRANSCRIPT = """
Caller: Hello, this is calling from your bank's fraud department.
Victim: Which bank?
Caller: HDFC Bank. We noticed some unusual activity on your account yesterday.
Victim: What kind of activity?
Caller: Several large transactions in a different city. Can you confirm if you made these?
Victim: No, I was here all day.
Caller: I see. For your security, we recommend changing your password through our official app.
Victim: Okay, I can do that.
Caller: Please use our official website or mobile app. Never share your OTP with anyone.
Victim: Understood. Thank you for letting me know.
Caller: You're welcome. Stay safe.
"""

async def stream_transcript(transcript: str, call_metadata: dict, delay: float = 0.5):
    """
    Streams a transcript word by word with live risk scoring.
    
    Args:
        transcript: Full transcript text
        call_metadata: Call metadata dict
        delay: Delay between words in seconds
    """
    words = transcript.split()
    current_window = ""
    
    print("\n" + "="*60)
    print("LIVE TRANSCRIPT STREAM")
    print("="*60 + "\n")
    
    for i, word in enumerate(words):
        current_window += " " + word
        current_window = current_window.strip()
        
        # Score every 5 words
        if (i + 1) % 5 == 0:
            result = score_call(current_window, call_metadata)
            
            # Clear line and print live score
            print(f"\r[{i+1}/{len(words)}] Risk Score: {result['risk_score']:3d} | Patterns: {', '.join(result['triggered_patterns'][:3])}", end="")
            sys.stdout.flush()
            
            await asyncio.sleep(delay)
    
    # Final score
    result = score_call(transcript, call_metadata)
    print(f"\n\n{'='*60}")
    print(f"FINAL RISK SCORE: {result['risk_score']}/100")
    print(f"Severity: {result['severity'].upper()}")
    print(f"Triggered Patterns: {', '.join(result['triggered_patterns'])}")
    print(f"Recommendation: {result['recommendation']}")
    print("="*60 + "\n")

async def main():
    """Run streaming demos for scam, benign, and ambiguous cases."""
    
    print("\n" + "█"*60)
    print("SafeNet AI — Scam Call Classifier Demo")
    print("█"*60)
    
    # Demo 1: Clear Scam
    print("\n📞 DEMO 1: SCAM CALL (Tech Support Impersonation)")
    scam_metadata = {
        "is_spoofed": True,
        "duration_sec": 120,
        "video_requested": False
    }
    await stream_transcript(SCAM_TRANSCRIPT, scam_metadata, delay=0.3)
    
    # Demo 2: Benign Call
    print("\n📞 DEMO 2: BENIGN CALL (Amazon Customer Service)")
    benign_metadata = {
        "is_spoofed": False,
        "duration_sec": 45,
        "video_requested": False
    }
    await stream_transcript(BENIGN_TRANSCRIPT, benign_metadata, delay=0.3)
    
    # Demo 3: Ambiguous Call
    print("\n📞 DEMO 3: AMBIGUOUS CALL (Bank Fraud Warning)")
    ambiguous_metadata = {
        "is_spoofed": False,
        "duration_sec": 60,
        "video_requested": False
    }
    await stream_transcript(AMBIGUOUS_TRANSCRIPT, ambiguous_metadata, delay=0.3)
    
    print("\n✅ Demo complete!")

if __name__ == "__main__":
    asyncio.run(main())
