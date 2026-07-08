"""
SafeNet AI — Counterfeit Vision: Training Script

Fine-tunes MobileNetV3-Small (from torchvision pretrained weights) on
a binary real/fake + denomination classification task.

Architecture:
  - Backbone:  MobileNetV3-Small (ImageNet pretrained, torchvision)
  - Head:      Two parallel linear heads sharing the same backbone:
                 • authenticity_head  → 2 classes (real / fake)
                 • denomination_head  → N classes (₹10, 20, 50, 100, 200, 500, 2000)
  - Loss:       Sum of CrossEntropy losses from both heads.

Device:
  - Auto-detects CUDA (NVIDIA) → ROCm (AMD) → CPU in that priority order.
  - On this machine: CPU-only (torch 2.12.1+cpu).
  - Training on the synthetic 30-img/class subset completes in ~2–5 min on CPU.

Exports:
  - model_weights.pth  (PyTorch state dict — for inference.py)
  - model.onnx         (ONNX — for on-device deployment / ONNX Runtime)

Usage:
  python -m app.counterfeit_vision.train [--data-dir PATH] [--epochs N]
                                         [--batch-size N] [--subset-fraction F]
"""

import os
import sys
import argparse
import json
import time
import datetime
import threading
import subprocess
from pathlib import Path
from typing import Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, models, transforms
from torchvision.models import MobileNet_V3_Small_Weights

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
_MODULE_DIR = Path(__file__).parent
DEFAULT_DATA_DIR = _MODULE_DIR.parent.parent.parent / "data" / "raw" / "currency"
DEFAULT_MODEL_DIR = _MODULE_DIR / "models"

DENOMINATIONS = ["10", "20", "50", "100", "200", "500", "2000"]
AUTH_CLASSES = ["fake", "real"]      # alphabetical — matches ImageFolder sort order for class subfolders


# ──────────────────────────────────────────────────────────────────────────────
# Device selection (CUDA → ROCm → CPU)
# ──────────────────────────────────────────────────────────────────────────────
def get_device() -> torch.device:
    """
    Returns the compute device. Strictly enforces GPU for the AMD notebook environment.
    """
    if not torch.cuda.is_available():
        print("[FATAL] No GPU detected. This script is strictly configured for the AMD GPU notebook.")
        print("Aborting to save shared team time.")
        sys.exit(1)
        
    name = torch.cuda.get_device_name(0)
    backend = "ROCm/HIP" if "AMD" in name or "Radeon" in name else "CUDA"
    print(f"🖥️  GPU detected [{backend}]: {name}")
    return torch.device("cuda")

# ──────────────────────────────────────────────────────────────────────────────
# ROCm Usage Logging
# ──────────────────────────────────────────────────────────────────────────────
def log_rocm_smi(stage: str, docs_dir: Path):
    """Logs rocm-smi output for hackathon usage proof."""
    docs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = docs_dir / f"rocm_{stage}_{timestamp}.log"
    
    try:
        # Will fail gracefully if rocm-smi is not installed
        res = subprocess.run(["rocm-smi"], capture_output=True, text=True, check=False)
        with open(log_path, "w") as f:
            f.write(res.stdout if res.stdout else f"rocm-smi failed or not found: {res.stderr}")
    except Exception as e:
        with open(log_path, "w") as f:
            f.write(f"Failed to execute rocm-smi: {e}")

class RocmLoggerThread(threading.Thread):
    def __init__(self, docs_dir: Path, interval_minutes: float):
        super().__init__(daemon=True)
        self.docs_dir = docs_dir
        self.interval = interval_minutes * 60
        self.stop_event = threading.Event()
        
    def run(self):
        while not self.stop_event.wait(self.interval):
            log_rocm_smi("mid", self.docs_dir)
            
    def stop(self):
        self.stop_event.set()


# ──────────────────────────────────────────────────────────────────────────────
# Dataset helpers
# ──────────────────────────────────────────────────────────────────────────────
def build_transforms(augment: bool = True) -> transforms.Compose:
    """
    Returns an image transform pipeline.

    Args:
        augment: If True, applies random flips/jitter (for training set).

    Returns:
        torchvision.transforms.Compose
    """
    base = [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ]
    if augment:
        base = [
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
        ] + base
    return transforms.Compose(base)


