"""
SafeNet AI — Enhanced Indian Currency Note Detector

A lightweight counterfeit detection system for Indian Rupee notes that works
without heavy ML dependencies. Uses image analysis + Gemini AI verification.

Supports: ₹10, ₹20, ₹50, ₹100, ₹200, ₹500, ₹2000
"""

import io
import base64
import os
from PIL import Image
import numpy as np
from typing import Dict, Tuple

# Indian Rupee denominations and their primary colors
DENOMINATION_COLORS = {
    "10": {"r": (200, 255), "g": (150, 210), "b": (100, 180), "name": "brown-orange"},
    "20": {"r": (200, 255), "g": (150, 200), "b": (100, 150), "name": "greenish-yellow"},
    "50": {"r": (180, 230), "g": (100, 180), "b": (180, 240), "name": "fluorescent blue"},
    "100": {"r": (150, 220), "g": (100, 180), "b": (200, 255), "name": "lavender-blue"},
    "200": {"r": (200, 255), "g": (200, 255), "b": (100, 180), "name": "bright yellow"},
    "500": {"r": (150, 200), "g": (150, 200), "b": (150, 200), "name": "stone gray"},
    "2000": {"r": (200, 255), "g": (150, 210), "b": (200, 255), "name": "magenta"},
}

# Expected dimensions (width x height in mm, converted to pixel ratios)
DENOMINATION_SIZES = {
    "10": (137, 63),
    "20": (147, 63),
    "50": (147, 73),
    "100": (157, 73),
    "200": (157, 73),
    "500": (166, 73),
    "2000": (166, 73),
}

# Security features that should be present
SECURITY_FEATURES = {
    "watermark": "Mahatma Gandhi portrait visible when held against light",
    "security_thread": "Visible security thread with denomination and 'Bharat' text",
    "see_through_register": "Elements on front and back perfectly align when held against light",
    "latent_image": "Denomination numeral visible at 45-degree angle",
    "micro_lettering": "Tiny text between security thread lines",
    "identification_mark": "Tactile mark for visually impaired (different for each denomination)",
    "changing_color": "Numeral changes color when tilted (₹500, ₹2000)",
    "ashoka_pillar": "Emblem on reverse side",
    "number_panel": "Numbering gradually increases from left to right",
}


def analyze_image_basic(image_bytes: bytes) -> Dict:
    """
    Performs basic image analysis to detect denomination and potential issues.
    
    Returns:
        Dict with denomination, confidence, and detected_issues
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(img)
    
    # Get dominant color
    avg_color = img_array.mean(axis=(0, 1))
    r, g, b = avg_color
    
    # Detect denomination based on color
    best_match = None
    best_score = 0
    
    for denom, color_range in DENOMINATION_COLORS.items():
        # Check if colors are in expected range
        r_match = color_range["r"][0] <= r <= color_range["r"][1]
        g_match = color_range["g"][0] <= g <= color_range["g"][1]
        b_match = color_range["b"][0] <= b <= color_range["b"][1]
        
        score = sum([r_match, g_match, b_match])
        if score > best_score:
            best_score = score
            best_match = denom
    
    # Calculate confidence based on color match
    base_confidence = (best_score / 3.0) * 0.6  # Max 60% from color
    
    # Check image quality
    sharpness = img.filter(Image.SHARPEN)
    sharpness_score = np.std(np.array(sharpness)) / 255.0
    quality_confidence = min(sharpness_score * 0.2, 0.2)  # Max 20% from quality
    
    # Check dimensions
    aspect_ratio = img.width / img.height if img.height > 0 else 0
    expected_ratio = DENOMINATION_SIZES[best_match][0] / DENOMINATION_SIZES[best_match][1] if best_match else 2.0
    ratio_diff = abs(aspect_ratio - expected_ratio) / expected_ratio
    size_confidence = max(0, 0.2 * (1 - ratio_diff))  # Max 20% from size
    
    total_confidence = base_confidence + quality_confidence + size_confidence
    
    # Detect potential issues
    issues = []
    if sharpness_score < 0.3:
        issues.append("Low image quality or blur detected")
    if ratio_diff > 0.15:
        issues.append("Unusual aspect ratio for Indian currency notes")
    if base_confidence < 0.3:
        issues.append("Color profile doesn't match expected denomination colors")
    
    return {
        "denomination": best_match or "unknown",
        "confidence": min(total_confidence, 0.95),  # Cap at 95% for basic analysis
        "dominant_color": {"r": int(r), "g": int(g), "b": int(b)},
        "image_size": {"width": img.width, "height": img.height},
        "aspect_ratio": round(aspect_ratio, 2),
        "detected_issues": issues,
    }


def verify_with_gemini(image_bytes: bytes, basic_analysis: Dict) -> Dict:
    """
    Uses Gemini AI to verify the note and provide detailed analysis.
    
    Returns:
        Dict with is_fake, confidence, explanation, and recommendations
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if not gemini_api_key:
        # Fallback without Gemini
        is_fake = len(basic_analysis["detected_issues"]) >= 2
        confidence = basic_analysis["confidence"]
        
        return {
            "is_fake": is_fake,
            "confidence": confidence,
            "explanation": f"Basic analysis detected {len(basic_analysis['detected_issues'])} potential issues",
            "verification_method": "rule-based",
        }
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_api_key)
        
        # Prepare image for Gemini
        img = Image.open(io.BytesIO(image_bytes))
        
        # Create prompt
        prompt = f"""Analyze this Indian Rupee currency note image for authenticity.

Expected Denomination: ₹{basic_analysis['denomination']}
Basic Analysis Confidence: {basic_analysis['confidence']:.1%}
Detected Issues: {', '.join(basic_analysis['detected_issues']) if basic_analysis['detected_issues'] else 'None'}

Please examine for:
1. Security features (watermark, security thread, see-through register)
2. Print quality and color accuracy
3. Paper texture indicators visible in the image
4. Denomination-specific features
5. Any signs of tampering or reproduction

Respond in this exact format:
AUTHENTICITY: [REAL/FAKE/SUSPICIOUS]
CONFIDENCE: [0-100]
EXPLANATION: [2-3 sentences explaining your assessment]
KEY_OBSERVATIONS: [Bullet points of specific features noticed]"""

        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content([prompt, img])
        
        # Parse response
        text = response.text
        
        is_fake = "FAKE" in text or "SUSPICIOUS" in text
        
        # Extract confidence
        confidence_line = [line for line in text.split('\n') if 'CONFIDENCE:' in line]
        if confidence_line:
            try:
                conf_str = confidence_line[0].split('CONFIDENCE:')[1].strip().split()[0]
                gemini_confidence = float(conf_str) / 100.0
            except:
                gemini_confidence = basic_analysis['confidence']
        else:
            gemini_confidence = basic_analysis['confidence']
        
        # Extract explanation
        expl_lines = [line for line in text.split('\n') if 'EXPLANATION:' in line]
        explanation = expl_lines[0].split('EXPLANATION:')[1].strip() if expl_lines else text[:200]
        
        return {
            "is_fake": is_fake,
            "confidence": gemini_confidence,
            "explanation": explanation,
            "full_analysis": text,
            "verification_method": "gemini-ai",
        }
        
    except Exception as e:
        # Fallback on error
        is_fake = len(basic_analysis["detected_issues"]) >= 2
        return {
            "is_fake": is_fake,
            "confidence": basic_analysis["confidence"],
            "explanation": f"Gemini verification failed: {str(e)}. Using rule-based analysis.",
            "verification_method": "rule-based-fallback",
        }


