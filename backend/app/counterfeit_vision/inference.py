"""
SafeNet AI — Counterfeit Vision: Inference + Grad-CAM

Public API:
  check_note(image_bytes: bytes) -> NoteResult

Returns:
  {
    is_fake:          bool,
    confidence:       float (0–1),
    denomination:     str (e.g. "₹500"),
    gradcam_overlay:  str (base64-encoded PNG of the Grad-CAM heatmap)
  }

Grad-CAM implementation:
  Hooks the gradient of the authentication logit w.r.t. the final
  convolutional feature map (features[-1]) of MobileNetV3-Small.
  The resulting heatmap highlights regions the model found suspicious
  (e.g. security thread area, watermark zone, serial number).

Model loading:
  Loads model_weights.pth from the models/ subdirectory at startup.
  Falls back to a randomly-initialised model if weights are not found
  (so the API endpoint stays alive during development).
"""

import io
import os
import json
import base64
import logging
from pathlib import Path
from typing import Optional

import numpy as np
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torchvision import transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    
from PIL import Image

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
_MODULE_DIR = Path(__file__).parent
MODEL_DIR = _MODULE_DIR / "models"
WEIGHTS_PATH = MODEL_DIR / "model_weights.pth"
LABEL_MAP_PATH = MODEL_DIR / "label_map.json"

DENOMINATIONS = ["10", "20", "50", "100", "200", "500", "2000"]
AUTH_CLASSES = ["fake", "real"]


# ──────────────────────────────────────────────────────────────────────────────
# Lazy-loaded model singleton
# ──────────────────────────────────────────────────────────────────────────────
_model = None
_device = None
_label_map: Optional[dict] = None


def _load_label_map() -> dict:
    """Loads label map from JSON, or returns defaults if file missing."""
    if LABEL_MAP_PATH.exists():
        with open(LABEL_MAP_PATH) as f:
            return json.load(f)
    return {"auth_classes": AUTH_CLASSES, "denomination_classes": DENOMINATIONS}


def _build_model():
    """
    Builds CurrencyClassifier. Imported inline to avoid circular dep with train.py.

    Returns:
        CurrencyClassifier instance (not loaded onto device yet).
    """
    from app.counterfeit_vision.train import CurrencyClassifier
    return CurrencyClassifier(num_denominations=len(DENOMINATIONS), pretrained=False)


def get_model():
    """
    Lazily loads the model and moves it to the best available device.

    Returns:
        (model, device, label_map)
    """
    global _model, _device, _label_map

    if _model is not None:
        return _model, _device, _label_map

    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch is not available. Running in degraded mode.")

    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _label_map = _load_label_map()

    model = _build_model()

    if WEIGHTS_PATH.exists():
        try:
            state = torch.load(WEIGHTS_PATH, map_location=_device, weights_only=True)
            model.load_state_dict(state)
            logger.info(f"Loaded weights from {WEIGHTS_PATH}")
        except Exception as e:
            logger.warning(f"Could not load weights ({e}). Using untrained model.")
    else:
        logger.warning(
            f"No weights at {WEIGHTS_PATH}. "
            "Run `python -m app.counterfeit_vision.train` to train the model. "
            "Using untrained model — predictions will be random."
        )

    model.to(_device)
    model.eval()
    _model = model
    return _model, _device, _label_map


# ──────────────────────────────────────────────────────────────────────────────
# Preprocessing
# ──────────────────────────────────────────────────────────────────────────────

def _get_preprocess():
    if not TORCH_AVAILABLE: return None
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

def _bytes_to_tensor(image_bytes: bytes):
    """
    Decodes raw image bytes to a preprocessed tensor and the original PIL image.

    Args:
        image_bytes: Raw bytes of JPEG/PNG/etc image.

    Returns:
        (tensor [1, 3, 224, 224], pil_image)
    """
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _get_preprocess()(pil_img).unsqueeze(0)  # [1, 3, 224, 224]
    return tensor, pil_img


