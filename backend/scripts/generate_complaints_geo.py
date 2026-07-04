"""
⚠️ SYNTHETIC DATA GENERATOR — Not derived from real incidents or persons.

Generates synthetic geotagged complaints for the SafeNet AI project.
Clustered roughly in the Delhi NCR bounding box to simulate hotspots.
"""
import json
import random
from uuid import uuid4
from faker import Faker

fake = Faker('en_IN')

# Delhi NCR rough bounding box
LAT_MIN, LAT_MAX = 28.40, 28.80
LNG_MIN, LNG_MAX = 76.80, 77.40

def generate_complaints_geo(num_clusters=8):
    hotspots = []
    
    for _ in range(num_clusters):
        # Create a cluster center
        center_lat = random.uniform(LAT_MIN, LAT_MAX)
        center_lng = random.uniform(LNG_MIN, LNG_MAX)
        
        # Determine intensity based on a weighted random choice
        severity_type = random.choices(
            ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'], 
            weights=[0.1, 0.2, 0.4, 0.3], 
            k=1
        )[0]
        
        if severity_type == 'CRITICAL':
            intensity = random.uniform(0.85, 1.0)
            radius = random.randint(1200, 2000)
            complaint_count = random.randint(50, 100)
        elif severity_type == 'HIGH':
            intensity = random.uniform(0.65, 0.84)
            radius = random.randint(800, 1500)
            complaint_count = random.randint(30, 49)
        elif severity_type == 'MEDIUM':
            intensity = random.uniform(0.4, 0.64)
            radius = random.randint(500, 1000)
            complaint_count = random.randint(10, 29)
        else:
            intensity = random.uniform(0.1, 0.39)
            radius = random.randint(300, 600)
            complaint_count = random.randint(1, 9)
            
        hotspots.append({
            "id": f"hs-SYNTH-{str(uuid4())[:8]}",
            "lat": round(center_lat, 6),
            "lng": round(center_lng, 6),
            "intensity": round(intensity, 2),
            "radius": radius,
            "type": severity_type,
            "complaint_count": complaint_count,
            "primary_complaint_type": random.choice(["UPI Fraud", "Vishing", "Counterfeit Currency", "Job Scam"])
        })
        
    return hotspots

if __name__ == "__main__":
    print("Generating synthetic geospatial complaints (Delhi NCR)...")
    data = generate_complaints_geo(12)
    
    import os
    os.makedirs("../data/synthetic", exist_ok=True),
    
    with open("../data/synthetic/complaints_geo_SYNTHETIC.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    print(f"Success: Generated {len(data)} synthetic hotspots at /data/synthetic/complaints_geo_SYNTHETIC.json")
