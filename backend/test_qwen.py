from app.fireworks_client import clean_thinking_process

mock_text = """question. Do not lecture prematurely."
 * Grounding facts indicate a "high scam likelihood" but a "pattern match score: 0/100" (meaning no specific scam pattern is identified yet in the text, just a general high likelihood flag, perhaps based on context or system state).

3. **Formulate the Response:**
 * Acknowledge the user briefly and professionally.
 * Ask exactly *one* highly targeted clarifying question to
 * *Draft 2:* Hi there. To help me protect you effectively, could you tell me exactly what suspicious message, call, or transaction you're dealing with right now? (Good, one question, targeted).
 * *Draft 3.(Refining for persona and rules):* Hello. I'm here to help protect you. To get started, could you tell me exactly what suspicious call, message, or transaction you are currently dealing with?

Hello. I'm here to help protect you. To get started, could you tell me exactly what suspicious call, message, or transaction you are currently dealing with?"""

print("CLEANED RESPONSE:")
print(clean_thinking_process(mock_text))
