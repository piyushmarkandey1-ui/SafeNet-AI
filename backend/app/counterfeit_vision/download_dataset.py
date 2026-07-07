"""
SafeNet AI — Counterfeit Vision: Dataset Downloader

⚠️  DATASET ACCESS NOTE:
=======================
This module is designed to work with the following Kaggle dataset:

    Title:  "Fake Currency Detection" (Indian Rupee notes, real vs fake)
    URL:    https://www.kaggle.com/datasets/hamzamansoor110/fake-currency-detection
    Author: Hamza Mansoor (Kaggle user hamzamansoor110)
    Format: Directory tree: real/<denomination>/*.jpg, fake/<denomination>/*.jpg

    ALTERNATIVE (larger, more comprehensive):
    Title:  "Indian Currency Note Dataset"
    URL:    https://www.kaggle.com/datasets/vikasnain/indian-currency-note-dataset

I CANNOT automatically download this dataset because:
  1. Kaggle requires authentication (API key or browser login).
  2. Direct programmatic access without a key would violate Kaggle ToS.

Manual download steps:
  1. Install Kaggle CLI:   pip install kaggle
  2. Place your API key at ~/.kaggle/kaggle.json  (from kaggle.com → Account → API)
  3. Run one of:
       kaggle datasets download -d hamzamansoor110/fake-currency-detection -p data/raw/currency --unzip
     OR use the Kaggle web UI to download the ZIP and extract to:
       data/raw/currency/
         real/
           100/  500/  2000/  ...
         fake/
           100/  500/  2000/  ...

If the exact dataset structure differs, set DATASET_ROOT env var or pass --data-dir.

This script will:
  - Verify the expected folder layout.
  - Fall back to generating a tiny SYNTHETIC dataset for smoke-testing the
    pipeline when no real data is present.
"""

import os
import sys
import argparse
import random
from pathlib import Path

# ⚠️  SYNTHETIC DATA — Not derived from real incidents or persons.
DENOMINATIONS = ["10", "20", "50", "100", "200", "500", "2000"]
CLASSES = ["real", "fake"]

DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "currency"


def verify_layout(data_dir: Path) -> dict:
    """
    Checks that the expected real/fake/<denomination> tree exists and counts images.

    Args:
        data_dir: Root of the currency dataset.

    Returns:
        dict with keys 'valid' (bool), 'counts' (dict), 'missing' (list).
    """
    counts = {}
    missing = []

    for cls in CLASSES:
        cls_dir = data_dir / cls
        if not cls_dir.exists():
            missing.append(str(cls_dir))
            continue
        for denom in DENOMINATIONS:
            denom_dir = cls_dir / denom
            if denom_dir.exists():
                imgs = list(denom_dir.glob("*.jpg")) + list(denom_dir.glob("*.png"))
                counts[f"{cls}/{denom}"] = len(imgs)

    return {
        "valid": len(missing) == 0 and len(counts) > 0,
        "counts": counts,
        "missing": missing,
    }


def generate_synthetic_dataset(data_dir: Path, n_per_class: int = 30) -> None:
    """
    Generates a minimal SYNTHETIC dataset for pipeline smoke-testing.

    Creates solid-colour JPEG images (real=green-tinted, fake=red-tinted)
    so the full train → validate → export pipeline can run without real data.

    Args:
        data_dir: Root directory where the synthetic dataset will be written.
        n_per_class: Number of images per (class, denomination) combination.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
    except ImportError:
        print("Pillow + numpy required: pip install pillow numpy")
        sys.exit(1)

    print(f"\n⚠️  Generating SYNTHETIC dataset at {data_dir} ({n_per_class} imgs per class/denom)")
    print("   This data is NOT real currency imagery. For training only.\n")

    rng = random.Random(42)

    for cls in CLASSES:
        for denom in DENOMINATIONS:
            out_dir = data_dir / cls / denom
            out_dir.mkdir(parents=True, exist_ok=True)

            for i in range(n_per_class):
                # Real notes: green base; Fake: red base + slight noise
                if cls == "real":
                    r, g, b = rng.randint(20, 60), rng.randint(100, 160), rng.randint(40, 90)
                else:
                    r, g, b = rng.randint(120, 180), rng.randint(20, 60), rng.randint(20, 60)

                img_arr = np.full((224, 224, 3), [r, g, b], dtype=np.uint8)
                # Add per-image noise so each sample is unique
                noise = np.random.randint(-15, 15, img_arr.shape, dtype=np.int16)
                img_arr = np.clip(img_arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)

                img = Image.fromarray(img_arr, "RGB")
                draw = ImageDraw.Draw(img)
                draw.text((10, 10), f"₹{denom}", fill=(255, 255, 200))
                draw.text((10, 30), f"SYNTHETIC-{cls.upper()}", fill=(200, 200, 200))
                draw.text((10, 50), f"img_{i:03d}", fill=(160, 160, 160))

                img.save(out_dir / f"SYNTHETIC_{cls}_{denom}_{i:03d}.jpg", quality=85)

    print(f"✅  Synthetic dataset written. Total images: {len(CLASSES) * len(DENOMINATIONS) * n_per_class}")


def main() -> None:
    """Entry point for the dataset downloader / verifier."""
    parser = argparse.ArgumentParser(description="SafeNet — Currency Dataset Setup")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR),
                        help="Root directory for the currency dataset.")
    parser.add_argument("--synthetic", action="store_true",
                        help="Force generation of synthetic data even if real data exists.")
    parser.add_argument("--n-per-class", type=int, default=30,
                        help="Images per (class, denomination) in synthetic mode (default: 30).")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    if args.synthetic:
        generate_synthetic_dataset(data_dir, args.n_per_class)
        return

    print(f"\n🔍  Verifying dataset at: {data_dir}")
    result = verify_layout(data_dir)

    if result["valid"]:
        print("✅  Real dataset detected.")
        total = sum(result["counts"].values())
        for k, v in sorted(result["counts"].items()):
            print(f"   {k}: {v} images")
        print(f"   Total: {total} images")
    else:
        print("❌  Real dataset NOT found.")
        if result["missing"]:
            print("   Missing directories:")
            for m in result["missing"]:
                print(f"     {m}")
        print("\n📋  Manual download instructions:")
        print("   kaggle datasets download -d hamzamansoor110/fake-currency-detection \\")
        print(f"       -p {data_dir} --unzip")
        print("\n   Falling back to SYNTHETIC data for smoke-testing...")
        generate_synthetic_dataset(data_dir, args.n_per_class)


if __name__ == "__main__":
    main()