class FlatCurrencyDataset(torch.utils.data.Dataset):
    """
    Wraps a two-level directory tree (real/<denom>/ and fake/<denom>/)
    and exposes each image with two integer labels:
      - auth_label:  0=fake, 1=real
      - denom_label: index into DENOMINATIONS list

    Args:
        root:      Path to the dataset root (contains 'real/' and 'fake/').
        transform: Torchvision transform applied to each PIL image.
        subset_fraction: Float 0<f<=1.0 — randomly keep this fraction for fast runs.
    """

    def __init__(self, root: Path, transform, subset_fraction: float = 1.0):
        from PIL import Image

        self.transform = transform
        self.samples: list[Tuple[Path, int, int]] = []  # (path, auth_label, denom_label)
        self._Image = Image

        denom_to_idx = {d: i for i, d in enumerate(DENOMINATIONS)}

        for auth_idx, auth_cls in enumerate(["fake", "real"]):
            cls_dir = root / auth_cls
            if not cls_dir.exists():
                continue
            for denom in DENOMINATIONS:
                denom_dir = cls_dir / denom
                if not denom_dir.exists():
                    continue
                for ext in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"):
                    for img_path in denom_dir.glob(ext):
                        self.samples.append((img_path, auth_idx, denom_to_idx[denom]))

        if subset_fraction < 1.0:
            import random
            rng = random.Random(42)
            k = max(1, int(len(self.samples) * subset_fraction))
            self.samples = rng.sample(self.samples, k)

        print(f"   Dataset loaded: {len(self.samples)} images (subset={subset_fraction:.0%})")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, auth_label, denom_label = self.samples[idx]
        img = self._Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, auth_label, denom_label


# ──────────────────────────────────────────────────────────────────────────────
# Model
# ──────────────────────────────────────────────────────────────────────────────
class CurrencyClassifier(nn.Module):
    """
    Dual-head MobileNetV3-Small classifier.

    Shared backbone → two parallel linear heads:
      - authenticity_head: binary (fake=0, real=1)
      - denomination_head: multi-class over DENOMINATIONS

    Args:
        num_denominations: Number of denomination classes.
        pretrained: Load ImageNet weights for the backbone.
    """

    def __init__(self, num_denominations: int = 7, pretrained: bool = True):
        super().__init__()
        weights = MobileNet_V3_Small_Weights.IMAGENET1K_V1 if pretrained else None
        backbone = models.mobilenet_v3_small(weights=weights)

        # Extract feature extractor (all layers except the final classifier)
        self.features = backbone.features
        self.avgpool = backbone.avgpool

        # MobileNetV3-Small final feature dim is 576
        in_features = 576

        self.authenticity_head = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.Hardswish(),
            nn.Dropout(p=0.2),
            nn.Linear(128, 2),
        )
        self.denomination_head = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.Hardswish(),
            nn.Dropout(p=0.2),
            nn.Linear(128, num_denominations),
        )

    def forward(self, x: torch.Tensor):
        """
        Args:
            x: Image tensor [B, 3, 224, 224]

        Returns:
            Tuple of (auth_logits [B, 2], denom_logits [B, N])
        """
        feat = self.features(x)
        feat = self.avgpool(feat)
        feat = feat.flatten(1)
        return self.authenticity_head(feat), self.denomination_head(feat)


