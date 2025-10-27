"""
Twitter/X Integration
Connect with customers on Twitter/X
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from integrations.social.base import SocialMediaPlatform, SocialMessage, SocialResponse
import structlog

logger = structlog.get_logger()


class TwitterIntegration(SocialMediaPlatform):
    """
    Twitter/X API integration for customer messaging.
    Handles mentions, DMs, and public replies.
    """
    
    def __init__(self, credentials: Dict[str, str] = None):
        credentials = credentials or {
            'api_key': os.getenv('TWITTER_API_KEY'),
            'api_secret': os.getenv('TWITTER_API_SECRET'),
            'access_token': os.getenv('TWITTER_ACCESS_TOKEN'),
            'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
            'bearer_token': os.getenv('TWITTER_BEARER_TOKEN'),
        }
        super().__init__('twitter', credentials)
        self.api_v2_url = 'https://api.twitter.com/2'
        self.api_v1_url = 'https://api.twitter.com/1.1'
        self.authenticated = False
    
    def authenticate(self) -> bool:
        """Authenticate with Twitter API."""
        try:
            # Check if credentials are available
            if not all([
                self.credentials.get('api_key'),
                self.credentials.get('api_secret'),
                self.credentials.get('access_token'),
                self.credentials.get('access_token_secret')
            ]):
                logger.warning("Twitter credentials not configured")
                return False
            
            # In production, this would use tweepy or Twitter API v2
            # For now, we'll create a mock authentication
            self.authenticated = True
            logger.info("Twitter authenticated successfully")
            return True
            
        except Exception as e:
            logger.error("Twitter authentication failed", error=str(e))
            return False
    
    def get_mentions(self, limit: int = 20) -> List[SocialMessage]:
        """
        Get recent mentions and DMs.
        
        Returns list of SocialMessage objects.
        """
        if not self.authenticated:
            if not self.authenticate():
                logger.warning("Cannot get mentions - not authenticated")
                return []
        
        # Mock implementation
        # In production, this would call Twitter API v2:
        # GET /2/tweets/search/recent?query=mentions:username
        # GET /2/dm_events
        
        logger.info("Fetching mentions", limit=limit)
        
        # Mock mentions for testing
        mentions = [
            SocialMessage(
                platform='twitter',
                message_id=f"mock_tweet_{i}",
                user_id=f"user_{i}",
                username=f"customer_{i}",
                text=f"Hey @yourcompany, I need help with tickets! {i}",
                timestamp=datetime.now(),
                metadata={'type': 'mention'}
            )
            for i in range(min(limit, 5))
        ]
        
        return mentions
    
    def send_message(self, to: str, message: str, reply_to: Optional[str] = None) -> SocialResponse:
        """
        Send a DM or reply on Twitter.
        
        Args:
            to: Username or user ID to send to
            message: Message text
            reply_to: If replying, the original message ID
            
        Returns:
            SocialResponse with status
        """
        if not self.authenticated:
            if not self.authenticate():
                return SocialResponse(
                    success=False,
                    message_id="",
                    timestamp=datetime.now(),
                    error="Not authenticated"
                )
        
        # Validate message
        is_valid, error = self.validate_message(message)
        if not is_valid:
            return SocialResponse(
                success=False,
                message_id="",
                timestamp=datetime.now(),
                error=error
            )
        
        try:
            # In production: POST to /2/dm_conversations
            logger.info("Sending Twitter message", to=to, has_reply_to=reply_to is not None)
            
            # Mock success
            return SocialResponse(
                success=True,
                message_id=f"tw_{datetime.now().timestamp()}",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error("Failed to send Twitter message", error=str(e))
            return SocialResponse(
                success=False,
                message_id="",
                timestamp=datetime.now(),
                error=str(e)
            )
    
    def reply_to_message(self, message_id: str, reply_text: str) -> SocialResponse:
        """Reply to a specific Twitter message."""
        return self.send_message(to="", message=reply_text, reply_to=message_id)
    
    def upload_media(self, file_path: str) -> str:
        """Upload media to Twitter and return media ID."""
        try:
            # In production: POST to /1.1/media/upload.json
            logger.info("Uploading media", file_path=file_path)
            return f"tw_media_{datetime.now().timestamp()}"
        except Exception as e:
            logger.error("Failed to upload media", error=str(e))
            return ""
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get information about a Twitter user."""
        try:
            # In production: GET /2/users/{id}
            return {
                'user_id': user_id,
                'username': 'mock_user',
                'display_name': 'Mock User',
                'followers_count': 1000,
                'verified': False
            }
        except Exception as e:
            logger.error("Failed to get user info", error=str(e))
            return {}
    
    def tweet(self, text: str, reply_to: Optional[str] = None) -> SocialResponse:
        """
        Post a public tweet.
        
        Args:
            text: Tweet content
            reply_to: Tweet ID to reply to (optional)
            
        Returns:
            SocialResponse with tweet ID
        """
        return self.send_message(to="", message=text, reply_to=reply_to)
    
    def get_hashtag_posts(self, hashtag: str, limit: int = 10) -> List[SocialMessage]:
        """
        Get recent posts with a specific hashtag.
        
        Useful for finding customers discussing your brand.
        """
        logger.info("Fetching hashtag posts", hashtag=hashtag, limit=limit)
        
        # Mock implementation
        return [
            SocialMessage(
                platform='twitter',
                message_id=f"hashtag_{hashtag}_{i}",
                user_id=f"user_{i}",
                username=f"user{i}",
                text=f"Excited about #{hashtag}! Looking for tickets.",
                timestamp=datetime.now(),
                metadata={'hashtag': hashtag}
            )
            for i in range(min(limit, 3))
        ]
