"""
OpenAI GPT Integration
Easy setup option using GPT via OpenAI API
"""

import os
from typing import List, Dict, Any
from llm_providers.base import LLMProvider, LLMRequest, LLMResponse
import structlog

logger = structlog.get_logger()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. Run: pip install openai")


class OpenAIProvider(LLMProvider):
    """
    OpenAI GPT provider.
    
    Models: gpt-4-turbo, gpt-4, gpt-3.5-turbo, gpt-4o-mini
    """
    
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        super().__init__('openai', api_key)
        self.client = None
        self.authenticated = False
        
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI library not available")
    
    def authenticate(self) -> bool:
        """Authenticate with OpenAI API."""
        if not OPENAI_AVAILABLE:
            return False
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
            return False
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            self.authenticated = True
            logger.info("OpenAI authenticated successfully")
            return True
        except Exception as e:
            logger.error("OpenAI authentication failed", error=str(e))
            return False
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using GPT."""
        if not self.authenticated:
            if not self.authenticate():
                raise RuntimeError("Not authenticated with OpenAI")
        
        # Validate request
        is_valid, error = self.validate_request(request)
        if not is_valid:
            raise ValueError(error)
        
        try:
            # Format messages for OpenAI API
            formatted_messages = []
            for msg in request.messages:
                formatted_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=request.model,
                messages=formatted_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=request.stream
            )
            
            # Extract content
            if request.stream:
                # Handle streaming response
                content = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
            else:
                content = response.choices[0].message.content
            
            # Get usage info
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            self.logger.info(
                "GPT response generated",
                model=request.model,
                tokens=usage['total_tokens']
            )
            
            return LLMResponse(
                content=content,
                model=request.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                metadata={'provider': 'openai'}
            )
            
        except Exception as e:
            self.logger.error("Failed to generate GPT response", error=str(e))
            raise
    
    def list_models(self) -> List[str]:
        """List available GPT models."""
        return [
            "gpt-4o",              # Latest, most capable
            "gpt-4-turbo",         # Fast GPT-4
            "gpt-4",              # Standard GPT-4
            "gpt-3.5-turbo",      # Fast and cheap
            "gpt-4o-mini"         # Small and efficient
        ]
