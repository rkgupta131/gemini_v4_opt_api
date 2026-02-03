# models/providers/claude_provider.py
import os
import time
from typing import Generator, Optional
from models.base_provider import ModelProvider

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ClaudeProvider(ModelProvider):
    """Anthropic Claude model provider"""
    
    def __init__(self):
        super().__init__("claude")
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError("anthropic package is not installed. Install it with: pip install anthropic")
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set in environment variables")
        
        self._client = anthropic.Anthropic(api_key=api_key)
    
    def generate_text(self, prompt: str, model: str = "claude-3-5-sonnet-20241022", 
                     fallback_models: Optional[list] = None, max_retries: int = 3) -> str:
        """Generate text using Claude models with retry logic"""
        models_to_try = [model]
        if fallback_models:
            models_to_try.extend(fallback_models)
        
        last_error = None
        for model_name in models_to_try:
            for attempt in range(max_retries):
                try:
                    message = self._client.messages.create(
                        model=model_name,
                        max_tokens=4096,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return message.content[0].text
                except Exception as e:
                    error_msg = str(e)
                    
                    # Check for rate limit
                    if "rate_limit" in error_msg.lower() or "429" in error_msg:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            print(f"[CLAUDE_RATE_LIMIT] ⚠️ Rate limit hit. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                            time.sleep(wait_time)
                            continue
                        else:
                            last_error = e
                            break
                    
                    # Other errors
                    last_error = e
                    if model_name != models_to_try[-1]:
                        print(f"[CLAUDE_FALLBACK] ⚠️ Model {model_name} failed, trying next fallback...")
                        break
                    else:
                        raise e
        
        if last_error:
            raise last_error
        
        raise RuntimeError("No Claude models available")
    
    def generate_stream(self, prompt: str, model: str = "claude-3-5-sonnet-20241022") -> Generator[str, None, None]:
        """Generate streaming text using Claude models"""
        with self._client.messages.stream(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text
    
    def get_smaller_model(self) -> str:
        """Get smaller/faster Claude model for simple tasks"""
        return "claude-3-haiku-20240307"
    
    def get_model_for_complexity(self, complexity: str) -> str:
        """Get appropriate Claude model based on task complexity"""
        if complexity == "high":
            return "claude-3-5-sonnet-20241022"
        elif complexity == "medium":
            return "claude-3-opus-20240229"
        else:
            return self.get_smaller_model()
    
    def get_default_model(self) -> str:
        """Get default Claude model for webpage generation"""
        return "claude-3-5-sonnet-20241022"




