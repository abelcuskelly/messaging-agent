"""
Advanced Analytics for the messaging agent
- Conversation flow analysis
- Sentiment analysis and customer satisfaction tracking
- Business intelligence dashboards
"""

import os
import json
import datetime
from typing import Dict, List, Any, Optional
from google.cloud import bigquery, language_v1
from google.cloud import monitoring_v3
import structlog
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

logger = structlog.get_logger()


class ConversationFlowAnalyzer:
    """Analyze conversation flows and patterns."""
    
    def __init__(self, project_id: Optional[str] = None, dataset_id: str = "messaging_logs"):
        self.project_id = project_id or os.getenv("PROJECT_ID")
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=self.project_id)
    
    def analyze_conversation_flows(self, days: int = 7) -> Dict[str, Any]:
        """Analyze conversation flows and common patterns."""
        query = f"""
        WITH conversation_flows AS (
            SELECT 
                conversation_id,
                ARRAY_AGG(user_message ORDER BY timestamp) as user_messages,
                ARRAY_AGG(agent_response ORDER BY timestamp) as agent_responses,
                COUNT(*) as message_count,
                AVG(duration_ms) as avg_duration,
                MIN(timestamp) as start_time,
                MAX(timestamp) as end_time
            FROM `{self.project_id}.{self.dataset_id}.conversations`
            WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
            GROUP BY conversation_id
        ),
        flow_patterns AS (
            SELECT 
                CASE 
                    WHEN message_count = 1 THEN 'single_message'
                    WHEN message_count BETWEEN 2 AND 5 THEN 'short_conversation'
                    WHEN message_count BETWEEN 6 AND 10 THEN 'medium_conversation'
                    ELSE 'long_conversation'
                END as flow_type,
                COUNT(*) as count,
                AVG(avg_duration) as avg_duration,
                AVG(message_count) as avg_messages
            FROM conversation_flows
            GROUP BY flow_type
        )
        SELECT * FROM flow_patterns
        ORDER BY count DESC
        """
        
        try:
            results = self.client.query(query).result()
            flows = []
            for row in results:
                flows.append({
                    "flow_type": row.flow_type,
                    "count": row.count,
                    "avg_duration": row.avg_duration,
                    "avg_messages": row.avg_messages
                })
            
            logger.info("Conversation flow analysis completed", flows_count=len(flows))
            return {"flows": flows}
            
        except Exception as e:
            logger.error("Conversation flow analysis failed", error=str(e))
            return {"error": str(e)}
    
    def get_conversation_topics(self, days: int = 7) -> Dict[str, Any]:
        """Analyze common conversation topics and keywords."""
        query = f"""
        SELECT 
            user_message,
            agent_response,
            COUNT(*) as frequency
        FROM `{self.project_id}.{self.dataset_id}.conversations`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY user_message, agent_response
        ORDER BY frequency DESC
        LIMIT 100
        """
        
        try:
            results = self.client.query(query).result()
            topics = []
            for row in results:
                topics.append({
                    "user_message": row.user_message,
                    "agent_response": row.agent_response,
                    "frequency": row.frequency
                })
            
            return {"topics": topics}
            
        except Exception as e:
            logger.error("Topic analysis failed", error=str(e))
            return {"error": str(e)}


