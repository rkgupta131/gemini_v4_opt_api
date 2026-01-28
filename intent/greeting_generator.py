"""
Simple greeting generator that uses a short template. Kept intentionally small.
"""

def generate_greeting_response(user_text: str) -> str:
    greetings = ["hi", "hello", "hey"]
    # simple heuristic
    t = user_text.lower()
    if any(g in t for g in greetings):
        return "Hello! How can I help you today? If you'd like to build a webpage, tell me what type and a short description."
    return "Hello! How can I help?"