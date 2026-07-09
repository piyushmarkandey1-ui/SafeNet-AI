from app.fireworks_client import clean_thinking_process

mock_text = """Thinking Process:

1. **Analyze the Input:**
   * User input: "hi"
   * Grounding facts: Pattern match score: 0/100 (meaning no specific scam pattern detected yet, it's just a greeting).
   * Persona: Citizen Shield, advanced AI fraud prevention assistant for Indian citizens.

2. **Determine the Intent/Goal:**
   * User is saying hello.
   * Respond with a welcoming greeting, introduce myself, and ask how I can assist them today.

3. **Draft the Response:**
   * Keep it brief and natural (as per rule 6: "reply naturally in 1-3 sentences").
   * Avoid listing steps.

4. **Refine (Self-Correction during drafting):**
   * Do not quote grounding facts.
   * Do not mention "0/100 score" in the response.

---

Namaste! I am Citizen Shield, your AI fraud prevention assistant. How can I help you stay safe today? Tell me if you've received any suspicious calls or messages!"""

print("CLEANED RESPONSE:")
print(clean_thinking_process(mock_text))

