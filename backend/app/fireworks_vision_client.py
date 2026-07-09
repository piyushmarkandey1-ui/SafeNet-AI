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
        
    prompt = """
    You are an expert currency detector. Analyze this image of an Indian Rupee note.
    Determine the following:
    1. Is there actually a currency note in the image, or is it just a person's face / a random background?
    2. If it is a note, what is its denomination (10, 20, 50, 100, 200, 500, 2000)?
    3. Are there signs it is counterfeit or a poorly printed fake?
    
    Respond ONLY with a valid JSON object matching this schema exactly:
    {
        "no_note": true or false,
        "is_fake": true or false,
        "denomination": "500" (or other valid denomination, or "None"),
        "confidence": 0.95,
        "detected_issues": ["list", "of", "issues"]
    }
    """
    
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
