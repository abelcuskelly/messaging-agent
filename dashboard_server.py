"""
Analytics Dashboard Server
Serves the analytics dashboard locally for development and testing
"""

import os
import json
import datetime
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from analytics import BusinessIntelligence, ConversationFlowAnalyzer, SentimentAnalyzer, create_analytics_dashboard

app = FastAPI(title="Qwen Messaging Agent Analytics Dashboard")

# Mount static files (for CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates for HTML rendering
templates = Jinja2Templates(directory="templates")

# Initialize analytics components
bi = BusinessIntelligence()
flow_analyzer = ConversationFlowAnalyzer()
sentiment_analyzer = SentimentAnalyzer()


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page."""
    try:
        # Get dashboard data
        dashboard_data = bi.create_dashboard_data(days=30)
        
        # Create HTML dashboard
        dashboard_html = create_analytics_dashboard(dashboard_data)
        
        if dashboard_html:
            with open(dashboard_html, "r") as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        else:
            return HTMLResponse(content="<h1>Dashboard Error</h1><p>Failed to generate dashboard</p>")
            
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")


@app.get("/api/metrics")
async def get_metrics(days: int = 30):
    """Get business metrics as JSON."""
    try:
        metrics = bi.get_business_metrics(days=days)
        return JSONResponse(content=metrics)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/flows")
async def get_conversation_flows(days: int = 7):
    """Get conversation flow analysis as JSON."""
    try:
        flows = flow_analyzer.analyze_conversation_flows(days=days)
        return JSONResponse(content=flows)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/sentiment")
async def get_sentiment_analysis(days: int = 7):
    """Get sentiment analysis as JSON."""
    try:
        sentiment_trends = bi._calculate_sentiment_trends(days=days)
        return JSONResponse(content=sentiment_trends)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/topics")
async def get_topics(days: int = 7):
    """Get conversation topics as JSON."""
    try:
        topics = flow_analyzer.get_conversation_topics(days=days)
        return JSONResponse(content=topics)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/dashboard")
async def get_full_dashboard(days: int = 30):
    """Get complete dashboard data as JSON."""
    try:
        dashboard_data = bi.create_dashboard_data(days=days)
        return JSONResponse(content=dashboard_data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}


def create_sample_data():
    """Create sample data for testing the dashboard."""
    # This would normally come from BigQuery, but for testing we'll create sample data
    sample_data = {
        "business_metrics": {
            "overall_metrics": {
                "total_conversations": 1250,
                "successful_conversations": 1180,
                "success_rate": 0.944,
                "avg_duration_ms": 2500,
                "period_days": 30
            },
            "daily_metrics": [
                {
                    "date": "2024-01-01",
                    "total_conversations": 45,
                    "successful_conversations": 42,
                    "failed_conversations": 3,
                    "success_rate": 0.933,
                    "avg_duration": 2400,
                    "avg_message_length": 25,
                    "avg_response_length": 150,
                    "unique_conversations": 40
                },
                {
                    "date": "2024-01-02",
                    "total_conversations": 52,
                    "successful_conversations": 49,
                    "failed_conversations": 3,
                    "success_rate": 0.942,
                    "avg_duration": 2600,
                    "avg_message_length": 28,
                    "avg_response_length": 145,
                    "unique_conversations": 48
                }
            ]
        },
        "conversation_flows": {
            "flows": [
                {
                    "flow_type": "short_conversation",
                    "count": 650,
                    "avg_duration": 1800,
                    "avg_messages": 3.2
                },
                {
                    "flow_type": "medium_conversation",
                    "count": 420,
                    "avg_duration": 3500,
                    "avg_messages": 7.8
                },
                {
                    "flow_type": "single_message",
                    "count": 180,
                    "avg_duration": 1200,
                    "avg_messages": 1.0
                }
            ]
        },
        "sentiment_trends": {
            "daily_sentiment": [
                {
                    "date": "2024-01-01",
                    "avg_sentiment": 0.65,
                    "sentiment_label": "positive",
                    "message_count": 45
                },
                {
                    "date": "2024-01-02",
                    "avg_sentiment": 0.72,
                    "sentiment_label": "positive",
                    "message_count": 52
                }
            ]
        },
        "generated_at": datetime.datetime.utcnow().isoformat()
    }
    
    # Save sample data to file
    with open("sample_dashboard_data.json", "w") as f:
        json.dump(sample_data, f, indent=2, default=str)
    
    return sample_data


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--create-sample", action="store_true", help="Create sample data for testing")
    args = parser.parse_args()
    
    if args.create_sample:
        print("Creating sample data...")
        create_sample_data()
        print("Sample data created in sample_dashboard_data.json")
    
    print(f"Starting analytics dashboard server on http://{args.host}:{args.port}")
    print("Available endpoints:")
    print("  / - Main dashboard")
    print("  /api/metrics - Business metrics")
    print("  /api/flows - Conversation flows")
    print("  /api/sentiment - Sentiment analysis")
    print("  /api/topics - Conversation topics")
    print("  /api/dashboard - Complete dashboard data")
    print("  /health - Health check")
    
    uvicorn.run(app, host=args.host, port=args.port, reload=True)
