"""
Base Social Media Integration
Abstract interface for social media platforms
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class SocialMessage:
    """Social media message data structure."""
    platform: str
    message_id: str
    user_id: str
    username: str
    text: str
    timestamp: datetime
    media_urls: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.media_urls is None:
            self.media_urls = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SocialResponse:
    """Response to a social media message."""
    success: bool
    message_id: str
    timestamp: datetime
    error: Optional[str] = None


class SocialMediaPlatform(ABC):
    """Abstract base class for social media platforms."""
    
    def __init__(self, name: str, credentials: Dict[str, str]):
        self.name = name
        self.credentials = credentials
        self.logger = logger.bind(platform=name)
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the social media platform."""
        pass
    
    @abstractmethod
    def get_mentions(self, limit: int = 20) -> List[SocialMessage]:
        """Get recent mentions/DMs."""
        pass
    
    @abstractmethod
    def send_message(self, to: str, message: str, reply_to: Optional[str] = None) -> SocialResponse:
        """Send a message to a user."""
        pass
    
    @abstractmethod
    def reply_to_message(self, message_id: str, reply_text: str) -> SocialResponse:
        """Reply to a specific message."""
        pass
    
    @abstractmethod
    def upload_media(self, file_path: str) -> str:
        """Upload media and return media ID."""
        pass
    
    @abstractmethod
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get information about a user."""
        pass
    
    def validate_message(self, message: str) -> tuple[bool, Optional[str]]:
        """
        Validate message before sending.
        Returns (is_valid, error_message).
        """
        if not message or not message.strip():
            return False, "Message cannot be empty"
        
        # Platform-specific length limits
        max_lengths = {
            'twitter': 280,
            'linkedin': 3000,
            'facebook': 8000
        }
        
        platform_max = max_lengths.get(self.name.lower(), 1000)
        if len(message) > platform_max:
            return False, f"Message exceeds {platform_max} character limit"
        
        return True, None
    
    def format_for_agent(self, message: SocialMessage) -> str:
        """
        Format social media message for the AI agent.
        Includes context about the platform and user.
        """
        context = f"[{message.platform.upper()}] Message from @{message.username}:\n"
        context += f"{message.text}\n"
        
        if message.metadata:
            context += f"\nAdditional context: {message.metadata}"
        
        return context
