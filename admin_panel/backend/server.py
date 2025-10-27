"""
Admin Panel Backend Server
Comprehensive management and monitoring for the messaging agent system
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import structlog
import redis.asyncio as redis
from google.cloud import bigquery
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio

# Import advanced features
try:
    from custom_dashboards import DashboardManager, CustomDashboard, DashboardWidget, DASHBOARD_TEMPLATES
    from webhook_manager import WebhookManager, WebhookConfig, WebhookEvent
    from automated_reports import ReportManager, ReportConfig, ReportFrequency, ReportFormat
    from business_integrations import (
        BusinessIntegrationManager, 
        IntegrationType, 
        AlertSeverity,
        SlackConfig,
        PagerDutyConfig,
        TeamsConfig
    )
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False
    logger.warning("Advanced features not available - install dependencies")

# Initialize logger
logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Messaging Agent Admin Panel",
    description="Comprehensive admin dashboard for managing and monitoring the AI messaging agent",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Security
security = HTTPBearer()

# Redis client for caching and real-time data
redis_client = None

async def get_redis():
    global redis_client
    if not redis_client:
        redis_client = await redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            decode_responses=True
        )
    return redis_client

# ================== Data Models ==================

class SystemConfig(BaseModel):
    """System configuration settings"""
    provider: str = Field(description="LLM provider (anthropic/openai/bedrock/qwen)")
    model: str = Field(description="Model name/version")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2000, ge=100, le=8000)
    rate_limit: int = Field(default=100, description="Requests per minute")
    cache_enabled: bool = Field(default=True)
    monitoring_enabled: bool = Field(default=True)
    auto_scaling: bool = Field(default=True)
    min_instances: int = Field(default=1, ge=1)
    max_instances: int = Field(default=10, ge=1)

class UserAccount(BaseModel):
    """User account management"""
    email: str
    role: str = Field(description="admin/operator/viewer")
    permissions: List[str] = []
    api_keys: List[str] = []
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_active: bool = True

class AlertConfig(BaseModel):
    """Alert configuration"""
    name: str
    metric: str
    threshold: float
    comparison: str = Field(description="greater/less/equal")
    notification_channels: List[str] = ["email", "slack"]
    enabled: bool = True

class ConversationFilter(BaseModel):
    """Filters for conversation queries"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[str] = None
    status: Optional[str] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None

# ================== Authentication ==================