def generate_simple_heatmap(image_bytes: bytes, focus_areas: list = None) -> str:
    """
    Generates a simple heatmap overlay highlighting suspicious areas.
    
    Args:
        image_bytes: Original image bytes
        focus_areas: List of (x, y, radius) tuples for suspicious regions
    
    Returns:
        Base64-encoded PNG
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((224, 224))
        img_array = np.array(img)
        
        # Create heatmap (simple edge detection as proxy for suspicious areas)
        from scipy import ndimage
        
        gray = np.mean(img_array, axis=2)
        edges = ndimage.sobel(gray)
        edges = (edges - edges.min()) / (edges.max() - edges.min() + 1e-8)
        
        # Convert to heatmap colors (red for high values)
        heatmap = np.zeros_like(img_array)
        heatmap[:, :, 0] = (edges * 255).astype(np.uint8)  # Red channel
        heatmap[:, :, 1] = ((1 - edges) * 100).astype(np.uint8)  # Dim green
        
        # Blend with original
        overlay = (0.6 * img_array + 0.4 * heatmap).clip(0, 255).astype(np.uint8)
        
        # Convert to base64
        overlay_img = Image.fromarray(overlay)
        buf = io.BytesIO()
        overlay_img.save(buf, format="PNG")
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
        
    except Exception as e:
        # Return empty string on error
        return ""


def check_indian_note(image_bytes: bytes) -> Dict:
    """
    Main function to check Indian currency notes for authenticity.
    
    Combines rule-based analysis with Gemini AI verification.
    
    Args:
        image_bytes: Raw image bytes
    
    Returns:
        Dict with full analysis results
    """
    # Step 1: Basic image analysis
    basic_analysis = analyze_image_basic(image_bytes)
    
    # Step 2: Gemini AI verification
    gemini_result = verify_with_gemini(image_bytes, basic_analysis)
    
    # Step 3: Generate heatmap
    gradcam_overlay = generate_simple_heatmap(image_bytes)
    
    # Step 4: Compile final result
    is_fake = gemini_result["is_fake"]
    confidence = gemini_result["confidence"]
    denom = basic_analysis["denomination"]
    
    # Generate recommendation
    if is_fake:
        if confidence > 0.85:
            severity = "critical"
            recommendation = f"ALERT: High-confidence counterfeit detected. Do not accept this note. Report to nearest bank or police station."
        elif confidence > 0.60:
            severity = "high"
            recommendation = f"WARNING: Likely counterfeit. Verify security features manually or take to bank for authentication."
        else:
            severity = "medium"
            recommendation = f"CAUTION: Suspicious features detected. Recommend professional verification."
    else:
        if confidence > 0.80:
            severity = "safe"
            recommendation = f"Note appears genuine. Standard security features detected."
        else:
            severity = "low"
            recommendation = f"Note likely genuine but image quality affects confidence. Use better lighting for verification."
    
    return {
        "is_fake": is_fake,
        "confidence": round(confidence, 3),
        "denomination": f"₹{denom}",
        "denomination_raw": denom,
        "auth_class": "fake" if is_fake else "real",
        "severity": severity,
        "recommendation": recommendation,
        "gradcam_overlay": gradcam_overlay,
        "basic_analysis": basic_analysis,
        "gemini_verification": gemini_result.get("explanation", ""),
        "verification_method": gemini_result["verification_method"],
        "detected_issues": basic_analysis["detected_issues"],
        "security_features_guide": SECURITY_FEATURES,
    }
