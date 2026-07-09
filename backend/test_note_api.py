"""Quick test of the note checker API endpoint"""
import requests
from pathlib import Path

# Test image
img_path = Path("../data/raw/currency/fake/500/SYNTHETIC_fake_500_000.jpg")

if not img_path.exists():
    print(f"❌ Image not found: {img_path}")
    exit(1)

print(f"Testing with: {img_path}")

# Test the API
with open(img_path, "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/vision/check-note",
        files={"file": ("test.jpg", f, "image/jpeg")}
    )

print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

if response.status_code == 200:
    result = response.json()
    print(f"\n✅ SUCCESS!")
    print(f"  is_fake: {result['is_fake']}")
    print(f"  confidence: {result['confidence']}")
    print(f"  denomination: {result['denomination']}")
    print(f"  severity: {result['severity']}")
    print(f"  recommendation: {result['recommendation'][:80]}...")
else:
    print(f"❌ FAILED: {response.status_code}")
