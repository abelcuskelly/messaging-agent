"""
LLM Provider Abstraction Layer
Unified interface for multiple LLM providers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class LLMRequest:
    """Request to an LLM provider."""
    messages: List[Dict[str, str]]
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str
    usage: Dict[str, int] = None
    finish_reason: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.usage is None:
            self.usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
        if self.metadata is None:
            self.metadata = {}


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, name: str, api_key: str):
        self.name = name
        self.api_key = api_key
        self.logger = logger.bind(provider=name)
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the provider."""
        pass
    
    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response from LLM."""
        pass
    
    @abstractmethod
    def list_models(self) -> List[str]:
        """List available models for this provider."""
        pass
    
    def validate_request(self, request: LLMRequest) -> tuple[bool, Optional[str]]:
        """
        Validate request before sending.
        Returns (is_valid, error_message).
        """
        if not request.messages:
            return False, "Messages list cannot be empty"
        
        if request.temperature < 0 or request.temperature > 2:
            return False, "Temperature must be between 0 and 2"
        
        if request.max_tokens < 1:
            return False, "Max tokens must be at least 1"
        
        return True, None
