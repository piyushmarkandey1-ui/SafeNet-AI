"""
SafeNet AI — Citizen Shield Evaluation Script

Tests the conversational agent for true personalization by simulating 4 scenarios:
1. Scenario A — detailed query (FedEx impersonation)
2. Scenario B — SAME underlying scam pattern as A, but worded completely differently
3. Scenario C — a vague one-liner (should trigger a clarifying question)
4. Scenario D — a follow-up to an ongoing conversation

The script prints the LLM's responses and checks that the responses to A and B
are not identical boilerplate templates.
"""

import sys
import difflib
import time
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Load keys
load_dotenv(backend_dir / ".env")

from app.citizen_shield.agent import respond_to_user

def print_box(title, text):
    print(f"\n{'='*80}")
    print(f" {title} ".center(80, '='))
    print(f"{'='*80}\n")
    print(text)
    print()

def main():
    print("Running Citizen Shield LLM Personalization Eval...\n")

    # ── Test 1: Scenario A (FedEx customs scam, verbose) ──────────────────────
    msg_A = (
        "I just got a call from +916511361582. The guy said he's from FedEx "
        "and my parcel is held at customs because they found illegal items. "
        "He said I need to pay 5000 rupees on a UPI link immediately or police "
        "will come to my house."
    )
    print(f"User (A): {msg_A}")
    res_A = respond_to_user(msg_A, [])
    print_box("Response A", res_A['text'])


    # ── Test 2: Scenario B (Same scam, different wording) ──────────────────────
    time.sleep(1) # stagger just slightly
    msg_B = (
        "Someone rang me claiming customs intercepted a package with my name "
        "on it. They threatened me with arrest and said to transfer money "
        "right now so they can clear it."
    )
    print(f"User (B): {msg_B}")
    res_B = respond_to_user(msg_B, [])
    print_box("Response B", res_B['text'])


    # ── Comparison A vs B ─────────────────────────────────────────────────────
    similarity = difflib.SequenceMatcher(None, res_A['text'], res_B['text']).ratio()
    print(f"Similarity between A and B: {similarity:.2f} (should be low, < 0.60)")
    if similarity > 0.8:
        print("FAIL: Responses are too similar. The LLM is likely falling back to a fixed template.")
    else:
        print("PASS: Responses are distinctly phrased despite the same underlying scam.")


    # ── Test 3: Scenario C (Vague one-liner) ──────────────────────────────────
    msg_C = "is this number a scam 9876543210?"
    print(f"\nUser (C): {msg_C}")
    res_C = respond_to_user(msg_C, [])
    print_box("Response C (Vague)", res_C['text'])
    if "?" in res_C['text']:
        print("PASS: Agent asked a clarifying question.")
    else:
        print("FAIL: Agent did not ask a clarifying question for a vague prompt.")


    # ── Test 4: Scenario D (Follow-up conversation) ───────────────────────────
    history = [
        {"role": "user", "content": "I got a call saying my bank account is blocked and I need to share my Aadhaar over WhatsApp."},
        {"role": "assistant", "content": "That sounds like a classic impersonation scam. Banks do not ask you to share your Aadhaar over WhatsApp to unblock an account. Did you share any details with them?"},
    ]
    msg_D = "No I didn't send anything, I just cut the call. What should I do now?"
    print(f"\nUser (D): {msg_D}")
    res_D = respond_to_user(msg_D, history)
    print_box("Response D (Follow-up)", res_D['text'])


if __name__ == "__main__":
    main()
