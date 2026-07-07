"""
# ⚠️  SYNTHETIC DATA — Not derived from real incidents or persons.

SafeNet AI — Counterfeit Vision: API Endpoint Test

Sends synthetic note images to POST /vision/check-note and prints results.
"""
import sys
import json
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests
except ImportError:
    print("requests not installed: pip install requests")
    sys.exit(1)

API_URL = "http://localhost:8000/vision/check-note"
DATA_ROOT = Path(__file__).parent.parent.parent / "data" / "raw" / "currency"


def check_image(img_path: Path, expected_label: str) -> None:
    print(f"\n{'='*58}")
    print(f"  File     : {img_path.name}")
    print(f"  Expected : {expected_label}")
    print(f"{'='*58}")

    with open(img_path, "rb") as f:
        response = requests.post(
            API_URL,
            files={"file": (img_path.name, f, "image/jpeg")},
            timeout=60,
        )

    if response.status_code != 200:
        print(f"  ❌  HTTP {response.status_code}: {response.text}")
        return

    result = response.json()
    correct = "✅" if (result["auth_class"] == expected_label) else "❌"

    print(f"  {correct} auth_class   : {result['auth_class']}")
    print(f"     is_fake      : {result['is_fake']}")
    print(f"     confidence   : {result['confidence']:.4f}")
    print(f"     denomination : {result['denomination']}")
    print(f"     severity     : {result['severity']}")
    print(f"     event_id     : {result['event_id']}")
    print(f"     gradcam_len  : {len(result['gradcam_overlay'])} chars")
    print(f"     recommendation: {result['recommendation'][:60]}...")

    # Save Grad-CAM
    if result["gradcam_overlay"]:
        out_path = Path(__file__).parent / f"api_gradcam_{expected_label}.png"
        out_path.write_bytes(base64.b64decode(result["gradcam_overlay"]))
        print(f"     overlay_saved: {out_path}")


if __name__ == "__main__":
    fake_imgs = sorted((DATA_ROOT / "fake" / "500").glob("*.jpg"))
    real_imgs = sorted((DATA_ROOT / "real" / "100").glob("*.jpg"))

    if not fake_imgs or not real_imgs:
        print("Run download_dataset.py --synthetic first.")
        sys.exit(1)

    try:
        import requests
        requests.get("http://localhost:8000/", timeout=3)
    except Exception:
        print("❌  Backend not running. Start with:")
        print("   uvicorn app.main:app --reload")
        sys.exit(1)

    check_image(fake_imgs[0], "fake")
    check_image(real_imgs[0], "real")

    # Check /dashboard/feed for the counterfeit event
    import requests as req
    feed = req.get("http://localhost:8000/dashboard/feed").json()
    cv_events = [e for e in feed if e.get("type") == "COUNTERFEIT"]
    print(f"\n{'='*58}")
    print(f"  /dashboard/feed  →  {len(cv_events)} COUNTERFEIT event(s) injected")
    if cv_events:
        e = cv_events[0]
        print(f"     title    : {e['title']}")
        print(f"     severity : {e['severity']}")
        print(f"     score    : {e['score']}")
    print(f"{'='*58}")
    print("\n✅  API endpoint test complete.")
