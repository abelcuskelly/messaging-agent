"""
Custom Dashboard Builder
Create and manage custom dashboards with drag-and-drop widgets
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import structlog

logger = structlog.get_logger()


class DashboardWidget(BaseModel):
    """Widget configuration for custom dashboards"""
    id: str
    type: str = Field(description="Widget type: metric, chart, table, map, etc.")
    title: str
    position: Dict[str, int] = Field(description="x, y, width, height")
    data_source: str = Field(description="Data source for the widget")
    config: Dict[str, Any] = Field(default_factory=dict)
    refresh_interval: int = Field(default=30, description="Refresh interval in seconds")


class CustomDashboard(BaseModel):
    """Custom dashboard configuration"""
    id: str
    name: str
    description: Optional[str] = None
    owner: str
    widgets: List[DashboardWidget]
    layout: str = Field(default="grid", description="Layout type: grid, flex, etc.")
    is_public: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DashboardManager:
    """Manage custom dashboards"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.logger = logger
    
    async def create_dashboard(self, dashboard: CustomDashboard) -> Dict[str, Any]:
        """Create a new custom dashboard"""
        try:
            # Save dashboard configuration
            dashboard_key = f"dashboard:{dashboard.id}"
            await self.redis.hset(
                dashboard_key,
                mapping={
                    "name": dashboard.name,
                    "description": dashboard.description or "",
                    "owner": dashboard.owner,
                    "widgets": json.dumps([w.dict() for w in dashboard.widgets]),
                    "layout": dashboard.layout,
                    "is_public": str(dashboard.is_public),
                    "created_at": dashboard.created_at.isoformat(),
                    "updated_at": dashboard.updated_at.isoformat()
                }
            )
            
            # Add to user's dashboard list
            await self.redis.sadd(f"user:{dashboard.owner}:dashboards", dashboard.id)
            
            # Add to public dashboards if public
            if dashboard.is_public:
                await self.redis.sadd("dashboards:public", dashboard.id)
            
            self.logger.info("Dashboard created", dashboard_id=dashboard.id, owner=dashboard.owner)
            
            return {"status": "success", "dashboard_id": dashboard.id}
            
        except Exception as e:
            self.logger.error("Failed to create dashboard", error=str(e))
            raise
    
    async def get_dashboard(self, dashboard_id: str) -> Optional[CustomDashboard]:
        """Get dashboard configuration"""
        try:
            dashboard_data = await self.redis.hgetall(f"dashboard:{dashboard_id}")
            
            if not dashboard_data:
                return None
            
            # Parse widgets
            widgets = json.loads(dashboard_data.get("widgets", "[]"))
            
            return CustomDashboard(
                id=dashboard_id,
                name=dashboard_data["name"],
                description=dashboard_data.get("description"),
                owner=dashboard_data["owner"],
                widgets=[DashboardWidget(**w) for w in widgets],
                layout=dashboard_data.get("layout", "grid"),
                is_public=dashboard_data.get("is_public") == "True",
                created_at=datetime.fromisoformat(dashboard_data["created_at"]),
                updated_at=datetime.fromisoformat(dashboard_data["updated_at"])
            )
            
        except Exception as e:
            self.logger.error("Failed to get dashboard", dashboard_id=dashboard_id, error=str(e))
            return None
    
    async def update_dashboard(self, dashboard_id: str, dashboard: CustomDashboard) -> Dict[str, Any]:
        """Update existing dashboard"""
        try:
            dashboard.updated_at = datetime.now()
            
            await self.redis.hset(
                f"dashboard:{dashboard_id}",
                mapping={
                    "name": dashboard.name,
                    "description": dashboard.description or "",
                    "widgets": json.dumps([w.dict() for w in dashboard.widgets]),
                    "layout": dashboard.layout,
                    "is_public": str(dashboard.is_public),
                    "updated_at": dashboard.updated_at.isoformat()
                }
            )
            
            self.logger.info("Dashboard updated", dashboard_id=dashboard_id)
            
            return {"status": "success", "dashboard_id": dashboard_id}
            
        except Exception as e:
            self.logger.error("Failed to update dashboard", error=str(e))
            raise
    
    async def delete_dashboard(self, dashboard_id: str, owner: str) -> Dict[str, Any]:
        """Delete a dashboard"""
        try:
            # Verify ownership
            dashboard = await self.get_dashboard(dashboard_id)
            if not dashboard or dashboard.owner != owner:
                return {"status": "error", "message": "Dashboard not found or access denied"}
            
            # Delete dashboard
            await self.redis.delete(f"dashboard:{dashboard_id}")
            await self.redis.srem(f"user:{owner}:dashboards", dashboard_id)
            await self.redis.srem("dashboards:public", dashboard_id)
            
            self.logger.info("Dashboard deleted", dashboard_id=dashboard_id)
            
            return {"status": "success"}
            
        except Exception as e:
            self.logger.error("Failed to delete dashboard", error=str(e))
            raise
    
    async def list_user_dashboards(self, user: str) -> List[Dict[str, Any]]:
        """List all dashboards for a user"""
        try:
            dashboard_ids = await self.redis.smembers(f"user:{user}:dashboards")
            
            dashboards = []
            for dashboard_id in dashboard_ids:
                dashboard = await self.get_dashboard(dashboard_id)
                if dashboard:
                    dashboards.append({
                        "id": dashboard.id,
                        "name": dashboard.name,
                        "description": dashboard.description,
                        "is_public": dashboard.is_public,
                        "widget_count": len(dashboard.widgets),
                        "updated_at": dashboard.updated_at.isoformat()
                    })
            
            return dashboards
            
        except Exception as e:
            self.logger.error("Failed to list dashboards", error=str(e))
            return []
    
    async def get_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Fetch data for a specific widget"""
        try:
            # Route to appropriate data source
            if widget.data_source == "conversations":
                return await self._get_conversation_data(widget)
            elif widget.data_source == "metrics":
                return await self._get_metrics_data(widget)
            elif widget.data_source == "users":
                return await self._get_user_data(widget)
            elif widget.data_source == "billing":
                return await self._get_billing_data(widget)
            else:
                return {"error": "Unknown data source"}
                
        except Exception as e:
            self.logger.error("Failed to get widget data", widget_id=widget.id, error=str(e))
            return {"error": str(e)}
    
    async def _get_conversation_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get conversation data for widget"""
        # Implementation depends on widget.config
        metric = widget.config.get("metric", "total")
        
        if metric == "total":
            total = await self.redis.get("metrics:total_conversations") or 0
            return {"value": int(total)}
        elif metric == "active":
            active = await self.redis.get("metrics:active_conversations") or 0
            return {"value": int(active)}
        elif metric == "hourly":
            # Get hourly stats
            hourly = []
            for i in range(24):
                count = await self.redis.get(f"metrics:hourly:{datetime.now().date()}:{i:02d}") or 0
                hourly.append({"hour": i, "count": int(count)})
            return {"data": hourly}
        
        return {}
    
    async def _get_metrics_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get general metrics data"""
        metric = widget.config.get("metric")
        
        value = await self.redis.get(f"metrics:{metric}") or 0
        return {"value": float(value)}
    
    async def _get_user_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get user-related data"""
        active_users = await self.redis.scard("metrics:active_users") or 0
        return {"value": int(active_users)}
    
    async def _get_billing_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get billing data"""
        current_month = datetime.now().strftime("%Y-%m")
        api_calls = await self.redis.get(f"usage:{current_month}:api_calls") or 0
        tokens = await self.redis.get(f"usage:{current_month}:tokens") or 0
        
        return {
            "api_calls": int(api_calls),
            "tokens": int(tokens),
            "cost": int(api_calls) * 0.0001 + int(tokens) * 0.000002
        }


# Predefined dashboard templates
DASHBOARD_TEMPLATES = {
    "executive": {
        "name": "Executive Dashboard",
        "description": "High-level overview for executives",
        "widgets": [
            {
                "id": "exec-1",
                "type": "metric",
                "title": "Total Conversations",
                "position": {"x": 0, "y": 0, "width": 3, "height": 2},
                "data_source": "conversations",
                "config": {"metric": "total"}
            },
            {
                "id": "exec-2",
                "type": "metric",
                "title": "Active Users",
                "position": {"x": 3, "y": 0, "width": 3, "height": 2},
                "data_source": "users",
                "config": {}
            },
            {
                "id": "exec-3",
                "type": "chart",
                "title": "Conversation Trends",
                "position": {"x": 0, "y": 2, "width": 6, "height": 4},
                "data_source": "conversations",
                "config": {"metric": "hourly", "chart_type": "line"}
            },
            {
                "id": "exec-4",
                "type": "metric",
                "title": "Monthly Cost",
                "position": {"x": 6, "y": 0, "width": 3, "height": 2},
                "data_source": "billing",
                "config": {}
            }
        ]
    },
    "operations": {
        "name": "Operations Dashboard",
        "description": "System health and performance monitoring",
        "widgets": [
            {
                "id": "ops-1",
                "type": "metric",
                "title": "Avg Response Time",
                "position": {"x": 0, "y": 0, "width": 3, "height": 2},
                "data_source": "metrics",
                "config": {"metric": "avg_response_time"}
            },
            {
                "id": "ops-2",
                "type": "metric",
                "title": "Success Rate",
                "position": {"x": 3, "y": 0, "width": 3, "height": 2},
                "data_source": "metrics",
                "config": {"metric": "success_rate"}
            },
            {
                "id": "ops-3",
                "type": "table",
                "title": "Recent Errors",
                "position": {"x": 0, "y": 2, "width": 6, "height": 4},
                "data_source": "errors",
                "config": {"limit": 10}
            }
        ]
    },
    "customer_support": {
        "name": "Customer Support Dashboard",
        "description": "Active conversations and customer insights",
        "widgets": [
            {
                "id": "cs-1",
                "type": "table",
                "title": "Active Conversations",
                "position": {"x": 0, "y": 0, "width": 6, "height": 6},
                "data_source": "conversations",
                "config": {"status": "active", "limit": 20}
            },
            {
                "id": "cs-2",
                "type": "chart",
                "title": "Top Intents",
                "position": {"x": 6, "y": 0, "width": 3, "height": 3},
                "data_source": "intents",
                "config": {"chart_type": "pie"}
            }
        ]
    }
}
