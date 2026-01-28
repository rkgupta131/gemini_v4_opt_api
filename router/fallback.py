# router/fallback.py

def fallback(model_id: str) -> str:
    """
    Gemini-only fallback.
    If something fails, retry using same model.
    """
    return "gemini:gemini-3-pro-preview"