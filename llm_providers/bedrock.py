"""
AWS Bedrock Integration
Easy setup option using models via AWS Bedrock
"""

import os
from typing import List, Dict, Any
from llm_providers.base import LLMProvider, LLMRequest, LLMResponse
import structlog
import json
import boto3

logger = structlog.get_logger()


class BedrockProvider(LLMProvider):
    """
    AWS Bedrock provider.
    
    Supports multiple models: Claude (Anthropic), Llama (Meta), Titan (Amazon), etc.
    """
    
    def __init__(self, api_key: str = None, region: str = None):
        # Bedrock doesn't use traditional API keys
        # Uses AWS credentials (access key ID, secret access key)
        api_key = api_key or os.getenv('AWS_ACCESS_KEY_ID')
        super().__init__('bedrock', api_key)
        
        self.region = region or os.getenv('AWS_REGION', 'us-east-1')
        self.client = None
        self.authenticated = False
        
        # AWS credentials
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_session_token = os.getenv('AWS_SESSION_TOKEN')
    
    def authenticate(self) -> bool:
        """Authenticate with AWS Bedrock."""
        if not self.aws_access_key or not self.aws_secret_key:
            logger.warning("AWS credentials not configured")
            return False
        
        try:
            # Initialize Bedrock client
            kwargs = {
                'region_name': self.region,
                'aws_access_key_id': self.aws_access_key,
                'aws_secret_access_key': self.aws_secret_key
            }
            
            if self.aws_session_token:
                kwargs['aws_session_token'] = self.aws_session_token
            
            self.client = boto3.client('bedrock-runtime', **kwargs)
            self.authenticated = True
            logger.info("AWS Bedrock authenticated successfully")
            return True
        except Exception as e:
            logger.error("AWS Bedrock authentication failed", error=str(e))
            return False
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Bedrock."""
        if not self.authenticated:
            if not self.authenticate():
                raise RuntimeError("Not authenticated with AWS Bedrock")
        
        # Validate request
        is_valid, error = self.validate_request(request)
        if not is_valid:
            raise ValueError(error)
        
        try:
            # Determine model provider based on model name
            if 'claude' in request.model.lower():
                return self._generate_claude(request)
            elif 'llama' in request.model.lower():
                return self._generate_llama(request)
            elif 'titan' in request.model.lower():
                return self._generate_titan(request)
            else:
                # Default to Claude format
                return self._generate_claude(request)
                
        except Exception as e:
            logger.error("Failed to generate Bedrock response", error=str(e))
            raise
    
    def _generate_claude(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Claude on Bedrock."""
        # Format messages for Claude
        messages = []
        for msg in request.messages:
            if msg['role'] != 'system':
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': request.max_tokens,
            'temperature': request.temperature,
            'messages': messages
        }
        
        # Invoke Bedrock
        response = self.client.invoke_model(
            modelId=request.model,
            body=json.dumps(body),
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        usage = {
            'prompt_tokens': response_body['usage']['input_tokens'],
            'completion_tokens': response_body['usage']['output_tokens'],
            'total_tokens': response_body['usage']['input_tokens'] + response_body['usage']['output_tokens']
        }
        
        self.logger.info(
            "Bedrock Claude response generated",
            model=request.model,
            tokens=usage['total_tokens']
        )
        
        return LLMResponse(
            content=content,
            model=request.model,
            usage=usage,
            finish_reason='stop',
            metadata={'provider': 'bedrock', 'model_type': 'claude'}
        )
    
    def _generate_llama(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Llama on Bedrock."""
        # Format prompt
        prompt = ""
        for msg in request.messages:
            role = msg['role']
            content = msg['content']
            if role == 'user':
                prompt += f"User: {content}\n"
            elif role == 'assistant':
                prompt += f"Assistant: {content}\n"
            elif role == 'system':
                prompt += f"System: {content}\n"
        
        prompt += "Assistant:"
        
        body = {
            'prompt': prompt,
            'max_gen_len': request.max_tokens,
            'temperature': request.temperature
        }
        
        # Invoke Bedrock
        response = self.client.invoke_model(
            modelId=request.model,
            body=json.dumps(body),
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        content = response_body['generation']
        
        usage = {
            'prompt_tokens': response_body.get('prompt_token_count', 0),
            'completion_tokens': response_body.get('generation_token_count', 0),
            'total_tokens': response_body.get('prompt_token_count', 0) + response_body.get('generation_token_count', 0)
        }
        
        self.logger.info(
            "Bedrock Llama response generated",
            model=request.model,
            tokens=usage['total_tokens']
        )
        
        return LLMResponse(
            content=content,
            model=request.model,
            usage=usage,
            finish_reason='stop',
            metadata={'provider': 'bedrock', 'model_type': 'llama'}
        )
    
    def _generate_titan(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Amazon Titan on Bedrock."""
        # Format prompt
        prompt = ""
        for msg in request.messages:
            role = msg['role']
            content = msg['content']
            if role == 'user':
                prompt += f"User: {content}\n"
            elif role == 'assistant':
                prompt += f"Assistant: {content}\n"
        
        body = {
            'inputText': prompt,
            'textGenerationConfig': {
                'maxTokenCount': request.max_tokens,
                'temperature': request.temperature
            }
        }
        
        # Invoke Bedrock
        response = self.client.invoke_model(
            modelId=request.model,
            body=json.dumps(body),
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        content = response_body['results'][0]['outputText']
        
        usage = {
            'prompt_tokens': response_body.get('inputTokenCount', 0),
            'completion_tokens': response_body.get('outputTokenCount', 0),
            'total_tokens': response_body.get('inputTokenCount', 0) + response_body.get('outputTokenCount', 0)
        }
        
        self.logger.info(
            "Bedrock Titan response generated",
            model=request.model,
            tokens=usage['total_tokens']
        )
        
        return LLMResponse(
            content=content,
            model=request.model,
            usage=usage,
            finish_reason='stop',
            metadata={'provider': 'bedrock', 'model_type': 'titan'}
        )
    
    def list_models(self) -> List[str]:
        """List available Bedrock models."""
        return [
            # Claude models
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-opus-20240229-v1:0",
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
            
            # Llama models
            "meta.llama3-70b-instruct-v1:0",
            "meta.llama3-8b-instruct-v1:0",
            
            # Amazon Titan
            "amazon.titan-text-express-v1",
            "amazon.titan-text-lite-v1",
            
            # Other models
            "ai21.j2-ultra-v1",
            "cohere.command-text-v14"
        ]
