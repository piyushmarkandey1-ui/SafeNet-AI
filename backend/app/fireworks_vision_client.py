import os
import logging
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def analyze_currency_image_fireworks(base64_image: str) -> Optional[str]:
    """
    Sends the base64 encoded image to Fireworks AI's vision model
    to detect if it's a real Indian currency note, a fake note, or just a face/background.
    
    Returns a JSON string matching the required schema, or None if it fails.
    """
    api_key = os.getenv("FIREWORKS_API_KEY")
    if not api_key:
        return None

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.fireworks.ai/inference/v1",
    )
        
    prompt = """You are an expert currency detector. You MUST output ONLY raw JSON. Do not include any explanations, thoughts, or markdown formatting.

Analyze the image carefully and determine:
1. Is there an Indian Rupee currency note in the image? If the image shows a person, an ID card (like Aadhaar, PAN, driver's license), a random object, or a blank background, you MUST set "no_note" to true.
2. If it is a currency note, what is its denomination? (10, 20, 50, 100, 200, 500, 2000, or None).
3. Are there counterfeit signs?

Return ONLY this JSON structure matching your analysis:
{"no_note": true_or_false, "is_fake": true_or_false, "denomination": "500", "confidence": 0.0_to_1.0, "detected_issues": ["Issue 1"]}"""
    
    try:
        response = client.chat.completions.create(
            model="accounts/fireworks/models/qwen2-vl-72b-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.warning(f"[fireworks_vision] Call failed: {e}")
        return None
