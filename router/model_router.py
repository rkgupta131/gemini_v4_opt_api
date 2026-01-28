# router/model_router.py

def select_model(prompt: str, tokens_est: int) -> str:
    """
    Always return Gemini 3 Pro Preview.
    Routing is no longer required.
    """
    return "gemini:gemini-3-pro-preview"