# intent/classifier.py

import re

# def classify_intent(text: str) -> str:
#     text = text.lower().strip()

#     # If user is simply greeting
#     if any(g in text for g in ["hello", "hi", "hey", "good morning", "good evening"]):
#         return "greeting_only"

#     # Informational / Chat queries (DO NOT START BUILDER)
#     informational_patterns = [
#         r"what is",
#         r"explain",
#         r"how does",
#         r"tell me about",
#         r"define",
#         r"what are",
#         r"why is",
#         r"difference between",
#         r"how to learn",
#         r"examples of",
#         r"guide me",
#     ]
#     if any(re.search(p, text) for p in informational_patterns):
#         return "other"

#     # If user expresses intent to build a webpage
#     builder_keywords = [
#         "build",
#         "create",
#         "generate",
#         "make",
#         "design",
#         "construct",
#         "develop",
#         "i want a website",
#         "i want to build",
#         "i want to create",
#         "webpage for",
#         "website for",
#         "landing page for",
#     ]
#     if any(k in text for k in builder_keywords):
#         return "webpage_build"

#     # Greeting + builder intent
#     if any(g in text for g in ["hi", "hello", "hey"]) and any(
#         k in text for k in builder_keywords
#     ):
#         return "greeting_and_webpage"

#     # Default = chat mode
#     return "other"


# intent/classifier.py
"""
Thin wrapper for intent classification. Attempts to use the model classifier
from models.gemini_client.classify_intent(). If that fails (network/ADC),
falls back to a simple heuristic classifier so your app remains responsive.
"""

from typing import Tuple
import re

try:
    from models.gemini_client import classify_intent as model_classify
except Exception:
    model_classify = None


def heuristic_classify(text: str) -> Tuple[str, dict]:
    txt = text.strip().lower()
    # greetings
    if re.fullmatch(r"(hi|hello|hey|yo|hi there|hello there)([!.]*)", txt):
        return "greeting_only", {"explanation": "Simple greeting detected", "confidence": 0.9}
    # short definitional questions (educational)
    if txt.startswith(("what is", "what's", "define", "explain", "how does", "how to")) and "webpage" in txt:
        return "chat", {"explanation": "Asking about what a webpage is — treat as educational chat", "confidence": 0.8}
    # explicit build triggers
    if any(kw in txt for kw in ("build a website", "make a website", "create a webpage", "generate a webpage", "build webpage", "make a landing page", "generate project")):
        return "webpage_build", {"explanation": "User explicitly requests webpage generation", "confidence": 0.95}
    # illegal content detection (very simple)
    if any(kw in txt for kw in ("hack", "ddos", "steal", "crack", "illegal", "bypass")):
        return "illegal", {"explanation": "Detected potential illegal intent", "confidence": 0.99}
    # fallback
    return "chat", {"explanation": "Default to chat", "confidence": 0.3}


def classify_intent(user_text: str) -> Tuple[str, dict]:
    if model_classify:
        try:
            label, meta = model_classify(user_text)
            return label, meta
        except Exception:
            # model failure — fall back
            return heuristic_classify(user_text)
    else:
        return heuristic_classify(user_text)