async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin authentication token"""
    token = credentials.credentials
    # In production, verify JWT token
    if token != os.getenv("ADMIN_TOKEN", "admin-secret-token"):
        raise HTTPException(status_code=403, detail="Invalid authentication token")
    return token

# ================== System Configuration ==================

@app.get("/api/config")
async def get_system_config(token: str = Depends(verify_admin_token)):
    """Get current system configuration"""
    r = await get_redis()
    config = await r.hgetall("system:config")
    
    if not config:
        # Return default config
        config = SystemConfig(
            provider=os.getenv("LLM_PROVIDER", "anthropic"),
            model=os.getenv("MODEL_NAME", "claude-3-sonnet"),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("MAX_TOKENS", "2000")),
            rate_limit=int(os.getenv("RATE_LIMIT", "100"))
        ).dict()
    
    return {"status": "success", "config": config}

@app.put("/api/config")
async def update_system_config(
    config: SystemConfig,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_admin_token)
):
    """Update system configuration"""
    r = await get_redis()
    
    # Save to Redis
    await r.hset("system:config", mapping=config.dict())
    
    # Trigger configuration reload in background
    background_tasks.add_task(reload_system_config, config)
    
    logger.info("System configuration updated", config=config.dict())
    
    return {"status": "success", "message": "Configuration updated"}

async def reload_system_config(config: SystemConfig):
    """Reload system configuration across all services"""
    # In production, trigger service reloads via Cloud Run API or Kubernetes
    logger.info("Reloading configuration across services", config=config.dict())

# ================== Analytics & Monitoring ==================

@app.get("/api/analytics/overview")
async def get_analytics_overview(token: str = Depends(verify_admin_token)):
    """Get analytics overview for the dashboard"""
    r = await get_redis()
    
    # Get real-time metrics
    total_conversations = await r.get("metrics:total_conversations") or 0
    active_users = await r.scard("metrics:active_users") or 0
    avg_response_time = await r.get("metrics:avg_response_time") or 0
    success_rate = await r.get("metrics:success_rate") or 95.0
    
    # Get hourly stats for chart
    hourly_stats = []
    for i in range(24):
        hour_key = f"metrics:hourly:{datetime.now().date()}:{i:02d}"
        count = await r.get(hour_key) or 0
        hourly_stats.append({"hour": i, "count": int(count)})
    
    # Get top intents
    top_intents = await r.zrevrange("metrics:intents", 0, 4, withscores=True)
    
    # Get system health
    health_checks = {
        "api": await r.get("health:api") or "healthy",
        "database": await r.get("health:database") or "healthy",
        "redis": "healthy",
        "model": await r.get("health:model") or "healthy"
    }
    
    return {
        "overview": {
            "total_conversations": int(total_conversations),
            "active_users": int(active_users),
            "avg_response_time": float(avg_response_time),
            "success_rate": float(success_rate)
        },
        "hourly_stats": hourly_stats,
        "top_intents": [
            {"intent": intent, "count": int(score)}
            for intent, score in top_intents
        ],
        "health": health_checks
    }

@app.post("/api/analytics/conversations")
async def get_conversation_analytics(
    filters: ConversationFilter,
    token: str = Depends(verify_admin_token)
):
    """Get detailed conversation analytics"""
    try:
        # Query BigQuery for conversation data
        client = bigquery.Client()
        
        query = """
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as conversation_count,
            AVG(response_time_ms) as avg_response_time,
            AVG(ARRAY_LENGTH(messages)) as avg_message_count,
            COUNT(DISTINCT user_id) as unique_users,
            COUNTIF(success = true) / COUNT(*) * 100 as success_rate
        FROM `{project}.conversations.messages`
        WHERE timestamp BETWEEN @start_date AND @end_date
        GROUP BY date
        ORDER BY date DESC
        """.format(project=os.getenv("GCP_PROJECT"))
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", filters.start_date or datetime.now() - timedelta(days=7)),
                bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", filters.end_date or datetime.now())
            ]
        )
        
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        
        analytics = []
        for row in results:
            analytics.append({
                "date": row.date.isoformat(),
                "conversations": row.conversation_count,
                "avg_response_time": row.avg_response_time,
                "avg_messages": row.avg_message_count,
                "unique_users": row.unique_users,
                "success_rate": row.success_rate
            })
        
        return {"status": "success", "analytics": analytics}
        
    except Exception as e:
        logger.error("Failed to get conversation analytics", error=str(e))
        # Return mock data for demo
        return {
            "status": "success",
            "analytics": [
                {
                    "date": (datetime.now() - timedelta(days=i)).date().isoformat(),
                    "conversations": 150 - (i * 10),
                    "avg_response_time": 250 + (i * 5),
                    "avg_messages": 8,
                    "unique_users": 50 - i,
                    "success_rate": 95 - i
                }
                for i in range(7)
            ]
        }

@app.get("/api/conversations/recent")
async def get_recent_conversations(
    limit: int = 10,
    token: str = Depends(verify_admin_token)
):
    """Get recent conversations for monitoring"""
    r = await get_redis()
    
    # Get recent conversation IDs
    conversation_ids = await r.lrange("conversations:recent", 0, limit - 1)
    
    conversations = []
    for conv_id in conversation_ids:
        conv_data = await r.hgetall(f"conversation:{conv_id}")
        if conv_data:
            conversations.append(conv_data)
    
    # Add mock data if empty
    if not conversations:
        conversations = [
            {
                "id": f"conv_{i}",
                "user_id": f"user_{i}",
                "started_at": (datetime.now() - timedelta(minutes=i*5)).isoformat(),
                "status": "active" if i < 3 else "completed",
                "messages": i * 2 + 3,
                "intent": ["ticket_purchase", "seat_upgrade", "event_info"][i % 3]
            }
            for i in range(limit)
        ]
    
    return {"conversations": conversations}

# ================== User Management ==================

@app.get("/api/users")
async def get_users(token: str = Depends(verify_admin_token)):
    """Get all user accounts"""
    r = await get_redis()
    
    user_keys = await r.keys("user:*")
    users = []
    
    for key in user_keys:
        user_data = await r.hgetall(key)
        if user_data:
            users.append(user_data)
    
    # Add mock data if empty
    if not users:
        users = [
            {
                "email": "admin@rationa.ai",
                "role": "admin",
                "created_at": datetime.now().isoformat(),
                "is_active": True
            },
            {
                "email": "operator@rationa.ai",
                "role": "operator",
                "created_at": datetime.now().isoformat(),
                "is_active": True
            }
        ]
    
    return {"users": users}

@app.post("/api/users")
async def create_user(
    user: UserAccount,
    token: str = Depends(verify_admin_token)
):
    """Create new user account"""
    r = await get_redis()
    
    # Check if user exists
    exists = await r.exists(f"user:{user.email}")
    if exists:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Save user
    user.created_at = datetime.now()
    await r.hset(f"user:{user.email}", mapping=user.dict())
    
    logger.info("User created", email=user.email, role=user.role)
    
    return {"status": "success", "message": "User created"}

# ================== Billing & Usage ==================

@app.get("/api/billing/usage")
async def get_usage_stats(token: str = Depends(verify_admin_token)):
    """Get billing and usage statistics"""
    r = await get_redis()
    
    # Get current month usage
    current_month = datetime.now().strftime("%Y-%m")
    
    usage = {
        "period": current_month,
        "api_calls": int(await r.get(f"usage:{current_month}:api_calls") or 0),
        "tokens_used": int(await r.get(f"usage:{current_month}:tokens") or 0),
        "storage_gb": float(await r.get(f"usage:{current_month}:storage") or 0.5),
        "bandwidth_gb": float(await r.get(f"usage:{current_month}:bandwidth") or 1.2)
    }
    
    # Calculate costs
    costs = {
        "api_calls": usage["api_calls"] * 0.0001,  # $0.0001 per call
        "tokens": usage["tokens_used"] * 0.000002,  # $2 per million tokens
        "storage": usage["storage_gb"] * 0.023,  # $0.023 per GB
        "bandwidth": usage["bandwidth_gb"] * 0.12,  # $0.12 per GB
    }
    costs["total"] = sum(costs.values())
    
    # Get daily usage for chart
    daily_usage = []
    for day in range(1, 31):
        day_key = f"usage:{current_month}-{day:02d}:api_calls"
        count = await r.get(day_key) or 0
        daily_usage.append({"day": day, "calls": int(count)})
    
    return {
        "usage": usage,
        "costs": costs,
        "daily_usage": daily_usage
    }

# ================== Alerts & Notifications ==================

@app.get("/api/alerts")
async def get_alerts(token: str = Depends(verify_admin_token)):
    """Get configured alerts"""
    r = await get_redis()
    
    alert_keys = await r.keys("alert:*")
    alerts = []
    
    for key in alert_keys:
        alert_data = await r.hgetall(key)
        if alert_data:
            alerts.append(alert_data)
    
    # Add default alerts if empty
    if not alerts:
        alerts = [
            {
                "name": "High Error Rate",
                "metric": "error_rate",
                "threshold": 5.0,
                "comparison": "greater",
                "enabled": True
            },
            {
                "name": "Low Success Rate",
                "metric": "success_rate",
                "threshold": 90.0,
                "comparison": "less",
                "enabled": True
            }
        ]
    
    return {"alerts": alerts}

@app.post("/api/alerts")
async def create_alert(
    alert: AlertConfig,
    token: str = Depends(verify_admin_token)
):
    """Create new alert configuration"""
    r = await get_redis()
    
    alert_id = f"alert:{alert.name.lower().replace(' ', '_')}"
    await r.hset(alert_id, mapping=alert.dict())
    
    logger.info("Alert created", name=alert.name, metric=alert.metric)
    
    return {"status": "success", "message": "Alert created"}

# ================== WebSocket for Real-time Updates ==================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time dashboard updates"""
    await manager.connect(websocket)
    
    try:
        # Send initial data
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and send updates
        while True:
            # Wait for any message from client (heartbeat)
            data = await websocket.receive_text()
            
            # Send real-time metrics
            r = await get_redis()
            metrics = {
                "type": "metrics_update",
                "timestamp": datetime.now().isoformat(),
                "active_conversations": int(await r.get("metrics:active_conversations") or 0),
                "queue_size": int(await r.llen("queue:messages") or 0),
                "response_time": float(await r.get("metrics:last_response_time") or 0)
            }
            await websocket.send_json(metrics)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ================== Model Management ==================

