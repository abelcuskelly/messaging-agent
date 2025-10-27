"""
Anthropic Claude Integration
Easy setup option using Claude via Anthropic API
"""

import os
from typing import List, Dict, Any
from llm_providers.base import LLMProvider, LLMRequest, LLMResponse
import structlog

logger = structlog.get_logger()

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic library not installed. Run: pip install anthropic")


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude provider.
    
    Models: claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-opus-20240229
    """
    
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        super().__init__('anthropic', api_key)
        self.client = None
        self.authenticated = False
        
        if not ANTHROPIC_AVAILABLE:
            logger.error("Anthropic library not available")
    
    def authenticate(self) -> bool:
        """Authenticate with Anthropic API."""
        if not ANTHROPIC_AVAILABLE:
            return False
        
        if not self.api_key:
            logger.warning("Anthropic API key not configured")
            return False
        
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.authenticated = True
            logger.info("Anthropic authenticated successfully")
            return True
        except Exception as e:
            logger.error("Anthropic authentication failed", error=str(e))
            return False
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Claude."""
        if not self.authenticated:
            if not self.authenticate():
                raise RuntimeError("Not authenticated with Anthropic")
        
        # Validate request
        is_valid, error = self.validate_request(request)
        if not is_valid:
            raise ValueError(error)
        
        try:
            # Format messages for Claude
            # Claude expects alternating user/assistant messages
            formatted_messages = []
            for msg in request.messages:
                formatted_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            # Convert messages format for Claude API
            system_message = None
            conversation_messages = []
            
            for msg in formatted_messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                elif msg['role'] in ['user', 'assistant']:
                    conversation_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            # Call Claude API
            response = self.client.messages.create(
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                messages=conversation_messages,
                system=system_message if system_message else None
            )
            
            # Extract content
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            # Get usage info
            usage = {
                'prompt_tokens': getattr(response.usage, 'input_tokens', 0),
                'completion_tokens': getattr(response.usage, 'output_tokens', 0),
                'total_tokens': getattr(response.usage, 'total_tokens', 0)
            }
            
            self.logger.info(
                "Claude response generated",
                model=request.model,
                tokens=usage['total_tokens']
            )
            
            return LLMResponse(
                content=content,
                model=request.model,
                usage=usage,
                finish_reason=getattr(response, 'stop_reason', 'unknown'),
                metadata={'provider': 'anthropic'}
            )
            
        except Exception as e:
            self.logger.error("Failed to generate Claude response", error=str(e))
            raise
    
    def list_models(self) -> List[str]:
        """List available Claude models."""
        return [
            "claude-3-5-sonnet-20241022",  # Most capable
            "claude-3-5-haiku-20241022",   # Fast and cheap
            "claude-3-opus-20240229",      # Previous gen
            "claude-3-sonnet-20240229",    # Previous gen
            "claude-3-haiku-20240307"      # Previous gen
        ]
