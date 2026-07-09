import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("FIREWORKS_API_KEY"),
    base_url="https://api.fireworks.ai/inference/v1",
)

system_prompt = """You are Citizen Shield, an advanced AI fraud prevention assistant protecting Indian citizens.
Your job is to analyze the user's situation and provide direct, clear, empathetic safety guidance.

RULES:
1. Speak naturally, professionally, and directly.
2. If the user's message is very brief (e.g. "hi"), welcome them and ask how you can help them stay safe.
3. If they are reporting a scam, give them direct, bulleted instructions on what to do.
4. Keep your response concise.
5. Never output draft steps, rules, or internal monologue. Output ONLY the direct response to the user."""

try:
    response = client.chat.completions.create(
        model="accounts/fireworks/models/glm-5p1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "I received a call from CBI saying my bank account will be blocked unless I transfer money.\n\n[GROUNDING FACTS]\n- Intent: suspicious_call\n- Pattern score: 95/100\n- Triggered tactics: [IMPERSONATION, URGENCY_THREAT, ACTION_REQUEST]"}
        ],
        temperature=0.7,
        max_tokens=600
    )
    print("RESPONSE:\n", response.choices[0].message.content)
except Exception as e:
    print("FAILED: ", e)