# ──────────────────────────────────────────────────────────────────────────────
# Grad-CAM
# ──────────────────────────────────────────────────────────────────────────────
def _compute_gradcam(
    model,
    input_tensor,
    auth_class_idx: int,
    device,
) -> np.ndarray:
    """
    Computes Grad-CAM heatmap for the authenticity classification decision.

    Hooks the last convolutional block of MobileNetV3-Small (features[-1]).
    Highlights regions that pushed the model toward the predicted class.

    Args:
        model:           CurrencyClassifier instance.
        input_tensor:    Preprocessed image tensor [1, 3, 224, 224].
        auth_class_idx:  Index of the predicted authenticity class (0=fake, 1=real).
        device:          Torch device.

    Returns:
        numpy.ndarray of shape (224, 224) with values in [0, 1].
    """
    gradients = []
    activations = []

    def _save_grad(grad) -> None:
        gradients.append(grad.detach())

    def _save_activation(module, inp, out) -> None:
        activations.append(out.detach())

    # Hook onto the last convolutional block
    target_layer = model.features[-1]
    forward_hook = target_layer.register_forward_hook(_save_activation)

    # Forward pass with gradients enabled
    input_tensor = input_tensor.to(device).requires_grad_(True)
    model.zero_grad()
    auth_logits, _ = model(input_tensor)

    # Backprop only for the predicted class score
    score = auth_logits[0, auth_class_idx]
    score.backward()

    # Retrieve gradient w.r.t. feature map via autograd
    # (The feature map is in activations; we get grad via input grad chain)
    forward_hook.remove()

    if not activations:
        return np.zeros((224, 224), dtype=np.float32)

    feat_map = activations[0]          # [1, C, H, W]
    grad_map = input_tensor.grad       # [1, 3, 224, 224] — not ideal, use proper hook

    # Better: hook the gradient flowing back through the target layer
    # We recompute using a gradient hook on the activation itself
    activations.clear()
    gradients.clear()

    # Register both hooks properly this time
    fwd_hook = target_layer.register_forward_hook(
        lambda m, inp, out: activations.append(out)
    )
    bwd_hook = target_layer.register_full_backward_hook(
        lambda m, grad_in, grad_out: gradients.append(grad_out[0].detach())
    )

    inp2 = input_tensor.detach().requires_grad_(True)
    model.zero_grad()
    auth_logits2, _ = model(inp2)
    auth_logits2[0, auth_class_idx].backward()

    fwd_hook.remove()
    bwd_hook.remove()

    if not activations or not gradients:
        return np.zeros((224, 224), dtype=np.float32)

    act = activations[0].detach()      # [1, C, H, W]
    grad = gradients[0]                # [1, C, H, W]

    # Global average pool the gradients → channel weights
    weights = grad.mean(dim=(2, 3), keepdim=True)   # [1, C, 1, 1]
    cam = (weights * act).sum(dim=1, keepdim=True)  # [1, 1, H, W]
    cam = F.relu(cam)

    # Upsample to input resolution
    cam = F.interpolate(cam, size=(224, 224), mode="bilinear", align_corners=False)
    cam = cam.squeeze().cpu().numpy()

    # Normalise to [0, 1]
    cam_min, cam_max = cam.min(), cam.max()
    if cam_max > cam_min:
        cam = (cam - cam_min) / (cam_max - cam_min)
    else:
        cam = np.zeros_like(cam)

    return cam.astype(np.float32)


def _overlay_heatmap(pil_image: Image.Image, cam: np.ndarray) -> str:
    """
    Blends Grad-CAM heatmap over the original image and returns a base64 PNG.

    Uses a jet-like colormap (pure numpy, no matplotlib dependency).

    Args:
        pil_image: Original PIL image.
        cam:       Grad-CAM array (224, 224), values in [0, 1].

    Returns:
        Base64-encoded PNG string (data URI ready).
    """
    import cv2

    # Resize original to 224×224 for overlay
    img_arr = np.array(pil_image.resize((224, 224))).astype(np.uint8)

    # Jet colormap via cv2
    heatmap_uint8 = (cam * 255).astype(np.uint8)
    heatmap_bgr = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    heatmap_rgb = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)

    # Alpha blend: 55% original + 45% heatmap
    overlay = (0.55 * img_arr + 0.45 * heatmap_rgb).clip(0, 255).astype(np.uint8)

    # Encode to PNG
    overlay_pil = Image.fromarray(overlay)
    buf = io.BytesIO()
    overlay_pil.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────
def check_note(image_bytes: bytes) -> dict:
    """
    Classifies a currency note image as real or fake, identifies denomination,
    and generates a Grad-CAM overlay showing the decision-relevant regions.

    Args:
        image_bytes: Raw bytes of the uploaded image (JPEG/PNG/WEBP).

    Returns:
        dict with keys:
          is_fake (bool):           True if the model predicts counterfeit.
          confidence (float):       Softmax probability of the predicted auth class.
          denomination (str):       Predicted denomination, e.g. "₹500".
          gradcam_overlay (str):    Base64-encoded PNG of the Grad-CAM heatmap.
          auth_class (str):         "fake" or "real".
          denomination_raw (str):   Numeric string, e.g. "500".
    """
    if not TORCH_AVAILABLE:
        # Graceful fallback when running in serverless environments without Torch
        import time
        time.sleep(0.5)
        return {
            "is_fake": False,
            "confidence": 0.85,
            "denomination": "₹500",
            "denomination_raw": "500",
            "auth_class": "real",
            "gradcam_overlay": "",
            "recommendation": "Mock response: Vercel serverless environment does not support PyTorch.",
        }

    model, device, label_map = get_model()

    input_tensor, pil_image = _bytes_to_tensor(image_bytes)

    with torch.no_grad():
        auth_logits, denom_logits = model(input_tensor.to(device))
        auth_probs = F.softmax(auth_logits, dim=1)[0]
        denom_probs = F.softmax(denom_logits, dim=1)[0]

    auth_idx = int(auth_probs.argmax().item())
    denom_idx = int(denom_probs.argmax().item())

    auth_classes = label_map.get("auth_classes", AUTH_CLASSES)
    denom_classes = label_map.get("denomination_classes", DENOMINATIONS)

    auth_class = auth_classes[auth_idx] if auth_idx < len(auth_classes) else "unknown"
    denom_raw = denom_classes[denom_idx] if denom_idx < len(denom_classes) else "unknown"
    confidence = float(auth_probs[auth_idx].item())

    # Grad-CAM (computed outside no_grad to enable backprop)
    cam = _compute_gradcam(model, input_tensor, auth_idx, device)
    gradcam_b64 = _overlay_heatmap(pil_image, cam)

    return {
        "is_fake": auth_class == "fake",
        "confidence": round(confidence, 4),
        "denomination": f"₹{denom_raw}",
        "denomination_raw": denom_raw,
        "auth_class": auth_class,
        "gradcam_overlay": gradcam_b64,
    }
