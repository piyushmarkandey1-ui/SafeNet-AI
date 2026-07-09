import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("FIREWORKS_API_KEY"),
    base_url="https://api.fireworks.ai/inference/v1",
)

try:
    response = client.chat.completions.create(
        model="accounts/fireworks/models/qwen3p7-plus",
        messages=[
            {
                "role": "user",
                "content": "Say hello"
            }
        ]
    )
    print("SUCCESS: ", response.choices[0].message.content)
except Exception as e:
    print(f"FAILED: {e}")
