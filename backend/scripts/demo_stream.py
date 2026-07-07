import time
import sys
import os
import requests
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init(autoreset=True)

API_URL = "http://localhost:8000/scam/score-call"

# Synthetic scam transcript demonstrating progressive escalation
SCAM_TRANSCRIPT = [
    ("Agent", "Hello, am I speaking with the account holder?"),
    ("Victim", "Yes, who is this?"),
    ("Agent", "This is the police department cyber cell. We have found suspicious activity."),
    ("Victim", "What? Police? What activity?"),
    ("Agent", "There is a warrant for your arrest regarding money laundering."),
    ("Victim", "This has to be a mistake!"),
    ("Agent", "Do not tell anyone. Stay on the line. Go to a quiet room immediately."),
    ("Victim", "Okay, I'm alone. What do I do?"),
    ("Agent", "We need to verify your identity. I am sending an OTP, please read the code back to me."),
]

def stream_call(transcript, is_spoofed=True):
    print(f"\n{Fore.CYAN}=== SAFENET AI LIVE INTERCEPT SIMULATION ==={Style.RESET_ALL}\n")
    
    accumulated_text = ""
    
    for speaker, phrase in transcript:
        accumulated_text += f" {phrase}"
        
        # Print the live transcript line
        color = Fore.YELLOW if speaker == "Agent" else Fore.WHITE
        print(f"{color}[{speaker}]: {phrase}{Style.RESET_ALL}")
        
        # Simulate network latency/speech delay
        time.sleep(1.5)
        
        # Score the accumulated window via FastAPI
        try:
            response = requests.post(
                API_URL, 
                json={
                    "caller_number": "+91-99999-00000",
                    "callee_number": "+91-88888-11111",
                    "transcript_window": accumulated_text,
                    "is_spoofed": is_spoofed,
                    "duration_sec": 45
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                score = result["risk_score"]
                sev = result["severity"]
                
                # Color code the score
                if sev == "critical":
                    s_color = Fore.RED + Style.BRIGHT
                elif sev == "high":
                    s_color = Fore.LIGHTRED_EX
                elif sev == "medium":
                    s_color = Fore.YELLOW
                else:
                    s_color = Fore.GREEN
                    
                print(f"  -> {Fore.LIGHTBLACK_EX}Real-time Risk Score:{Style.RESET_ALL} {s_color}{score}/100 ({sev.upper()}){Style.RESET_ALL}")
                if result["triggered_patterns"]:
                    print(f"  -> {Fore.LIGHTBLACK_EX}Flags:{Style.RESET_ALL} {', '.join(result['triggered_patterns'])}")
            else:
                print(f"  -> {Fore.RED}Error hitting API: {response.status_code}{Style.RESET_ALL}")
        except requests.exceptions.ConnectionError:
            print(f"  -> {Fore.RED}Backend not running! Start with: uvicorn app.main:app --reload{Style.RESET_ALL}")
            sys.exit(1)
            
        print("-" * 50)
        
    print(f"\n{Fore.CYAN}=== INTERCEPT COMPLETE ==={Style.RESET_ALL}\n")

if __name__ == "__main__":
    stream_call(SCAM_TRANSCRIPT)
