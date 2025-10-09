"""
Integration Ecosystem for the messaging agent
- Webhook support for external system notifications
- Zapier/IFTTT-style integrations
- Slack/Teams bot integration for internal support
"""

import os
import json
import hmac
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Callable
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
import httpx
import structlog
from google.cloud import secretmanager

logger = structlog.get_logger()


class WebhookManager:
    """Manage webhook subscriptions and notifications."""
    
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("PROJECT_ID")
        self.webhooks: Dict[str, Dict[str, Any]] = {}
        self.secret_client = secretmanager.SecretManagerServiceClient()
    
    def register_webhook(
        self,
        webhook_id: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Register a webhook subscription."""
        try:
            self.webhooks[webhook_id] = {
                "url": url,
                "events": events,
                "secret": secret,
                "headers": headers or {},
                "active": True,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
            
            logger.info("Webhook registered", webhook_id=webhook_id, url=url, events=events)
            return True
            
        except Exception as e:
            logger.error("Webhook registration failed", error=str(e))
            return False
    
    def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook subscription."""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            logger.info("Webhook unregistered", webhook_id=webhook_id)
            return True
        return False
    
    async def send_webhook(self, event_type: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Send webhook notifications for an event."""
        results = []
        
        for webhook_id, webhook in self.webhooks.items():
            if not webhook["active"] or event_type not in webhook["events"]:
                continue
            
            try:
                payload = {
                    "event": event_type,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "data": data
                }
                
                # Sign payload if secret is provided
                if webhook["secret"]:
                    signature = self._sign_payload(json.dumps(payload), webhook["secret"])
                    webhook["headers"]["X-Webhook-Signature"] = signature
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        webhook["url"],
                        json=payload,
                        headers=webhook["headers"],
                        timeout=10.0
                    )
                
                results.append({
                    "webhook_id": webhook_id,
                    "status_code": response.status_code,
                    "success": response.status_code < 400
                })
                
                logger.info("Webhook sent", 
                           webhook_id=webhook_id, 
                           event=event_type, 
                           status=response.status_code)
                
            except Exception as e:
                logger.error("Webhook delivery failed", 
                           webhook_id=webhook_id, 
                           error=str(e))
                results.append({
                    "webhook_id": webhook_id,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def _sign_payload(self, payload: str, secret: str) -> str:
        """Sign webhook payload with HMAC-SHA256."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()


class ZapierIntegration:
    """Zapier-style integration for external services."""
    
    def __init__(self, webhook_manager: WebhookManager):
        self.webhook_manager = webhook_manager
    
    def create_zapier_trigger(self, trigger_name: str, webhook_url: str) -> Dict[str, Any]:
        """Create a Zapier trigger for external integrations."""
        webhook_id = f"zapier_{trigger_name}"
        
        success = self.webhook_manager.register_webhook(
            webhook_id=webhook_id,
            url=webhook_url,
            events=["conversation_completed", "ticket_purchased", "ticket_upgraded", "error_occurred"]
        )
        
        if success:
            return {
                "trigger_id": webhook_id,
                "webhook_url": f"https://your-api.com/webhooks/{webhook_id}",
                "events": ["conversation_completed", "ticket_purchased", "ticket_upgraded", "error_occurred"],
                "status": "active"
            }
        
        return {"error": "Failed to create Zapier trigger"}
    
    async def handle_zapier_webhook(self, webhook_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming Zapier webhook."""
        try:
            # Process Zapier webhook data
            event_type = payload.get("event", "unknown")
            data = payload.get("data", {})
            
            # Log the integration event
            logger.info("Zapier webhook received", 
                       webhook_id=webhook_id, 
                       event=event_type, 
                       data_keys=list(data.keys()))
            
            # Process based on event type
            if event_type == "conversation_completed":
                return await self._handle_conversation_completed(data)
            elif event_type == "ticket_purchased":
                return await self._handle_ticket_purchased(data)
            elif event_type == "ticket_upgraded":
                return await self._handle_ticket_upgraded(data)
            else:
                return {"status": "ignored", "reason": f"Unknown event type: {event_type}"}
                
        except Exception as e:
            logger.error("Zapier webhook handling failed", error=str(e))
            return {"error": str(e)}
    
    async def _handle_conversation_completed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversation completed event."""
        # Example: Send to CRM, update customer records, etc.
        return {"status": "processed", "action": "conversation_logged"}
    
    async def _handle_ticket_purchased(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ticket purchase event."""
        # Example: Send confirmation email, update inventory, etc.
        return {"status": "processed", "action": "ticket_confirmed"}
    
    async def _handle_ticket_upgraded(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ticket upgrade event."""
        # Example: Send upgrade confirmation, process refund, etc.
        return {"status": "processed", "action": "upgrade_processed"}


class SlackBot:
    """Slack bot integration for internal support."""
    
    def __init__(self, bot_token: str, signing_secret: str):
        self.bot_token = bot_token
        self.signing_secret = signing_secret
        self.client = httpx.AsyncClient()
    
    async def send_message(self, channel: str, text: str, blocks: Optional[List[Dict]] = None) -> bool:
        """Send a message to a Slack channel."""
        try:
            payload = {
                "channel": channel,
                "text": text,
                "token": self.bot_token
            }
            
            if blocks:
                payload["blocks"] = blocks
            
            response = await self.client.post(
                "https://slack.com/api/chat.postMessage",
                json=payload
            )
            
            result = response.json()
            success = result.get("ok", False)
            
            if success:
                logger.info("Slack message sent", channel=channel)
            else:
                logger.error("Slack message failed", error=result.get("error"))
            
            return success
            
        except Exception as e:
            logger.error("Slack message sending failed", error=str(e))
            return False
    
    async def handle_slack_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming Slack events."""
        try:
            event_type = event.get("type")
            
            if event_type == "app_mention":
                return await self._handle_mention(event)
            elif event_type == "message":
                return await self._handle_message(event)
            else:
                return {"status": "ignored", "reason": f"Unknown event type: {event_type}"}
                
        except Exception as e:
            logger.error("Slack event handling failed", error=str(e))
            return {"error": str(e)}
    
    async def _handle_mention(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Slack app mention."""
        text = event.get("text", "")
        channel = event.get("channel")
        
        # Process the mention and respond
        response_text = f"Hello! I'm the Qwen messaging agent. How can I help with ticketing support?"
        
        await self.send_message(channel, response_text)
        
        return {"status": "processed", "action": "mention_responded"}
    
    async def _handle_message(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Slack direct message."""
        text = event.get("text", "")
        channel = event.get("channel")
        
        # Process the message and respond
        response_text = f"I received your message: {text}. This is a placeholder response."
        
        await self.send_message(channel, response_text)
        
        return {"status": "processed", "action": "message_responded"}


class TeamsBot:
    """Microsoft Teams bot integration."""
    
    def __init__(self, bot_id: str, bot_password: str):
        self.bot_id = bot_id
        self.bot_password = bot_password
        self.client = httpx.AsyncClient()
    
    async def send_message(self, service_url: str, conversation_id: str, text: str) -> bool:
        """Send a message to a Teams conversation."""
        try:
            url = f"{service_url}/v3/conversations/{conversation_id}/activities"
            
            payload = {
                "type": "message",
                "text": text
            }
            
            response = await self.client.post(url, json=payload)
            
            success = response.status_code < 400
            if success:
                logger.info("Teams message sent", conversation_id=conversation_id)
            else:
                logger.error("Teams message failed", status=response.status_code)
            
            return success
            
        except Exception as e:
            logger.error("Teams message sending failed", error=str(e))
            return False
    
    async def handle_teams_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming Teams events."""
        try:
            event_type = event.get("type")
            
            if event_type == "message":
                return await self._handle_message(event)
            else:
                return {"status": "ignored", "reason": f"Unknown event type: {event_type}"}
                
        except Exception as e:
            logger.error("Teams event handling failed", error=str(e))
            return {"error": str(e)}
    
    async def _handle_message(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Teams message."""
        text = event.get("text", "")
        service_url = event.get("serviceUrl")
        conversation_id = event.get("conversation", {}).get("id")
        
        # Process the message and respond
        response_text = f"I received your message: {text}. This is a placeholder response."
        
        await self.send_message(service_url, conversation_id, response_text)
        
        return {"status": "processed", "action": "message_responded"}


class IntegrationAPI:
    """FastAPI endpoints for integrations."""
    
    def __init__(self, webhook_manager: WebhookManager, zapier: ZapierIntegration, slack_bot: SlackBot, teams_bot: TeamsBot):
        self.webhook_manager = webhook_manager
        self.zapier = zapier
        self.slack_bot = slack_bot
        self.teams_bot = teams_bot
        self.app = FastAPI()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes for integrations."""
        
        @self.app.post("/webhooks/register")
        async def register_webhook(request: Request):
            data = await request.json()
            success = self.webhook_manager.register_webhook(
                webhook_id=data["webhook_id"],
                url=data["url"],
                events=data["events"],
                secret=data.get("secret"),
                headers=data.get("headers", {})
            )
            return {"success": success}
        
        @self.app.post("/webhooks/{webhook_id}")
        async def handle_webhook(webhook_id: str, request: Request):
            payload = await request.json()
            return await self.zapier.handle_zapier_webhook(webhook_id, payload)
        
        @self.app.post("/slack/events")
        async def handle_slack_events(request: Request):
            event = await request.json()
            return await self.slack_bot.handle_slack_event(event)
        
        @self.app.post("/teams/events")
        async def handle_teams_events(request: Request):
            event = await request.json()
            return await self.teams_bot.handle_teams_event(event)
        
        @self.app.get("/integrations/status")
        async def get_integrations_status():
            return {
                "webhooks": len(self.webhook_manager.webhooks),
                "slack_bot": "active" if self.slack_bot.bot_token else "inactive",
                "teams_bot": "active" if self.teams_bot.bot_id else "inactive"
            }


def create_integration_ecosystem() -> IntegrationAPI:
    """Create the complete integration ecosystem."""
    webhook_manager = WebhookManager()
    zapier = ZapierIntegration(webhook_manager)
    
    # Initialize bots (tokens from environment or Secret Manager)
    slack_bot = SlackBot(
        bot_token=os.getenv("SLACK_BOT_TOKEN", ""),
        signing_secret=os.getenv("SLACK_SIGNING_SECRET", "")
    )
    
    teams_bot = TeamsBot(
        bot_id=os.getenv("TEAMS_BOT_ID", ""),
        bot_password=os.getenv("TEAMS_BOT_PASSWORD", "")
    )
    
    return IntegrationAPI(webhook_manager, zapier, slack_bot, teams_bot)


# Example usage and setup
if __name__ == "__main__":
    import uvicorn
    
    # Create integration ecosystem
    integration_api = create_integration_ecosystem()
    
    # Run the integration API server
    uvicorn.run(integration_api.app, host="0.0.0.0", port=8081)
