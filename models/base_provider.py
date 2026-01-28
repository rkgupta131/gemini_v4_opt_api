# models/base_provider.py
from abc import ABC, abstractmethod
from typing import Generator, Optional

class ModelProvider(ABC):
    """Base class for all model providers"""
    
    def __init__(self, model_family: str):
        self.model_family = model_family
    
    @abstractmethod
    def generate_text(self, prompt: str, model: str, fallback_models: Optional[list] = None, max_retries: int = 3) -> str:
        """Generate text using the specified model"""
        pass
    
    @abstractmethod
    def generate_stream(self, prompt: str, model: str) -> Generator[str, None, None]:
        """Generate streaming text"""
        pass
    
    @abstractmethod
    def get_smaller_model(self) -> str:
        """Get a smaller/faster model for simple tasks"""
        pass
    
    @abstractmethod
    def get_model_for_complexity(self, complexity: str) -> str:
        """Get appropriate model based on task complexity"""
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get default model for webpage generation"""
        pass

