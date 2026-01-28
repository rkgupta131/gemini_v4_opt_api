# utils/tokenizer.py

def estimate_tokens(text: str) -> int:
    """
    Rough token estimate: ~1.3x words.
    Good enough for routing decisions.
    """
    if not text:
        return 0
    return int(len(text.split()) * 1.3)