class SentimentAnalyzer:
    """Analyze sentiment and customer satisfaction."""
    
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("PROJECT_ID")
        self.client = language_v1.LanguageServiceClient()
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using Google Natural Language API."""
        try:
            document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
            response = self.client.analyze_sentiment(request={'document': document})
            
            sentiment = response.document_sentiment
            
            return {
                "score": sentiment.score,  # -1 to 1
                "magnitude": sentiment.magnitude,  # 0 to infinity
                "sentiment_label": self._get_sentiment_label(sentiment.score)
            }
            
        except Exception as e:
            logger.error("Sentiment analysis failed", error=str(e))
            return {"error": str(e)}
    
    def _get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label."""
        if score > 0.25:
            return "positive"
        elif score < -0.25:
            return "negative"
        else:
            return "neutral"
    
    def analyze_conversation_sentiment(self, conversation_id: str, project_id: str, dataset_id: str = "messaging_logs") -> Dict[str, Any]:
        """Analyze sentiment for a specific conversation."""
        client = bigquery.Client(project=project_id)
        
        query = f"""
        SELECT user_message, agent_response, timestamp
        FROM `{project_id}.{dataset_id}.conversations`
        WHERE conversation_id = @conversation_id
        ORDER BY timestamp
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("conversation_id", "STRING", conversation_id)
            ]
        )
        
        try:
            results = client.query(query, job_config=job_config).result()
            
            sentiments = []
            for row in results:
                user_sentiment = self.analyze_sentiment(row.user_message)
                agent_sentiment = self.analyze_sentiment(row.agent_response)
                
                sentiments.append({
                    "timestamp": row.timestamp.isoformat(),
                    "user_message": row.user_message,
                    "user_sentiment": user_sentiment,
                    "agent_response": row.agent_response,
                    "agent_sentiment": agent_sentiment
                })
            
            # Calculate overall conversation sentiment
            user_scores = [s["user_sentiment"].get("score", 0) for s in sentiments if "score" in s["user_sentiment"]]
            overall_sentiment = sum(user_scores) / len(user_scores) if user_scores else 0
            
            return {
                "conversation_id": conversation_id,
                "overall_sentiment": overall_sentiment,
                "sentiment_label": self._get_sentiment_label(overall_sentiment),
                "message_sentiments": sentiments
            }
            
        except Exception as e:
            logger.error("Conversation sentiment analysis failed", error=str(e))
            return {"error": str(e)}


class BusinessIntelligence:
    """Business intelligence and analytics dashboard."""
    
    def __init__(self, project_id: Optional[str] = None, dataset_id: str = "messaging_logs"):
        self.project_id = project_id or os.getenv("PROJECT_ID")
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=self.project_id)
        self.sentiment_analyzer = SentimentAnalyzer(project_id)
    
    def get_business_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive business metrics."""
        query = f"""
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as total_conversations,
            COUNTIF(status = 'success') as successful_conversations,
            COUNTIF(status = 'error') as failed_conversations,
            AVG(duration_ms) as avg_duration,
            AVG(message_length) as avg_message_length,
            AVG(response_length) as avg_response_length,
            COUNT(DISTINCT conversation_id) as unique_conversations
        FROM `{self.project_id}.{self.dataset_id}.conversations`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        """
        
        try:
            results = self.client.query(query).result()
            metrics = []
            for row in results:
                metrics.append({
                    "date": row.date.isoformat(),
                    "total_conversations": row.total_conversations,
                    "successful_conversations": row.successful_conversations,
                    "failed_conversations": row.failed_conversations,
                    "success_rate": row.successful_conversations / row.total_conversations if row.total_conversations > 0 else 0,
                    "avg_duration": row.avg_duration,
                    "avg_message_length": row.avg_message_length,
                    "avg_response_length": row.avg_response_length,
                    "unique_conversations": row.unique_conversations
                })
            
            # Calculate overall metrics
            total_convs = sum(m["total_conversations"] for m in metrics)
            successful_convs = sum(m["successful_conversations"] for m in metrics)
            avg_duration = sum(m["avg_duration"] for m in metrics) / len(metrics) if metrics else 0
            
            overall_metrics = {
                "total_conversations": total_convs,
                "successful_conversations": successful_convs,
                "success_rate": successful_convs / total_convs if total_convs > 0 else 0,
                "avg_duration_ms": avg_duration,
                "period_days": days
            }
            
            return {
                "daily_metrics": metrics,
                "overall_metrics": overall_metrics
            }
            
        except Exception as e:
            logger.error("Business metrics calculation failed", error=str(e))
            return {"error": str(e)}
    
    def create_dashboard_data(self, days: int = 30) -> Dict[str, Any]:
        """Create data for business intelligence dashboard."""
        try:
            # Get business metrics
            business_metrics = self.get_business_metrics(days)
            
            # Get conversation flows
            flow_analyzer = ConversationFlowAnalyzer(self.project_id)
            flow_analysis = flow_analyzer.analyze_conversation_flows(days)
            
            # Get topics
            topics_analysis = flow_analyzer.get_conversation_topics(days)
            
            # Calculate sentiment trends
            sentiment_trends = self._calculate_sentiment_trends(days)
            
            dashboard_data = {
                "business_metrics": business_metrics,
                "conversation_flows": flow_analysis,
                "topics": topics_analysis,
                "sentiment_trends": sentiment_trends,
                "generated_at": datetime.datetime.utcnow().isoformat()
            }
            
            logger.info("Dashboard data generated", days=days)
            return dashboard_data
            
        except Exception as e:
            logger.error("Dashboard data generation failed", error=str(e))
            return {"error": str(e)}
    
    def _calculate_sentiment_trends(self, days: int) -> Dict[str, Any]:
        """Calculate sentiment trends over time."""
        query = f"""
        SELECT 
            DATE(timestamp) as date,
            user_message,
            COUNT(*) as frequency
        FROM `{self.project_id}.{self.dataset_id}.conversations`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY DATE(timestamp), user_message
        ORDER BY date DESC, frequency DESC
        """
        
        try:
            results = self.client.query(query).result()
            
            daily_sentiments = {}
            for row in results:
                date_str = row.date.isoformat()
                if date_str not in daily_sentiments:
                    daily_sentiments[date_str] = []
                
                sentiment = self.sentiment_analyzer.analyze_sentiment(row.user_message)
                if "score" in sentiment:
                    daily_sentiments[date_str].append({
                        "message": row.user_message,
                        "sentiment_score": sentiment["score"],
                        "frequency": row.frequency
                    })
            
            # Calculate daily average sentiment
            sentiment_trends = []
            for date, messages in daily_sentiments.items():
                if messages:
                    weighted_sentiment = sum(
                        msg["sentiment_score"] * msg["frequency"] 
                        for msg in messages
                    ) / sum(msg["frequency"] for msg in messages)
                    
                    sentiment_trends.append({
                        "date": date,
                        "avg_sentiment": weighted_sentiment,
                        "sentiment_label": self.sentiment_analyzer._get_sentiment_label(weighted_sentiment),
                        "message_count": len(messages)
                    })
            
            return {"daily_sentiment": sentiment_trends}
            
        except Exception as e:
            logger.error("Sentiment trends calculation failed", error=str(e))
            return {"error": str(e)}
    
    def export_dashboard_data(self, days: int = 30, output_path: str = "dashboard_data.json"):
        """Export dashboard data to JSON file."""
        try:
            dashboard_data = self.create_dashboard_data(days)
            
            with open(output_path, "w") as f:
                json.dump(dashboard_data, f, indent=2, default=str)
            
            logger.info("Dashboard data exported", output_path=output_path)
            return output_path
            
        except Exception as e:
            logger.error("Dashboard data export failed", error=str(e))
            return None