# ──────────────────────────────────────────────────────────────────────────────
# Training loop
# ──────────────────────────────────────────────────────────────────────────────
def train(
    data_dir: Path,
    model_dir: Path,
    epochs: int = 10,
    batch_size: int = 16,
    lr: float = 1e-3,
    val_split: float = 0.2,
    subset_fraction: float = 1.0,
    device: torch.device = None,
    max_minutes: float = 60.0,
    dry_run: bool = False,
    log_interval_minutes: float = 10.0,
) -> dict:
    """
    Runs the full training loop and saves model artifacts.

    Args:
        data_dir:         Root of the real/fake/<denom>/ dataset.
        model_dir:        Where to save model_weights.pth, model.onnx, label_map.json.
        epochs:           Training epochs.
        batch_size:       Mini-batch size.
        lr:               Initial learning rate for AdamW.
        val_split:        Fraction of data reserved for validation.
        subset_fraction:  Use only this fraction of data (for fast smoke tests).
        device:           Torch device. Auto-detected if None.
        max_minutes:      Stop training gracefully after this many minutes.
        dry_run:          Run exactly 1 mini-batch to sanity-check pipeline.
        log_interval_minutes: Frequency to poll rocm-smi.

    Returns:
        dict with 'val_auth_acc', 'val_denom_acc', 'best_epoch'.
    """
    if device is None:
        device = get_device()

    model_dir.mkdir(parents=True, exist_ok=True)

    # ── Dataset ──────────────────────────────────────────────────────────────
    print("\n📂  Loading dataset...")
    full_ds = FlatCurrencyDataset(data_dir, build_transforms(augment=True), subset_fraction)

    if len(full_ds) == 0:
        print("❌  No images found. Run download_dataset.py first.")
        sys.exit(1)

    n_val = max(1, int(len(full_ds) * val_split))
    n_train = len(full_ds) - n_val
    train_ds, val_ds = random_split(full_ds, [n_train, n_val],
                                    generator=torch.Generator().manual_seed(42))

    # Use faster non-augmented transforms for val
    val_ds.dataset.transform = build_transforms(augment=False)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              num_workers=0, pin_memory=False)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                            num_workers=0, pin_memory=False)

    print(f"   Train: {n_train} | Val: {n_val}")

    # ── Model ─────────────────────────────────────────────────────────────────
    model = CurrencyClassifier(num_denominations=len(DENOMINATIONS), pretrained=True).to(device)

    auth_criterion = nn.CrossEntropyLoss()
    denom_criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # ── Loop ──────────────────────────────────────────────────────────────────
    best_val_acc = 0.0
    best_epoch = 0
    results = {}

    print(f"\n🏋️  Training for {epochs} epochs on {device}...\n")
    print(f"⏱️  Budget: This run is configured to use at most {max_minutes} minutes of your team's shared GPU time.")
    if dry_run:
        print("⚠️  DRY RUN MODE: Will only process 1 mini-batch to verify pipeline.")
        
    docs_dir = _MODULE_DIR.parent.parent.parent / "docs" / "amd_usage"
    log_rocm_smi("before", docs_dir)
    logger_thread = RocmLoggerThread(docs_dir, log_interval_minutes)
    logger_thread.start()
    
    global_start_t = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        t0 = time.time()

        for i, (imgs, auth_labels, denom_labels) in enumerate(train_loader):
            if dry_run and i > 0:
                break
            imgs = imgs.to(device)
            auth_labels = auth_labels.to(device)
            denom_labels = denom_labels.to(device)

            optimizer.zero_grad()
            auth_logits, denom_logits = model(imgs)
            loss = auth_criterion(auth_logits, auth_labels) + \
                   denom_criterion(denom_logits, denom_labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
            if (time.time() - global_start_t) / 60.0 > max_minutes:
                print("\n⚠️  Time limit approached! Breaking train loop early to save checkpoint.")
                break

        scheduler.step()

        # ── Validation ────────────────────────────────────────────────────────
        model.eval()
        auth_correct = denom_correct = total = 0

        with torch.no_grad():
            for i, (imgs, auth_labels, denom_labels) in enumerate(val_loader):
                if dry_run and i > 0:
                    break
                imgs = imgs.to(device)
                auth_labels = auth_labels.to(device)
                denom_labels = denom_labels.to(device)

                auth_logits, denom_logits = model(imgs)
                auth_correct += (auth_logits.argmax(1) == auth_labels).sum().item()
                denom_correct += (denom_logits.argmax(1) == denom_labels).sum().item()
                total += len(imgs)

        val_auth_acc = auth_correct / total if total else 0
        val_denom_acc = denom_correct / total if total else 0
        elapsed = time.time() - t0

        print(f"  Epoch {epoch:3d}/{epochs}  "
              f"loss={train_loss/max(len(train_loader),1):.4f}  "
              f"auth_acc={val_auth_acc:.3f}  "
              f"denom_acc={val_denom_acc:.3f}  "
              f"({elapsed:.1f}s)")

        combined_acc = (val_auth_acc + val_denom_acc) / 2
        if combined_acc > best_val_acc:
            best_val_acc = combined_acc
            best_epoch = epoch
            torch.save(model.state_dict(), model_dir / "model_weights.pth")

        results = {
            "val_auth_acc": round(val_auth_acc, 4),
            "val_denom_acc": round(val_denom_acc, 4),
            "best_epoch": best_epoch,
        }
        
        if (time.time() - global_start_t) / 60.0 > max_minutes:
            print("\n⚠️  Time limit approached! Halting training completely.")
            break
            
        if dry_run:
            print("\n⚠️  DRY RUN MODE: Halting after 1 epoch.")
            break
            
    logger_thread.stop()
    log_rocm_smi("after", docs_dir)

    # ── ONNX Export ───────────────────────────────────────────────────────────
    print("\n📦  Exporting to ONNX...")
    model.load_state_dict(torch.load(model_dir / "model_weights.pth", map_location=device))
    model.eval()

    dummy_input = torch.randn(1, 3, 224, 224).to(device)
    onnx_path = model_dir / "model.onnx"

    # Use legacy TorchScript-based exporter (dynamo=False) for compatibility
    # with torch 2.x where the dynamo exporter requires onnxscript wiring.
    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        input_names=["image"],
        output_names=["auth_logits", "denom_logits"],
        dynamic_axes={"image": {0: "batch_size"},
                      "auth_logits": {0: "batch_size"},
                      "denom_logits": {0: "batch_size"}},
        opset_version=17,
        dynamo=False,
    )
    print(f"   Saved: {onnx_path}")

    # ── Label map ─────────────────────────────────────────────────────────────
    label_map = {
        "auth_classes": AUTH_CLASSES,
        "denomination_classes": DENOMINATIONS,
    }
    label_map_path = model_dir / "label_map.json"
    with open(label_map_path, "w") as f:
        json.dump(label_map, f, indent=2)
    print(f"   Saved: {label_map_path}")

    print(f"\n✅  Training complete. Best epoch: {best_epoch}  "
          f"auth_acc={results.get('val_auth_acc', 0):.3f}  "
          f"denom_acc={results.get('val_denom_acc', 0):.3f}")

    duration_s = time.time() - global_start_t
    summary = {
        "start_time": datetime.datetime.fromtimestamp(global_start_t).isoformat(),
        "end_time": datetime.datetime.now().isoformat(),
        "duration_seconds": round(duration_s, 2),
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "final_epoch": results.get("best_epoch", 0),
        "final_val_auth_acc": results.get("val_auth_acc", 0),
        "final_val_denom_acc": results.get("val_denom_acc", 0),
        "output_model": str(onnx_path.resolve())
    }
    summary_path = docs_dir / "training_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\n" + "="*60)
    print("🚀  HARDWARE LOGGING & ARTIFACTS SAVED")
    print("="*60)
    print("Please download the following files from this AMD notebook environment")
    print("back to your local repository before terminating the session:")
    print(f" 1. Model: {onnx_path.resolve()}")
    print(f" 2. Label Map: {model_dir.resolve() / 'label_map.json'}")
    print(f" 3. AMD Logs: All files in {docs_dir.resolve()}")
    print("="*60)

    return results


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    """CLI wrapper for train()."""
    parser = argparse.ArgumentParser(description="SafeNet — Currency Classifier Training")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--model-dir", default=str(DEFAULT_MODEL_DIR))
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--subset-fraction", type=float, default=1.0,
                        help="Use fraction of data (0–1). Use 0.3 for a fast smoke test.")
    parser.add_argument("--max_minutes", type=float, default=60.0)
    parser.add_argument("--log_interval_minutes", type=float, default=10.0)
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    train(
        data_dir=Path(args.data_dir),
        model_dir=Path(args.model_dir),
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        subset_fraction=args.subset_fraction,
        max_minutes=args.max_minutes,
        dry_run=args.dry_run,
        log_interval_minutes=args.log_interval_minutes,
    )


if __name__ == "__main__":
    main()
