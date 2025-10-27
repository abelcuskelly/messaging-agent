"""
Webhook Manager
Configure and manage webhooks for external integrations
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
import json
import httpx
import hmac
import hashlib
import structlog

logger = structlog.get_logger()


class WebhookEvent(BaseModel):
    """Webhook event types"""
    conversation_started: bool = False
    conversation_completed: bool = False
    message_received: bool = False
    message_sent: bool = False
    error_occurred: bool = False
    alert_triggered: bool = False
    model_switched: bool = False
    user_created: bool = False
    threshold_exceeded: bool = False


class WebhookConfig(BaseModel):
    """Webhook configuration"""
    id: str
    name: str
    url: HttpUrl
    events: WebhookEvent
    secret: str = Field(description="Secret for HMAC signature")
    headers: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    retry_count: int = Field(default=3, ge=0, le=10)
    timeout: int = Field(default=30, ge=5, le=120)
    created_at: datetime = Field(default_factory=datetime.now)


class WebhookPayload(BaseModel):
    """Webhook payload structure"""
    event: str
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None


class WebhookManager:
    """Manage webhooks and deliver events"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.logger = logger
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def create_webhook(self, webhook: WebhookConfig) -> Dict[str, Any]:
        """Register a new webhook"""
        try:
            webhook_key = f"webhook:{webhook.id}"
            
            await self.redis.hset(
                webhook_key,
                mapping={
                    "name": webhook.name,
                    "url": str(webhook.url),
                    "events": json.dumps(webhook.events.dict()),
                    "secret": webhook.secret,
                    "headers": json.dumps(webhook.headers),
                    "enabled": str(webhook.enabled),
                    "retry_count": str(webhook.retry_count),
                    "timeout": str(webhook.timeout),
                    "created_at": webhook.created_at.isoformat()
                }
            )
            
            # Add to active webhooks list
            if webhook.enabled:
                await self.redis.sadd("webhooks:active", webhook.id)
            
            self.logger.info("Webhook created", webhook_id=webhook.id, url=str(webhook.url))
            
            return {"status": "success", "webhook_id": webhook.id}
            
        except Exception as e:
            self.logger.error("Failed to create webhook", error=str(e))
            raise
    
    async def get_webhook(self, webhook_id: str) -> Optional[WebhookConfig]:
        """Get webhook configuration"""
        try:
            webhook_data = await self.redis.hgetall(f"webhook:{webhook_id}")
            
            if not webhook_data:
                return None
            
            return WebhookConfig(
                id=webhook_id,
                name=webhook_data["name"],
                url=webhook_data["url"],
                events=WebhookEvent(**json.loads(webhook_data["events"])),
                secret=webhook_data["secret"],
                headers=json.loads(webhook_data.get("headers", "{}")),
                enabled=webhook_data.get("enabled") == "True",
                retry_count=int(webhook_data.get("retry_count", 3)),
                timeout=int(webhook_data.get("timeout", 30)),
                created_at=datetime.fromisoformat(webhook_data["created_at"])
            )
            
        except Exception as e:
            self.logger.error("Failed to get webhook", webhook_id=webhook_id, error=str(e))
            return None
    
    async def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all webhooks"""
        try:
            webhook_keys = await self.redis.keys("webhook:*")
            
            webhooks = []
            for key in webhook_keys:
                webhook_id = key.split(":")[-1]
                webhook = await self.get_webhook(webhook_id)
                if webhook:
                    webhooks.append({
                        "id": webhook.id,
                        "name": webhook.name,
                        "url": str(webhook.url),
                        "enabled": webhook.enabled,
                        "created_at": webhook.created_at.isoformat()
                    })
            
            return webhooks
            
        except Exception as e:
            self.logger.error("Failed to list webhooks", error=str(e))
            return []
    
    async def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook"""
        try:
            await self.redis.delete(f"webhook:{webhook_id}")
            await self.redis.srem("webhooks:active", webhook_id)
            
            self.logger.info("Webhook deleted", webhook_id=webhook_id)
            
            return {"status": "success"}
            
        except Exception as e:
            self.logger.error("Failed to delete webhook", error=str(e))
            raise
    
    async def trigger_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger webhook for specific event"""
        try:
            # Get all active webhooks
            webhook_ids = await self.redis.smembers("webhooks:active")
            
            delivery_results = []
            
            for webhook_id in webhook_ids:
                webhook = await self.get_webhook(webhook_id)
                
                if not webhook or not webhook.enabled:
                    continue
                
                # Check if webhook is subscribed to this event
                if not getattr(webhook.events, event_type, False):
                    continue
                
                # Deliver the webhook
                result = await self._deliver_webhook(webhook, event_type, data)
                delivery_results.append(result)
            
            return {
                "event": event_type,
                "webhooks_triggered": len(delivery_results),
                "results": delivery_results
            }
            
        except Exception as e:
            self.logger.error("Failed to trigger event", event=event_type, error=str(e))
            return {"status": "error", "message": str(e)}
    
    async def _deliver_webhook(
        self, 
        webhook: WebhookConfig, 
        event_type: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deliver webhook payload to endpoint"""
        try:
            # Create payload
            payload = WebhookPayload(
                event=event_type,
                timestamp=datetime.now(),
                data=data
            )
            
            # Generate HMAC signature
            payload_json = json.dumps(payload.dict(), default=str)
            signature = hmac.new(
                webhook.secret.encode(),
                payload_json.encode(),
                hashlib.sha256
            ).hexdigest()
            
            payload.signature = signature
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-Event": event_type,
                "X-Webhook-Timestamp": payload.timestamp.isoformat(),
                **webhook.headers
            }
            
            # Attempt delivery with retries
            for attempt in range(webhook.retry_count + 1):
                try:
                    response = await self.http_client.post(
                        str(webhook.url),
                        json=payload.dict(exclude={"signature"}),
                        headers=headers,
                        timeout=webhook.timeout
                    )
                    
                    if response.status_code < 300:
                        # Log successful delivery
                        await self._log_delivery(webhook.id, event_type, "success", response.status_code)
                        
                        self.logger.info(
                            "Webhook delivered",
                            webhook_id=webhook.id,
                            event=event_type,
                            status=response.status_code
                        )
                        
                        return {
                            "webhook_id": webhook.id,
                            "status": "success",
                            "status_code": response.status_code,
                            "attempts": attempt + 1
                        }
                    
                except Exception as delivery_error:
                    if attempt == webhook.retry_count:
                        # Log failed delivery
                        await self._log_delivery(webhook.id, event_type, "failed", 0, str(delivery_error))
                        
                        self.logger.error(
                            "Webhook delivery failed",
                            webhook_id=webhook.id,
                            event=event_type,
                            error=str(delivery_error),
                            attempts=attempt + 1
                        )
                        
                        return {
                            "webhook_id": webhook.id,
                            "status": "failed",
                            "error": str(delivery_error),
                            "attempts": attempt + 1
                        }
                    
                    # Wait before retry (exponential backoff)
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
            
            return {
                "webhook_id": webhook.id,
                "status": "failed",
                "error": "Max retries exceeded"
            }
            
        except Exception as e:
            self.logger.error("Webhook delivery error", webhook_id=webhook.id, error=str(e))
            return {
                "webhook_id": webhook.id,
                "status": "error",
                "error": str(e)
            }
    
    async def _log_delivery(
        self, 
        webhook_id: str, 
        event: str, 
        status: str, 
        status_code: int,
        error: Optional[str] = None
    ):
        """Log webhook delivery attempt"""
        try:
            log_entry = {
                "webhook_id": webhook_id,
                "event": event,
                "status": status,
                "status_code": status_code,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in Redis list (keep last 100 entries per webhook)
            log_key = f"webhook:{webhook_id}:deliveries"
            await self.redis.lpush(log_key, json.dumps(log_entry))
            await self.redis.ltrim(log_key, 0, 99)
            
            # Update webhook stats
            await self.redis.hincrby(f"webhook:{webhook_id}:stats", f"{status}_count", 1)
            
        except Exception as e:
            self.logger.error("Failed to log delivery", error=str(e))
    
    async def get_webhook_stats(self, webhook_id: str) -> Dict[str, Any]:
        """Get webhook delivery statistics"""
        try:
            stats = await self.redis.hgetall(f"webhook:{webhook_id}:stats")
            
            return {
                "success_count": int(stats.get("success_count", 0)),
                "failed_count": int(stats.get("failed_count", 0)),
                "total_deliveries": int(stats.get("success_count", 0)) + int(stats.get("failed_count", 0))
            }
            
        except Exception as e:
            self.logger.error("Failed to get webhook stats", error=str(e))
            return {}
    
    async def get_recent_deliveries(self, webhook_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent webhook deliveries"""
        try:
            deliveries = await self.redis.lrange(f"webhook:{webhook_id}:deliveries", 0, limit - 1)
            
            return [json.loads(d) for d in deliveries]
            
        except Exception as e:
            self.logger.error("Failed to get recent deliveries", error=str(e))
            return []
    
    async def test_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Test webhook with a ping event"""
        webhook = await self.get_webhook(webhook_id)
        
        if not webhook:
            return {"status": "error", "message": "Webhook not found"}
        
        test_data = {
            "test": True,
            "webhook_id": webhook_id,
            "message": "This is a test webhook delivery"
        }
        
        result = await self._deliver_webhook(webhook, "test", test_data)
        
        return result