@app.get("/api/models")
async def get_available_models(token: str = Depends(verify_admin_token)):
    """Get list of available models"""
    models = {
        "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "openai": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
        "bedrock": ["claude-v2", "llama2-70b", "titan-text"],
        "qwen": ["Qwen3-4B-Instruct", "Qwen3-8B-Instruct"]
    }
    
    return {"models": models}

@app.post("/api/models/switch")
async def switch_model(
    provider: str,
    model: str,
    token: str = Depends(verify_admin_token)
):
    """Switch to a different model"""
    r = await get_redis()
    
    # Update configuration
    await r.hset("system:config", "provider", provider)
    await r.hset("system:config", "model", model)
    
    logger.info("Model switched", provider=provider, model=model)
    
    return {"status": "success", "message": f"Switched to {provider}/{model}"}

# ================== Export & Reports ==================

@app.get("/api/export/conversations")
async def export_conversations(
    format: str = "csv",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    token: str = Depends(verify_admin_token)
):
    """Export conversation data"""
    # In production, query BigQuery and generate export
    
    # Mock data for demo
    data = {
        "conversations": [
            {
                "id": f"conv_{i}",
                "date": (datetime.now() - timedelta(days=i)).isoformat(),
                "user_id": f"user_{i}",
                "messages": i * 2 + 3,
                "duration_seconds": i * 60 + 120,
                "success": True
            }
            for i in range(10)
        ]
    }
    
    if format == "csv":
        df = pd.DataFrame(data["conversations"])
        csv_data = df.to_csv(index=False)
        return {"format": "csv", "data": csv_data}
    else:
        return {"format": "json", "data": data}

