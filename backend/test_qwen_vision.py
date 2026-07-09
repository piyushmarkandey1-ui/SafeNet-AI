import os
from openai import OpenAI
from dotenv import load_dotenv
import base64

load_dotenv()

client = OpenAI(
    api_key=os.getenv("FIREWORKS_API_KEY"),
    base_url="https://api.fireworks.ai/inference/v1",
)

try:
    # 1x1 pixel black image in base64
    b64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    response = client.chat.completions.create(
        model="accounts/fireworks/models/qwen3p7-plus",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
                ]
            }
        ]
    )
    print("SUCCESS: ", response.choices[0].message.content)
except Exception as e:
    print(f"FAILED: {e}")
