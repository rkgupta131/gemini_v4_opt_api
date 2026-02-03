# models/providers/gpt_provider.py
import os
import time
from typing import Generator, Optional
from models.base_provider import ModelProvider

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class GPTProvider(ModelProvider):
    """OpenAI GPT model provider"""
    
    def __init__(self):
        super().__init__("gpt")
        if not OPENAI_AVAILABLE:
            raise RuntimeError("openai package is not installed. Install it with: pip install openai")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment variables")
        
        self._client = OpenAI(api_key=api_key)
    
    def generate_text(self, prompt: str, model: str = "gpt-4o", 
                     fallback_models: Optional[list] = None, max_retries: int = 3) -> str:
        """Generate text using OpenAI GPT models with retry logic"""
        models_to_try = [model]
        if fallback_models:
            models_to_try.extend(fallback_models)
        
        last_error = None
        for model_name in models_to_try:
            for attempt in range(max_retries):
                try:
                    response = self._client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    error_msg = str(e)
                    
                    # Check for rate limit
                    if "rate_limit" in error_msg.lower() or "429" in error_msg:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            print(f"[GPT_RATE_LIMIT] ⚠️ Rate limit hit. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                            time.sleep(wait_time)
                            continue
                        else:
                            last_error = e
                            break
                    
                    # Other errors
                    last_error = e
                    if model_name != models_to_try[-1]:
                        print(f"[GPT_FALLBACK] ⚠️ Model {model_name} failed, trying next fallback...")
                        break
                    else:
                        raise e
        
        if last_error:
            raise last_error
        
        raise RuntimeError("No GPT models available")
    
    def generate_stream(self, prompt: str, model: str = "gpt-4o") -> Generator[str, None, None]:
        """Generate streaming text using OpenAI GPT models"""
        stream = self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def get_smaller_model(self) -> str:
        """Get smaller/faster GPT model for simple tasks"""
        return "gpt-4o-mini"
    
    def get_model_for_complexity(self, complexity: str) -> str:
        """Get appropriate GPT model based on task complexity"""
        if complexity == "high":
            return "gpt-4o"
        elif complexity == "medium":
            return "gpt-4o"
        else:
            return self.get_smaller_model()
    
    def get_default_model(self) -> str:
        """Get default GPT model for webpage generation"""
        return "gpt-4o"




