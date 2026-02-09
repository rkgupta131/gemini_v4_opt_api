# models/providers/__init__.py
from .gemini_provider import GeminiProvider
from .gpt_provider import GPTProvider

# Claude provider is optional (file may not exist)
try:
    from .claude_provider import ClaudeProvider
    __all__ = ['GeminiProvider', 'GPTProvider', 'ClaudeProvider']
except ImportError:
    # Claude provider not available
    __all__ = ['GeminiProvider', 'GPTProvider']





