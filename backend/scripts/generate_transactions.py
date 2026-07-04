"""
⚠️ SYNTHETIC DATA GENERATOR — Not derived from real incidents or persons.

Generates synthetic transaction (UPI-style) data for the SafeNet AI project.
Injects a "fan-in" pattern to simulate money mule networks.
"""
import csv
import random
from uuid import uuid4
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('en_IN')

def generate_transactions(num_normal=800, num_mule_networks=3):
    records = []
    
    # 1. Generate normal transactions
    for _ in range(num_normal):
        records.append({
            "txn_id": str(uuid4()),
            "sender_account": fake.bban(),
            "receiver_account": fake.bban(),
            "amount": round(random.uniform(10, 50000), 2),
            "timestamp": fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            "flagged_mule": False,
            "device_hash": fake.sha256()[:16]
        })
        
    # 2. Inject fan-in patterns (mule networks)
    # Multiple senders transferring just below the 50k threshold to a single receiver
    for _ in range(num_mule_networks):
        mule_account = fake.bban()
        mule_device = fake.sha256()[:16]
        
        num_senders = random.randint(5, 12)
        base_time = fake.date_time_between(start_date='-5d', end_date='now')
        
        for _ in range(num_senders):
            sender_account = fake.bban()
            # Send amounts like 49,900 or 49,999 to avoid standard thresholds
            amount = round(random.uniform(49000, 49999), 2) 
            
            # Transactions happen within a tight 2-hour window
            txn_time = base_time + timedelta(minutes=random.randint(1, 120))
            
            records.append({
                "txn_id": str(uuid4()),
                "sender_account": sender_account,
                "receiver_account": mule_account,
                "amount": amount,
                "timestamp": txn_time.isoformat(),
                "flagged_mule": True,
                "device_hash": fake.sha256()[:16] # Senders use different devices
            })
            
        # The mule then immediately sweeps the funds out to a final account
        sweep_time = base_time + timedelta(minutes=130)
        records.append({
            "txn_id": str(uuid4()),
            "sender_account": mule_account,
            "receiver_account": fake.bban(),
            "amount": round(num_senders * 49500, 2), # Sweep total
            "timestamp": sweep_time.isoformat(),
            "flagged_mule": True,
            "device_hash": mule_device
        })
        
    random.shuffle(records)
    return records

if __name__ == "__main__":
    print("Generating synthetic transaction records with fan-in patterns...")
    data = generate_transactions(800, 4)
    
    import os
    os.makedirs("../data/synthetic", exist_ok=True)
    
    with open("../data/synthetic/transactions_SYNTHETIC.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
    print(f"Success: Generated {len(data)} synthetic transactions at /data/synthetic/transactions_SYNTHETIC.csv")
