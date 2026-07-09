import os
import logging
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.getenv("FIREWORKS_API_KEY"),
    base_url="https://api.fireworks.ai/inference/v1",
)

def analyze_currency_image_fireworks(base64_image: str) -> Optional[str]:
    """
    Sends the base64 encoded image to Fireworks AI's Llama 3.2 Vision model
    to detect if it's a real Indian currency note, a fake note, or just a face/background.
    
    Returns a JSON string matching the required schema, or None if it fails.
    """
    if not os.getenv("FIREWORKS_API_KEY"):
        return None
        
    prompt = """You are an expert currency detector. You MUST output ONLY raw JSON. Do not include any explanations, thoughts, or markdown formatting.

Analyze the image and determine:
1. Is there a currency note?
2. What is its denomination?
3. Are there counterfeit signs?

Return ONLY this JSON structure:
{"no_note": false, "is_fake": false, "denomination": "500", "confidence": 0.95, "detected_issues": []}"""
    
    try:
        response = client.chat.completions.create(
            model="accounts/fireworks/models/qwen3p7-plus",
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
