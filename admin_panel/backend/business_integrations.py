"""
Business Tool Integrations
Integrate with Slack, PagerDuty, Teams, and other business tools
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from enum import Enum
import json
import httpx
import structlog

logger = structlog.get_logger()


class IntegrationType(str, Enum):
    """Supported integration types"""
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    TEAMS = "teams"
    DISCORD = "discord"
    JIRA = "jira"
    DATADOG = "datadog"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SlackConfig(BaseModel):
    """Slack integration configuration"""
    webhook_url: HttpUrl
    channel: str = Field(description="Slack channel for notifications")
    username: str = Field(default="Messaging Agent Bot")
    icon_emoji: str = Field(default=":robot_face:")
    mention_on_critical: bool = True
    mention_users: List[str] = Field(default_factory=list)


class PagerDutyConfig(BaseModel):
    """PagerDuty integration configuration"""
    integration_key: str
    service_id: str
    escalation_policy: Optional[str] = None
    auto_resolve: bool = True


class TeamsConfig(BaseModel):
    """Microsoft Teams integration configuration"""
    webhook_url: HttpUrl
    channel_id: str
    mention_on_critical: bool = True


class BusinessIntegrationManager:
    """Manage business tool integrations"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.logger = logger
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    # ==================== Slack Integration ====================
    
    async def send_slack_notification(
        self,
        config: SlackConfig,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        fields: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Send notification to Slack"""
        try:
            # Color coding based on severity
            color_map = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ff9900",
                AlertSeverity.ERROR: "#ff0000",
                AlertSeverity.CRITICAL: "#8B0000"
            }
            
            # Prepare message
            text = message
            if severity == AlertSeverity.CRITICAL and config.mention_on_critical:
                mentions = " ".join([f"<@{user}>" for user in config.mention_users])
                if mentions:
                    text = f"{mentions} {message}"
            
            # Build Slack message
            slack_message = {
                "username": config.username,
                "icon_emoji": config.icon_emoji,
                "channel": config.channel,
                "attachments": [
                    {
                        "color": color_map[severity],
                        "title": title,
                        "text": text,
                        "fields": fields or [],
                        "footer": "Messaging Agent Admin",
                        "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            # Send to Slack
            response = await self.http_client.post(
                str(config.webhook_url),
                json=slack_message
            )
            
            if response.status_code == 200:
                self.logger.info("Slack notification sent", title=title, severity=severity.value)
                return {"status": "success", "platform": "slack"}
            else:
                self.logger.error("Slack notification failed", status=response.status_code)
                return {"status": "error", "message": response.text}
                
        except Exception as e:
            self.logger.error("Slack notification error", error=str(e))
            return {"status": "error", "message": str(e)}
    
    async def send_slack_conversation_alert(
        self,
        config: SlackConfig,
        conversation_id: str,
        user_id: str,
        issue: str
    ) -> Dict[str, Any]:
        """Send conversation-specific alert to Slack"""
        fields = [
            {"title": "Conversation ID", "value": conversation_id, "short": True},
            {"title": "User ID", "value": user_id, "short": True},
            {"title": "Issue", "value": issue, "short": False}
        ]
        
        return await self.send_slack_notification(
            config,
            title="⚠️ Conversation Alert",
            message=f"An issue was detected in conversation {conversation_id}",
            severity=AlertSeverity.WARNING,
            fields=fields
        )
    
    async def send_slack_system_alert(
        self,
        config: SlackConfig,
        component: str,
        status: str,
        details: str
    ) -> Dict[str, Any]:
        """Send system alert to Slack"""
        severity = AlertSeverity.CRITICAL if status == "down" else AlertSeverity.WARNING
        
        fields = [
            {"title": "Component", "value": component, "short": True},
            {"title": "Status", "value": status, "short": True},
            {"title": "Details", "value": details, "short": False}
        ]
        
        return await self.send_slack_notification(
            config,
            title="🚨 System Alert" if severity == AlertSeverity.CRITICAL else "⚠️ System Warning",
            message=f"System component '{component}' is {status}",
            severity=severity,
            fields=fields
        )
    
    # ==================== PagerDuty Integration ====================
    
    async def create_pagerduty_incident(
        self,
        config: PagerDutyConfig,
        title: str,
        description: str,
        severity: AlertSeverity,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create incident in PagerDuty"""
        try:
            # Map severity to PagerDuty severity
            pd_severity_map = {
                AlertSeverity.INFO: "info",
                AlertSeverity.WARNING: "warning",
                AlertSeverity.ERROR: "error",
                AlertSeverity.CRITICAL: "critical"
            }
            
            # Build PagerDuty event
            event = {
                "routing_key": config.integration_key,
                "event_action": "trigger",
                "payload": {
                    "summary": title,
                    "severity": pd_severity_map[severity],
                    "source": "Messaging Agent System",
                    "custom_details": details or {}
                },
                "dedup_key": f"msg-agent-{datetime.now().strftime('%Y%m%d')}-{title}"
            }
            
            # Send to PagerDuty Events API
            response = await self.http_client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=event,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 202]:
                result = response.json()
                self.logger.info(
                    "PagerDuty incident created",
                    title=title,
                    dedup_key=result.get("dedup_key")
                )
                return {"status": "success", "platform": "pagerduty", "dedup_key": result.get("dedup_key")}
            else:
                self.logger.error("PagerDuty incident failed", status=response.status_code)
                return {"status": "error", "message": response.text}
                
        except Exception as e:
            self.logger.error("PagerDuty incident error", error=str(e))
            return {"status": "error", "message": str(e)}
    
    async def resolve_pagerduty_incident(
        self,
        config: PagerDutyConfig,
        dedup_key: str
    ) -> Dict[str, Any]:
        """Resolve a PagerDuty incident"""
        try:
            event = {
                "routing_key": config.integration_key,
                "event_action": "resolve",
                "dedup_key": dedup_key
            }
            
            response = await self.http_client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=event,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 202]:
                self.logger.info("PagerDuty incident resolved", dedup_key=dedup_key)
                return {"status": "success", "platform": "pagerduty"}
            else:
                return {"status": "error", "message": response.text}
                
        except Exception as e:
            self.logger.error("PagerDuty resolve error", error=str(e))
            return {"status": "error", "message": str(e)}
    
    # ==================== Microsoft Teams Integration ====================
    
    async def send_teams_notification(
        self,
        config: TeamsConfig,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        facts: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Send notification to Microsoft Teams"""
        try:
            # Color coding
            color_map = {
                AlertSeverity.INFO: "0078D4",
                AlertSeverity.WARNING: "FFA500",
                AlertSeverity.ERROR: "FF0000",
                AlertSeverity.CRITICAL: "8B0000"
            }
            
            # Build Teams adaptive card
            teams_message = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "themeColor": color_map[severity],
                "summary": title,
                "sections": [
                    {
                        "activityTitle": title,
                        "activitySubtitle": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "text": message,
                        "facts": facts or []
                    }
                ]
            }
            
            # Send to Teams
            response = await self.http_client.post(
                str(config.webhook_url),
                json=teams_message
            )
            
            if response.status_code == 200:
                self.logger.info("Teams notification sent", title=title)
                return {"status": "success", "platform": "teams"}
            else:
                self.logger.error("Teams notification failed", status=response.status_code)
                return {"status": "error", "message": response.text}
                
        except Exception as e:
            self.logger.error("Teams notification error", error=str(e))
            return {"status": "error", "message": str(e)}
    
    # ==================== Multi-Platform Broadcast ====================
    
    async def broadcast_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Broadcast alert to all configured platforms"""
        results = []
        
        try:
            # Get all active integrations
            integrations = await self.redis.hgetall("integrations:config")
            
            # Send to Slack if configured
            if "slack" in integrations:
                slack_config = SlackConfig(**json.loads(integrations["slack"]))
                result = await self.send_slack_notification(
                    slack_config,
                    title,
                    message,
                    severity,
                    [{"title": k, "value": str(v), "short": True} for k, v in (details or {}).items()]
                )
                results.append(result)
            
            # Send to PagerDuty if critical
            if severity == AlertSeverity.CRITICAL and "pagerduty" in integrations:
                pd_config = PagerDutyConfig(**json.loads(integrations["pagerduty"]))
                result = await self.create_pagerduty_incident(
                    pd_config,
                    title,
                    message,
                    severity,
                    details
                )
                results.append(result)
            
            # Send to Teams if configured
            if "teams" in integrations:
                teams_config = TeamsConfig(**json.loads(integrations["teams"]))
                result = await self.send_teams_notification(
                    teams_config,
                    title,
                    message,
                    severity,
                    [{"name": k, "value": str(v)} for k, v in (details or {}).items()]
                )
                results.append(result)
            
            self.logger.info("Alert broadcast complete", platforms=len(results), severity=severity.value)
            
            return {
                "status": "success",
                "platforms_notified": len(results),
                "results": results
            }
            
        except Exception as e:
            self.logger.error("Broadcast alert error", error=str(e))
            return {"status": "error", "message": str(e)}
    
    # ==================== Integration Management ====================
    
    async def configure_integration(
        self,
        integration_type: IntegrationType,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Configure a business tool integration"""
        try:
            await self.redis.hset(
                "integrations:config",
                integration_type.value,
                json.dumps(config)
            )
            
            await self.redis.sadd("integrations:active", integration_type.value)
            
            self.logger.info("Integration configured", type=integration_type.value)
            
            return {"status": "success", "integration": integration_type.value}
            
        except Exception as e:
            self.logger.error("Failed to configure integration", error=str(e))
            raise
    
    async def test_integration(self, integration_type: IntegrationType) -> Dict[str, Any]:
        """Test an integration"""
        try:
            integrations = await self.redis.hgetall("integrations:config")
            
            if integration_type.value not in integrations:
                return {"status": "error", "message": "Integration not configured"}
            
            if integration_type == IntegrationType.SLACK:
                config = SlackConfig(**json.loads(integrations["slack"]))
                return await self.send_slack_notification(
                    config,
                    "Test Notification",
                    "This is a test message from Messaging Agent Admin",
                    AlertSeverity.INFO
                )
            elif integration_type == IntegrationType.PAGERDUTY:
                config = PagerDutyConfig(**json.loads(integrations["pagerduty"]))
                result = await self.create_pagerduty_incident(
                    config,
                    "Test Incident",
                    "This is a test incident from Messaging Agent Admin",
                    AlertSeverity.INFO,
                    {"test": True}
                )
                # Auto-resolve test incident
                if result.get("dedup_key"):
                    await self.resolve_pagerduty_incident(config, result["dedup_key"])
                return result
            elif integration_type == IntegrationType.TEAMS:
                config = TeamsConfig(**json.loads(integrations["teams"]))
                return await self.send_teams_notification(
                    config,
                    "Test Notification",
                    "This is a test message from Messaging Agent Admin",
                    AlertSeverity.INFO
                )
            
            return {"status": "error", "message": "Integration type not supported"}
            
        except Exception as e:
            self.logger.error("Failed to test integration", error=str(e))
            return {"status": "error", "message": str(e)}
    
    async def list_integrations(self) -> List[Dict[str, Any]]:
        """List all configured integrations"""
        try:
            active = await self.redis.smembers("integrations:active")
            integrations = []
            
            for integration in active:
                integrations.append({
                    "type": integration,
                    "status": "active"
                })
            
            return integrations
            
        except Exception as e:
            self.logger.error("Failed to list integrations", error=str(e))
            return []
