"""
# ⚠️  SYNTHETIC DATA — Not derived from real incidents or persons.

SafeNet AI — Counterfeit Vision: Grad-CAM Smoke Test

Runs inference on two synthetic notes (fake + real) and saves
the Grad-CAM overlay PNG for visual inspection.
"""
import sys
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.counterfeit_vision.inference import check_note


def test_image(img_path: Path, label: str) -> dict:
    print(f"\n{'='*55}")
    print(f"  Image : {img_path.name}  [{label}]")
    print(f"{'='*55}")

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    result = check_note(img_bytes)

    print(f"  is_fake      : {result['is_fake']}")
    print(f"  auth_class   : {result['auth_class']}")
    print(f"  confidence   : {result['confidence']:.4f}")
    print(f"  denomination : {result['denomination']}")
    print(f"  gradcam_len  : {len(result['gradcam_overlay'])} chars (base64 PNG)")

    # Save overlay
    out_path = Path(__file__).parent / f"gradcam_{label}.png"
    overlay_bytes = base64.b64decode(result["gradcam_overlay"])
    out_path.write_bytes(overlay_bytes)
    print(f"  Overlay saved: {out_path}")

    return result


if __name__ == "__main__":
    data_root = Path(__file__).parent.parent.parent / "data" / "raw" / "currency"

    fake_imgs = list((data_root / "fake" / "500").glob("*.jpg"))
    real_imgs = list((data_root / "real" / "100").glob("*.jpg"))

    if not fake_imgs or not real_imgs:
        print("Synthetic data not found. Run: python -m app.counterfeit_vision.download_dataset --synthetic")
        sys.exit(1)

    r_fake = test_image(fake_imgs[0], "fake_500")
    r_real = test_image(real_imgs[0], "real_100")

    print("\n" + "="*55)
    print("  SUMMARY")
    print("="*55)
    print(f"  Fake ₹500  → is_fake={r_fake['is_fake']:5}  conf={r_fake['confidence']:.3f}")
    print(f"  Real ₹100  → is_fake={r_real['is_fake']:5}  conf={r_real['confidence']:.3f}")
    print("="*55)

    correct = int(r_fake["is_fake"]) + int(not r_real["is_fake"])
    print(f"\n  Correct predictions: {correct}/2")
    print("\n✅  Grad-CAM smoke test complete.")