def create_analytics_dashboard(dashboard_data: Dict[str, Any]) -> str:
    """Create an HTML dashboard from analytics data."""
    try:
        # Create conversation flow chart
        flows = dashboard_data.get("conversation_flows", {}).get("flows", [])
        if flows:
            flow_df = pd.DataFrame(flows)
            flow_fig = px.bar(flow_df, x="flow_type", y="count", title="Conversation Flow Distribution")
            flow_chart = flow_fig.to_html(include_plotlyjs="cdn")
        else:
            flow_chart = "<p>No conversation flow data available</p>"
        
        # Create sentiment trends chart
        sentiment_trends = dashboard_data.get("sentiment_trends", {}).get("daily_sentiment", [])
        if sentiment_trends:
            sentiment_df = pd.DataFrame(sentiment_trends)
            sentiment_fig = px.line(sentiment_df, x="date", y="avg_sentiment", title="Daily Sentiment Trends")
            sentiment_chart = sentiment_fig.to_html(include_plotlyjs="cdn")
        else:
            sentiment_chart = "<p>No sentiment data available</p>"
        
        # Create HTML dashboard
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Qwen Messaging Agent Analytics Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric-card {{ 
                    background: #f5f5f5; 
                    padding: 20px; 
                    margin: 10px 0; 
                    border-radius: 8px; 
                    display: inline-block;
                    min-width: 200px;
                }}
                .chart-container {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>Qwen Messaging Agent Analytics Dashboard</h1>
            
            <h2>Business Metrics</h2>
            <div class="metric-card">
                <h3>Overall Performance</h3>
                <p>Total Conversations: {dashboard_data.get('business_metrics', {}).get('overall_metrics', {}).get('total_conversations', 0)}</p>
                <p>Success Rate: {dashboard_data.get('business_metrics', {}).get('overall_metrics', {}).get('success_rate', 0):.2%}</p>
                <p>Avg Duration: {dashboard_data.get('business_metrics', {}).get('overall_metrics', {}).get('avg_duration_ms', 0):.0f}ms</p>
            </div>
            
            <h2>Conversation Flows</h2>
            <div class="chart-container">
                {flow_chart}
            </div>
            
            <h2>Sentiment Trends</h2>
            <div class="chart-container">
                {sentiment_chart}
            </div>
            
            <p><em>Generated at: {dashboard_data.get('generated_at', 'Unknown')}</em></p>
        </body>
        </html>
        """
        
        # Save dashboard
        dashboard_path = "analytics_dashboard.html"
        with open(dashboard_path, "w") as f:
            f.write(html_content)
        
        logger.info("Analytics dashboard created", path=dashboard_path)
        return dashboard_path
        
    except Exception as e:
        logger.error("Dashboard creation failed", error=str(e))
        return None
