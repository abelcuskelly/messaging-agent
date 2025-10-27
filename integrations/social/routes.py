"""
Social Media API Routes
FastAPI endpoints for social media operations
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from integrations.social.manager import SocialMediaManager
from integrations.social.base import SocialMessage, SocialResponse
from auth.jwt_auth import get_current_active_user, User, check_scopes
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/social", tags=["social"])

# Initialize manager
manager = SocialMediaManager()


# Request models
class SendSocialMessageRequest(BaseModel):
    platform: str
    to: str
    message: str
    reply_to: Optional[str] = None


class ReplyToMessageRequest(BaseModel):
    reply_text: str


class SocialCampaignRequest(BaseModel):
    message: str
    platforms: Optional[List[str]] = None


# Response models
class PlatformStatsResponse(BaseModel):
    platform: str
    is_authenticated: bool
    total_messages: int
    recent_messages: int


class UnifiedStatsResponse(BaseModel):
    total_platforms: int
    active_platforms: int
    platform_stats: dict


# Routes

@router.get("/platforms")
async def get_available_platforms(
    current_user: User = Depends(check_scopes(["admin", "view_social"]))
):
    """Get list of available social media platforms."""
    platforms = list(manager.platforms.keys())
    return {
        "platforms": platforms,
        "count": len(platforms)
    }


@router.get("/messages")
async def get_all_messages(
    limit: int = Query(20, ge=1, le=100),
    platform: Optional[str] = None,
    current_user: User = Depends(check_scopes(["view_social"]))
):
    """
    Get messages from social media platforms.
    
    Args:
        limit: Number of messages per platform
        platform: Specific platform to query (optional)
    """
    try:
        if platform:
            messages = manager.get_platform_messages(platform, limit=limit)
        else:
            messages = manager.get_all_messages(limit_per_platform=limit)
        
        return {
            "messages": [
                {
                    "platform": msg.platform,
                    "message_id": msg.message_id,
                    "user_id": msg.user_id,
                    "username": msg.username,
                    "text": msg.text,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in messages
            ],
            "count": len(messages)
        }
    except Exception as e:
        logger.error("Failed to get messages", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{platform}")
async def get_platform_messages(
    platform: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(check_scopes(["view_social"]))
):
    """Get messages from a specific platform."""
    try:
        messages = manager.get_platform_messages(platform, limit=limit)
        
        return {
            "platform": platform,
            "messages": [
                {
                    "message_id": msg.message_id,
                    "user_id": msg.user_id,
                    "username": msg.username,
                    "text": msg.text,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in messages
            ],
            "count": len(messages)
        }
    except Exception as e:
        logger.error(f"Failed to get {platform} messages", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_message(
    request: SendSocialMessageRequest,
    current_user: User = Depends(check_scopes(["admin", "send_social"]))
):
    """Send a message on a social media platform."""
    try:
        platform = manager.get_platform(request.platform)
        if not platform:
            raise HTTPException(status_code=404, detail=f"Platform {request.platform} not found")
        
        response = platform.send_message(
            to=request.to,
            message=request.message,
            reply_to=request.reply_to
        )
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        
        logger.info("Social message sent",
                   platform=request.platform,
                   user_id=current_user.username)
        
        return {
            "success": True,
            "platform": request.platform,
            "message_id": response.message_id,
            "timestamp": response.timestamp.isoformat() if response.timestamp else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send message", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reply/{platform}/{message_id}")
async def reply_to_message(
    platform: str,
    message_id: str,
    request: ReplyToMessageRequest,
    current_user: User = Depends(check_scopes(["admin", "send_social"]))
):
    """Reply to a specific social media message."""
    try:
        response = manager.reply_to_message(platform, message_id, request.reply_text)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        
        logger.info("Reply sent",
                   platform=platform,
                   message_id=message_id,
                   user_id=current_user.username)
        
        return {
            "success": True,
            "platform": platform,
            "reply_message_id": response.message_id,
            "timestamp": response.timestamp.isoformat() if response.timestamp else None
        }
    except Exception as e:
        logger.error("Failed to send reply", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/welcome/{platform}")
async def send_welcome_message(
    platform: str,
    user_id: str,
    custom_message: Optional[str] = None,
    current_user: User = Depends(check_scopes(["admin", "send_social"]))
):
    """Send a welcome message to a new customer."""
    try:
        response = manager.send_welcome_message(platform, user_id, custom_message)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        
        logger.info("Welcome message sent",
                   platform=platform,
                   user_id=user_id,
                   by_user=current_user.username)
        
        return {
            "success": True,
            "platform": platform,
            "user_id": user_id,
            "message_id": response.message_id
        }
    except Exception as e:
        logger.error("Failed to send welcome message", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-respond/{platform}")
async def auto_respond_to_message(
    platform: str,
    message_id: str,
    user_id: str,
    current_user: User = Depends(check_scopes(["admin", "send_social"]))
):
    """Automatically respond to a social media message using AI."""
    try:
        response = manager.auto_respond_to_message(platform, message_id, user_id)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        
        logger.info("Auto-response sent",
                   platform=platform,
                   message_id=message_id,
                   by_user=current_user.username)
        
        return {
            "success": True,
            "platform": platform,
            "message_id": message_id,
            "response_message_id": response.message_id
        }
    except Exception as e:
        logger.error("Failed to auto-respond", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mentions/{keyword}")
async def monitor_brand_mentions(
    keyword: str,
    current_user: User = Depends(check_scopes(["admin", "view_social"]))
):
    """Monitor brand mentions across all social media platforms."""
    try:
        mentions = manager.monitor_brand_mentions(keyword)
        
        return {
            "keyword": keyword,
            "mentions": [
                {
                    "platform": msg.platform,
                    "username": msg.username,
                    "text": msg.text,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in mentions
            ],
            "count": len(mentions)
        }
    except Exception as e:
        logger.error("Failed to get mentions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaign")
async def create_social_campaign(
    request: SocialCampaignRequest,
    current_user: User = Depends(check_scopes(["admin"]))
):
    """Create a social media campaign across multiple platforms."""
    try:
        results = manager.create_social_campaign(request.message, request.platforms)
        
        successful_platforms = [p for p, r in results.items() if r.success]
        failed_platforms = [p for p, r in results.items() if not r.success]
        
        logger.info("Social campaign created",
                   total_platforms=len(results),
                   successful=len(successful_platforms),
                   user_id=current_user.username)
        
        return {
            "success": True,
            "campaign_message": request.message,
            "successful_platforms": successful_platforms,
            "failed_platforms": failed_platforms,
            "platforms_posted": len(successful_platforms),
            "platforms_failed": len(failed_platforms)
        }
    except Exception as e:
        logger.error("Failed to create campaign", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{platform}")
async def get_platform_stats(
    platform: str,
    current_user: User = Depends(check_scopes(["admin", "view_social"]))
):
    """Get statistics for a specific social media platform."""
    try:
        stats = manager.get_platform_stats(platform)
        return stats
    except Exception as e:
        logger.error(f"Failed to get {platform} stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_unified_stats(
    current_user: User = Depends(check_scopes(["admin", "view_dashboard"]))
):
    """Get unified statistics across all social media platforms."""
    try:
        stats = manager.get_unified_stats()
        return stats
    except Exception as e:
        logger.error("Failed to get unified stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{platform}")
async def check_platform_health(
    platform: str,
    current_user: User = Depends(check_scopes(["admin", "view_social"]))
):
    """Check health status of a social media platform."""
    try:
        platform_obj = manager.get_platform(platform)
        if not platform_obj:
            return {
                "platform": platform,
                "status": "not_found",
                "authenticated": False
            }
        
        is_authenticated = platform_obj.authenticated
        
        return {
            "platform": platform,
            "status": "healthy" if is_authenticated else "not_authenticated",
            "authenticated": is_authenticated
        }
    except Exception as e:
        logger.error(f"Failed to check {platform} health", error=str(e))
        return {
            "platform": platform,
            "status": "error",
            "authenticated": False,
            "error": str(e)
        }
