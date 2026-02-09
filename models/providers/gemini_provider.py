# models/providers/gemini_provider.py
import os
import time
from typing import Generator, Optional
from google import genai
from google.genai.types import HttpOptions
from models.base_provider import ModelProvider


class GeminiProvider(ModelProvider):
    """Gemini model provider"""
    
    def __init__(self):
        super().__init__("gemini")
        self._client = None
    
    def _make_client(self):
        if self._client is not None:
            return self._client
        
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
        
        if not project:
            raise RuntimeError(
                "GOOGLE_CLOUD_PROJECT is not set. "
                "Make sure load_dotenv() is called before using GeminiProvider."
            )
        
        self._client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
            http_options=HttpOptions(api_version="v1"),
        )
        return self._client
    
    def generate_text(self, prompt: str, model: str = "gemini-3-pro-preview", 
                     fallback_models: Optional[list] = None, max_retries: int = 3) -> str:
        """Generate text using Gemini models with retry logic"""
        client = self._make_client()
        
        models_to_try = [model]
        if fallback_models:
            models_to_try.extend(fallback_models)
        
        last_error = None
        for model_name in models_to_try:
            for attempt in range(max_retries):
                try:
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    if model_name != model:
                        print(f"[GEMINI_FALLBACK] ✅ Used fallback model: {model_name} (original: {model})")
                    return getattr(resp, "text", "") or str(resp)
                except Exception as e:
                    error_msg = str(e)
                    
                    # Check for 429 error (rate limit / resource exhausted)
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "Resource exhausted" in error_msg:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            print(f"[GEMINI_RATE_LIMIT] ⚠️ Rate limit hit (429). Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                            time.sleep(wait_time)
                            continue
                        else:
                            last_error = e
                            break
                    
                    # Check for 404 error (model not found)
                    elif "404" in error_msg or "NOT_FOUND" in error_msg:
                        if model_name != models_to_try[-1]:
                            print(f"[GEMINI_FALLBACK] ⚠️ Model {model_name} not available (404), trying next fallback...")
                            last_error = e
                            break
                        else:
                            raise e
                    
                    # Other errors
                    else:
                        last_error = e
                        if model_name != models_to_try[-1]:
                            break
                        else:
                            raise e
        
        if last_error:
            error_msg = str(last_error)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                raise RuntimeError(
                    "Gemini API rate limit exceeded (429). Please wait a few minutes and try again."
                ) from last_error
            raise last_error
        
        raise RuntimeError("No Gemini models available")
    
    def generate_stream(self, prompt: str, model: str = "gemini-3-pro-preview") -> Generator[str, None, None]:
        """Generate streaming text using Gemini models"""
        client = self._make_client()
        
        if hasattr(client.models, "generate_content_stream"):
            for part in client.models.generate_content_stream(
                model=model,
                contents=prompt,
            ):
                if hasattr(part, "text") and part.text:
                    yield part.text
        else:
            # Fallback to non-streaming
            yield self.generate_text(prompt, model=model)
    
    def get_smaller_model(self) -> str:
        """Get smaller/faster Gemini model for simple tasks"""
        return "gemini-2.0-flash"
    
    def get_model_for_complexity(self, complexity: str) -> str:
        """Get appropriate Gemini model based on task complexity"""
        if complexity == "high":
            return "gemini-3-pro-preview"
        elif complexity == "medium":
            return "gemini-2.0-flash"
        else:
            return self.get_smaller_model()
    
    def get_default_model(self) -> str:
        """Get default Gemini model for webpage generation"""
        return "gemini-3-pro-preview"





