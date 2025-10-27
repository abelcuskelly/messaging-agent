"""
Unified Social Media Manager
Centralized management for all social media platforms
"""

from typing import List, Dict, Any, Optional
from integrations.social.base import SocialMessage, SocialResponse
from integrations.social.twitter import TwitterIntegration
from integrations.social.linkedin import LinkedInIntegration
from integrations.social.facebook import FacebookIntegration
import structlog

logger = structlog.get_logger()


class SocialMediaManager:
    """
    Unified manager for all social media platforms.
    Handles cross-platform messaging, monitoring, and analytics.
    """
    
    def __init__(self):
        self.platforms = {}
        self.logger = logger
        self._initialize_platforms()
    
    def _initialize_platforms(self):
        """Initialize all social media platforms."""
        try:
            # Initialize Twitter/X
            self.platforms['twitter'] = TwitterIntegration()
            if self.platforms['twitter'].authenticate():
                logger.info("Twitter integration initialized")
            
            # Initialize LinkedIn
            self.platforms['linkedin'] = LinkedInIntegration()
            if self.platforms['linkedin'].authenticate():
                logger.info("LinkedIn integration initialized")
            
            # Initialize Facebook
            self.platforms['facebook'] = FacebookIntegration()
            if self.platforms['facebook'].authenticate():
                logger.info("Facebook integration initialized")
            
        except Exception as e:
            logger.error("Failed to initialize social media platforms", error=str(e))
    
    def get_platform(self, platform_name: str) -> Optional[Any]:
        """Get a specific platform integration."""
        return self.platforms.get(platform_name.lower())
    
    def get_all_messages(self, limit_per_platform: int = 20) -> List[SocialMessage]:
        """
        Get messages from all platforms.
        
        Returns:
            List of all messages across platforms
        """
        all_messages = []
        
        for platform_name, platform in self.platforms.items():
            try:
                messages = platform.get_mentions(limit=limit_per_platform)
                all_messages.extend(messages)
            except Exception as e:
                logger.error(f"Failed to get {platform_name} messages", error=str(e))
        
        # Sort by timestamp (newest first)
        all_messages.sort(key=lambda x: x.timestamp, reverse=True)
        
        return all_messages
    
    def get_platform_messages(self, platform_name: str, limit: int = 20) -> List[SocialMessage]:
        """Get messages from a specific platform."""
        platform = self.get_platform(platform_name)
        if not platform:
            logger.warning(f"Platform {platform_name} not found")
            return []
        
        try:
            return platform.get_mentions(limit=limit)
        except Exception as e:
            logger.error(f"Failed to get {platform_name} messages", error=str(e))
            return []
    
    def send_to_all_platforms(self, user_id: str, message: str) -> Dict[str, SocialResponse]:
        """
        Send a message to a user across all their social media accounts.
        
        Args:
            user_id: User ID (platform-specific)
            message: Message text
            
        Returns:
            Dict of {platform_name: SocialResponse}
        """
        results = {}
        
        for platform_name, platform in self.platforms.items():
            try:
                response = platform.send_message(to=user_id, message=message)
                results[platform_name] = response
            except Exception as e:
                logger.error(f"Failed to send on {platform_name}", error=str(e))
                results[platform_name] = SocialResponse(
                    success=False,
                    message_id="",
                    timestamp=None,
                    error=str(e)
                )
        
        return results
    
    def reply_to_message(self, platform_name: str, message_id: str, reply_text: str) -> SocialResponse:
        """Reply to a message on a specific platform."""
        platform = self.get_platform(platform_name)
        if not platform:
            return SocialResponse(
                success=False,
                message_id="",
                timestamp=None,
                error=f"Platform {platform_name} not found"
            )
        
        return platform.reply_to_message(message_id, reply_text)
    
    def get_platform_stats(self, platform_name: str) -> Dict[str, Any]:
        """Get statistics for a specific platform."""
        platform = self.get_platform(platform_name)
        if not platform:
            return {'error': f'Platform {platform_name} not found'}
        
        try:
            messages = platform.get_mentions(limit=1000)
            return {
                'total_messages': len(messages),
                'platform': platform_name,
                'is_authenticated': platform.authenticated,
                'recent_messages': len(messages)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_unified_stats(self) -> Dict[str, Any]:
        """Get statistics across all platforms."""
        stats = {}
        
        for platform_name in self.platforms.keys():
            stats[platform_name] = self.get_platform_stats(platform_name)
        
        stats['total_platforms'] = len(self.platforms)
        stats['active_platforms'] = len([p for p in self.platforms.values() if p.authenticated])
        
        return stats
    
    def send_welcome_message(self, platform_name: str, user_id: str, custom_message: str = None) -> SocialResponse:
        """
        Send a welcome message to a new customer.
        
        Args:
            platform_name: Platform to send on
            user_id: User ID
            custom_message: Custom welcome message (optional)
            
        Returns:
            SocialResponse with status
        """
        default_message = (
            "Hi! 👋 Welcome! I'm your AI assistant. "
            "I can help you with:\n"
            "- Finding tickets\n"
            "- Seat upgrades\n"
            "- Event information\n"
            "- Order status\n\n"
            "How can I help you today?"
        )
        
        message = custom_message or default_message
        
        platform = self.get_platform(platform_name)
        if not platform:
            return SocialResponse(
                success=False,
                message_id="",
                timestamp=None,
                error=f"Platform {platform_name} not found"
            )
        
        return platform.send_message(to=user_id, message=message)
    
    def process_social_message(self, message: SocialMessage) -> str:
        """
        Process a message from social media and return an appropriate response.
        
        This would integrate with your AI agent to generate responses.
        
        Args:
            message: Social media message
            
        Returns:
            AI-generated response text
        """
        # Format message for AI agent
        formatted_message = message.platform.format_for_agent(message)
        
        # In production, this would call your AI agent
        # For now, return a mock response
        mock_responses = {
            'twitter': "Thanks for reaching out on Twitter! I'd be happy to help you find tickets. What game or event are you interested in?",
            'linkedin': "Hello! Thank you for your interest. I can assist with corporate ticket packages and bulk purchases. What's your timeline?",
            'facebook': "Hi there! 👋 Great to hear from you on Facebook. Let me help you with ticket information. What are you looking for?"
        }
        
        return mock_responses.get(message.platform, "Hello! How can I help you today?")
    
    def auto_respond_to_message(self, platform_name: str, message_id: str, user_id: str) -> SocialResponse:
        """
        Automatically respond to a social media message using the AI agent.
        
        Args:
            platform_name: Platform the message came from
            message_id: ID of the message
            user_id: ID of the user
            
        Returns:
            SocialResponse with reply status
        """
        # Get the original message
        platform = self.get_platform(platform_name)
        if not platform:
            return SocialResponse(
                success=False,
                message_id="",
                timestamp=None,
                error=f"Platform {platform_name} not found"
            )
        
        # Get message details (mock for now)
        # In production, you'd fetch the actual message
        message = SocialMessage(
            platform=platform_name,
            message_id=message_id,
            user_id=user_id,
            username="user",
            text="Need help with tickets",
            timestamp=None
        )
        
        # Generate AI response
        reply_text = self.process_social_message(message)
        
        # Send reply
        return platform.reply_to_message(message_id, reply_text)
    
    def monitor_brand_mentions(self, keyword: str) -> List[SocialMessage]:
        """
        Monitor brand mentions across all platforms.
        
        Args:
            keyword: Keyword to search for
            
        Returns:
            List of messages mentioning the keyword
        """
        all_messages = self.get_all_messages(limit_per_platform=50)
        
        # Filter messages containing keyword
        mentions = [
            msg for msg in all_messages
            if keyword.lower() in msg.text.lower() or keyword.lower() in msg.username.lower()
        ]
        
        return mentions
    
    def create_social_campaign(self, message: str, platforms: List[str] = None) -> Dict[str, SocialResponse]:
        """
        Create a social media campaign across multiple platforms.
        
        Args:
            message: Campaign message
            platforms: List of platforms to post on (None = all)
            
        Returns:
            Dict of {platform: SocialResponse}
        """
        platforms_to_post = platforms if platforms else self.platforms.keys()
        results = {}
        
        for platform_name in platforms_to_post:
            platform = self.get_platform(platform_name)
            if not platform:
                continue
            
            try:
                # Different platforms have different methods
                if platform_name == 'twitter':
                    response = platform.tweet(message)
                elif platform_name == 'linkedin':
                    response = platform.post_content(message)
                elif platform_name == 'facebook':
                    # For Facebook, you'd post to the page
                    response = platform.send_message(to="", message=message)
                else:
                    response = platform.send_message(to="", message=message)
                
                results[platform_name] = response
            except Exception as e:
                logger.error(f"Failed to post on {platform_name}", error=str(e))
                results[platform_name] = SocialResponse(
                    success=False,
                    message_id="",
                    timestamp=None,
                    error=str(e)
                )
        
        return results
