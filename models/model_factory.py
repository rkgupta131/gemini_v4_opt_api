# models/model_factory.py
from typing import Optional
from models.base_provider import ModelProvider

# Cache providers to avoid recreating clients
_provider_cache: dict[str, ModelProvider] = {}


def get_provider(model_family: str = "gemini") -> ModelProvider:
    """
    Get or create a model provider for the specified family.
    
    Args:
        model_family: "gemini", "gpt", or "claude" (case-insensitive)
    
    Returns:
        ModelProvider instance
    
    Raises:
        ValueError: If model_family is not supported
        RuntimeError: If provider initialization fails (missing API keys, etc.)
    """
    model_family = model_family.lower().strip()
    
    # Check cache first
    if model_family in _provider_cache:
        return _provider_cache[model_family]
    
    # Import providers (lazy import to avoid errors if packages not installed)
    try:
        from models.providers.gemini_provider import GeminiProvider
        from models.providers.gpt_provider import GPTProvider
        from models.providers.claude_provider import ClaudeProvider
    except ImportError as e:
        raise RuntimeError(f"Failed to import model providers: {e}")
    
    # Create provider based on family
    if model_family == "gemini":
        provider = GeminiProvider()
    elif model_family == "gpt":
        provider = GPTProvider()
    elif model_family == "claude":
        provider = ClaudeProvider()
    else:
        raise ValueError(
            f"Unsupported model family: '{model_family}'. "
            f"Supported families: gemini, gpt, claude"
        )
    
    # Cache the provider
    _provider_cache[model_family] = provider
    return provider


def clear_provider_cache():
    """Clear the provider cache (useful for testing or reinitialization)"""
    global _provider_cache
    _provider_cache.clear()


def get_available_families() -> list[str]:
    """Get list of available model families (based on installed packages and API keys)"""
    families = []
    
    # Gemini is always available if GOOGLE_CLOUD_PROJECT is set
    import os
    if os.getenv("GOOGLE_CLOUD_PROJECT"):
        families.append("gemini")
    
    # Check GPT
    try:
        from models.providers.gpt_provider import GPTProvider
        if os.getenv("OPENAI_API_KEY"):
            families.append("gpt")
    except:
        pass
    
    # Check Claude
    try:
        from models.providers.claude_provider import ClaudeProvider
        if os.getenv("ANTHROPIC_API_KEY"):
            families.append("claude")
    except:
        pass
    
    return families




