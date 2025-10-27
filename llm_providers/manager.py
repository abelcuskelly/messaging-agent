"""
Unified LLM Provider Manager
Easy switching between Anthropic, OpenAI, AWS Bedrock, and Qwen
"""

import os
from typing import Optional, Dict, Any, List
from llm_providers.base import LLMProvider, LLMRequest, LLMResponse
from llm_providers.anthropic import AnthropicProvider
from llm_providers.openai import OpenAIProvider
from llm_providers.bedrock import BedrockProvider
import structlog

logger = structlog.get_logger()


class LLMProviderManager:
    """
    Unified manager for multiple LLM providers.
    Supports easy switching between Anthropic, OpenAI, AWS Bedrock, and Qwen.
    """
    
    def __init__(self, default_provider: str = None):
        """
        Initialize LLM provider manager.
        
        Args:
            default_provider: Default provider to use ('anthropic', 'openai', 'bedrock', 'qwen')
        """
        self.providers = {}
        self.default_provider = default_provider or os.getenv('LLM_PROVIDER', 'anthropic')
        self.logger = logger
        
        # Initialize all providers
        self._initialize_providers()
        
        # Set active provider
        self.active_provider = self.default_provider
        self.active_provider_instance = self.get_provider(self.active_provider)
    
    def _initialize_providers(self):
        """Initialize all available LLM providers."""
        try:
            # Anthropic (Claude)
            self.providers['anthropic'] = AnthropicProvider()
            
            # OpenAI (GPT)
            self.providers['openai'] = OpenAIProvider()
            
            # AWS Bedrock
            self.providers['bedrock'] = BedrockProvider()
            
            # Note: Qwen provider would be the existing Vertex AI integration
            # This is handled separately as it's the advanced option
            
            # Try to authenticate each provider
            for name, provider in self.providers.items():
                try:
                    provider.authenticate()
                except Exception as e:
                    logger.warning(f"{name} provider not authenticated", error=str(e))
            
        except Exception as e:
            logger.error("Failed to initialize LLM providers", error=str(e))
    
    def get_provider(self, provider_name: str) -> Optional[LLMProvider]:
        """Get a specific provider by name."""
        return self.providers.get(provider_name.lower())
    
    def set_active_provider(self, provider_name: str) -> bool:
        """
        Switch active provider.
        
        Args:
            provider_name: Name of provider ('anthropic', 'openai', 'bedrock')
            
        Returns:
            True if provider was set successfully
        """
        provider = self.get_provider(provider_name)
        if not provider:
            logger.warning(f"Provider {provider_name} not found")
            return False
        
        if not provider.authenticated:
            if not provider.authenticate():
                logger.warning(f"Provider {provider_name} authentication failed")
                return False
        
        self.active_provider = provider_name
        self.active_provider_instance = provider
        
        logger.info(f"Active provider set to {provider_name}")
        return True
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        provider: str = None
    ) -> LLMResponse:
        """
        Generate response using active or specified provider.
        
        Args:
            messages: List of messages in format [{'role': 'user', 'content': 'Hello'}]
            model: Model to use (default: provider's default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            provider: Override active provider
            
        Returns:
            LLMResponse with generated content
        """
        # Determine which provider to use
        if provider:
            if not self.set_active_provider(provider):
                raise RuntimeError(f"Failed to set provider to {provider}")
        
        if not self.active_provider_instance:
            raise RuntimeError("No active provider available")
        
        # Get model if not specified
        if not model:
            available_models = self.active_provider_instance.list_models()
            if available_models:
                model = available_models[0]  # Use first available model
            else:
                raise RuntimeError("No models available for provider")
        
        # Create request
        request = LLMRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Generate response
        return self.active_provider_instance.generate(request)
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers and their status."""
        providers_list = []
        
        for name, provider in self.providers.items():
            providers_list.append({
                'name': name,
                'authenticated': provider.authenticated,
                'default_model': provider.list_models()[0] if provider.list_models() else None,
                'available_models': len(provider.list_models())
            })
        
        return providers_list
    
    def get_provider_stats(self, provider_name: str = None) -> Dict[str, Any]:
        """
        Get statistics for a provider.
        
        Args:
            provider_name: Provider name (None = active provider)
            
        Returns:
            Provider statistics
        """
        provider = self.get_provider(provider_name) if provider_name else self.active_provider_instance
        
        if not provider:
            return {'error': 'Provider not found'}
        
        return {
            'provider': provider_name or self.active_provider,
            'authenticated': provider.authenticated,
            'available_models': provider.list_models(),
            'model_count': len(provider.list_models())
        }
    
    def create_chat(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        provider: str = None
    ) -> str:
        """
        Create a chat conversation.
        
        Args:
            system_prompt: System prompt for the conversation
            messages: User messages
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Max tokens
            provider: Provider to use
            
        Returns:
            Assistant's response
        """
        # Add system message
        full_messages = [{'role': 'system', 'content': system_prompt}] + messages
        
        response = self.generate(
            messages=full_messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=provider
        )
        
        return response.content


# Convenience function for easy import
def get_easy_setup_manager(provider: str = None) -> LLMProviderManager:
    """
    Get LLM provider manager for easy setup.
    
    Args:
        provider: Preferred provider ('anthropic', 'openai', 'bedrock')
        
    Returns:
        LLMProviderManager instance
    """
    return LLMProviderManager(default_provider=provider)
