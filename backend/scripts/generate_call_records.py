"""
⚠️ SYNTHETIC DATA GENERATOR — Not derived from real incidents or persons.

Generates synthetic CDR (Call Detail Record) style data for the SafeNet AI project.
"""
import csv
import json
import random
from uuid import uuid4
from faker import Faker

fake = Faker('en_IN')

# Phrase bank for transcript snippets
SCAM_PHRASES = [
    "This is the police department, there is a warrant for your arrest.",
    "Your tax penalty is pending, please press 1 to resolve.",
    "We noticed unauthorized charges, please read the code we just sent you.",
    "Your package is held at customs. Click the link to pay the fee.",
    "Your bank account will be frozen in 2 hours due to suspicious activity.",
    "You have won a lottery of 50 Lakhs. Pay processing fee to claim.",
]

BENIGN_PHRASES = [
    "Hey, what time are we meeting for dinner?",
    "Can you pick up some groceries on your way home?",
    "Your appointment is confirmed for tomorrow at 10 AM.",
    "Did you get the email I sent earlier?",
    "Happy Birthday! Hope you have a great day.",
    "The weather is supposed to be nice this weekend.",
]

def generate_call_records(num_records=1000):
    records = []
    
    for _ in range(num_records):
        is_spoofed = random.random() < 0.15 # 15% chance of being spoofed (scam)
        
        caller = fake.phone_number()
        callee = fake.phone_number()
        duration = random.randint(10, 3600)
        
        if is_spoofed:
            snippet = random.choice(SCAM_PHRASES)
            duration = random.randint(10, 300) # Scams are usually shorter if they fail
        else:
            snippet = random.choice(BENIGN_PHRASES)
            
        record = {
            "call_id": str(uuid4()),
            "caller_number": caller,
            "callee_number": callee,
            "duration_sec": duration,
            "is_spoofed": is_spoofed,
            "transcript_snippet": snippet,
            "timestamp": fake.date_time_between(start_date='-30d', end_date='now').isoformat()
        }
        records.append(record)
        
    return records

if __name__ == "__main__":
    print("Generating synthetic call records...")
    data = generate_call_records(500)
    
    import os
    os.makedirs("../data/synthetic", exist_ok=True)
    
    with open("../data/synthetic/calls_SYNTHETIC.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
    print(f"Success: Generated 500 synthetic call records at /data/synthetic/calls_SYNTHETIC.csv")