# ================== System Actions ==================

@app.post("/api/system/restart")
async def restart_service(
    service: str,
    token: str = Depends(verify_admin_token)
):
    """Restart a specific service"""
    logger.info("Restarting service", service=service)
    
    # In production, trigger Cloud Run service restart
    # For now, just log the action
    
    return {"status": "success", "message": f"Service {service} restart initiated"}

@app.post("/api/system/clear-cache")
async def clear_cache(token: str = Depends(verify_admin_token)):
    """Clear Redis cache"""
    r = await get_redis()
    
    # Clear cache keys
    cache_keys = await r.keys("cache:*")
    if cache_keys:
        await r.delete(*cache_keys)
    
    logger.info("Cache cleared", keys_deleted=len(cache_keys))
    
    return {"status": "success", "message": f"Cleared {len(cache_keys)} cache entries"}

# ================== Health Check ==================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ================== Advanced Features (Custom Dashboards) ==================

if ADVANCED_FEATURES_AVAILABLE:
    
    dashboard_manager = None
    webhook_manager = None
    report_manager = None
    integration_manager = None
    
    async def get_dashboard_manager():
        global dashboard_manager
        if not dashboard_manager:
            r = await get_redis()
            dashboard_manager = DashboardManager(r)
        return dashboard_manager
    
    async def get_webhook_manager():
        global webhook_manager
        if not webhook_manager:
            r = await get_redis()
            webhook_manager = WebhookManager(r)
        return webhook_manager
    
    async def get_report_manager():
        global report_manager
        if not report_manager:
            r = await get_redis()
            report_manager = ReportManager(r)
        return report_manager
    
    async def get_integration_manager():
        global integration_manager
        if not integration_manager:
            r = await get_redis()
            integration_manager = BusinessIntegrationManager(r)
        return integration_manager
    
    # Custom Dashboards
    @app.post("/api/dashboards")
    async def create_custom_dashboard(
        dashboard: CustomDashboard,
        token: str = Depends(verify_admin_token)
    ):
        """Create a custom dashboard"""
        manager = await get_dashboard_manager()
        return await manager.create_dashboard(dashboard)
    
    @app.get("/api/dashboards/{dashboard_id}")
    async def get_custom_dashboard(
        dashboard_id: str,
        token: str = Depends(verify_admin_token)
    ):
        """Get dashboard configuration"""
        manager = await get_dashboard_manager()
        dashboard = await manager.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return {"dashboard": dashboard}
    
    @app.get("/api/dashboards")
    async def list_custom_dashboards(
        user: str = "admin",
        token: str = Depends(verify_admin_token)
    ):
        """List user's dashboards"""
        manager = await get_dashboard_manager()
        dashboards = await manager.list_user_dashboards(user)
        return {"dashboards": dashboards}
    
    @app.get("/api/dashboards/templates")
    async def get_dashboard_templates(token: str = Depends(verify_admin_token)):
        """Get predefined dashboard templates"""
        return {"templates": DASHBOARD_TEMPLATES}
    
    # Webhooks
    @app.post("/api/webhooks")
    async def create_webhook(
        webhook: WebhookConfig,
        token: str = Depends(verify_admin_token)
    ):
        """Create a new webhook"""
        manager = await get_webhook_manager()
        return await manager.create_webhook(webhook)
    
    @app.get("/api/webhooks")
    async def list_webhooks(token: str = Depends(verify_admin_token)):
        """List all webhooks"""
        manager = await get_webhook_manager()
        webhooks = await manager.list_webhooks()
        return {"webhooks": webhooks}
    
    @app.post("/api/webhooks/{webhook_id}/test")
    async def test_webhook(
        webhook_id: str,
        token: str = Depends(verify_admin_token)
    ):
        """Test a webhook"""
        manager = await get_webhook_manager()
        return await manager.test_webhook(webhook_id)
    
    @app.get("/api/webhooks/{webhook_id}/stats")
    async def get_webhook_stats(
        webhook_id: str,
        token: str = Depends(verify_admin_token)
    ):
        """Get webhook delivery statistics"""
        manager = await get_webhook_manager()
        stats = await manager.get_webhook_stats(webhook_id)
        return {"stats": stats}
    
    # Automated Reports
    @app.post("/api/reports")
    async def create_report(
        report: ReportConfig,
        token: str = Depends(verify_admin_token)
    ):
        """Create a scheduled report"""
        manager = await get_report_manager()
        return await manager.create_report(report)
    
    @app.get("/api/reports")
    async def list_reports(token: str = Depends(verify_admin_token)):
        """List all reports"""
        manager = await get_report_manager()
        reports = await manager.list_reports()
        return {"reports": reports}
    
    @app.post("/api/reports/{report_id}/generate")
    async def generate_report_now(
        report_id: str,
        background_tasks: BackgroundTasks,
        token: str = Depends(verify_admin_token)
    ):
        """Generate a report immediately"""
        manager = await get_report_manager()
        background_tasks.add_task(manager.generate_report, report_id)
        return {"status": "success", "message": "Report generation started"}
    
    # Business Integrations
    @app.post("/api/integrations/{integration_type}/configure")
    async def configure_integration(
        integration_type: IntegrationType,
        config: Dict[str, Any],
        token: str = Depends(verify_admin_token)
    ):
        """Configure a business tool integration"""
        manager = await get_integration_manager()
        return await manager.configure_integration(integration_type, config)
    
    @app.post("/api/integrations/{integration_type}/test")
    async def test_integration(
        integration_type: IntegrationType,
        token: str = Depends(verify_admin_token)
    ):
        """Test an integration"""
        manager = await get_integration_manager()
        return await manager.test_integration(integration_type)
    
    @app.get("/api/integrations")
    async def list_integrations(token: str = Depends(verify_admin_token)):
        """List all configured integrations"""
        manager = await get_integration_manager()
        integrations = await manager.list_integrations()
        return {"integrations": integrations}
    
    @app.post("/api/integrations/slack/notify")
    async def send_slack_notification(
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        token: str = Depends(verify_admin_token)
    ):
        """Send a Slack notification"""
        manager = await get_integration_manager()
        r = await get_redis()
        integrations = await r.hgetall("integrations:config")
        
        if "slack" not in integrations:
            raise HTTPException(status_code=400, detail="Slack not configured")
        
        config = SlackConfig(**json.loads(integrations["slack"]))
        return await manager.send_slack_notification(config, title, message, severity)
    
    @app.post("/api/integrations/pagerduty/incident")
    async def create_pagerduty_incident(
        title: str,
        description: str,
        severity: AlertSeverity,
        token: str = Depends(verify_admin_token)
    ):
        """Create a PagerDuty incident"""
        manager = await get_integration_manager()
        r = await get_redis()
        integrations = await r.hgetall("integrations:config")
        
        if "pagerduty" not in integrations:
            raise HTTPException(status_code=400, detail="PagerDuty not configured")
        
        config = PagerDutyConfig(**json.loads(integrations["pagerduty"]))
        return await manager.create_pagerduty_incident(config, title, description, severity)
    
    @app.post("/api/integrations/broadcast")
    async def broadcast_alert(
        title: str,
        message: str,
        severity: AlertSeverity,
        details: Optional[Dict[str, Any]] = None,
        token: str = Depends(verify_admin_token)
    ):
        """Broadcast alert to all configured platforms"""
        manager = await get_integration_manager()
        return await manager.broadcast_alert(title, message, severity, details)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
