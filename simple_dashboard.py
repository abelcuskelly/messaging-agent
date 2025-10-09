"""
Simple Analytics Dashboard Server (Local Testing)
Serves the analytics dashboard locally without Google Cloud dependencies
"""

import json
import datetime
import random
import csv
import io
import base64
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import secrets
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

app = FastAPI(title="Qwen Messaging Agent Analytics Dashboard")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Authentication
security = HTTPBasic()
WEBSOCKET_CONNECTIONS = []
ALERT_THRESHOLDS = {
    "success_rate_min": 0.85,
    "avg_duration_max": 5000,
    "sentiment_min": 0.3
}

# Custom branding colors
BRAND_COLORS = {
    "primary": "#667eea",
    "secondary": "#764ba2", 
    "accent": "#f093fb",
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "info": "#17a2b8"
}


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify user credentials."""
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "qwen2024")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


async def broadcast_update(data: Dict[str, Any]):
    """Broadcast updates to all connected WebSocket clients."""
    if WEBSOCKET_CONNECTIONS:
        message = json.dumps(data)
        disconnected = []
        for connection in WEBSOCKET_CONNECTIONS:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            WEBSOCKET_CONNECTIONS.remove(conn)


def check_alerts(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check if any metrics exceed alert thresholds."""
    alerts = []
    overall = data.get("business_metrics", {}).get("overall_metrics", {})
    
    success_rate = overall.get("success_rate", 0)
    if success_rate < ALERT_THRESHOLDS["success_rate_min"]:
        alerts.append({
            "type": "warning",
            "metric": "Success Rate",
            "value": f"{success_rate:.1%}",
            "threshold": f"{ALERT_THRESHOLDS['success_rate_min']:.1%}",
            "message": f"Success rate ({success_rate:.1%}) below threshold ({ALERT_THRESHOLDS['success_rate_min']:.1%})"
        })
    
    avg_duration = overall.get("avg_duration_ms", 0)
    if avg_duration > ALERT_THRESHOLDS["avg_duration_max"]:
        alerts.append({
            "type": "warning",
            "metric": "Average Duration",
            "value": f"{avg_duration:.0f}ms",
            "threshold": f"{ALERT_THRESHOLDS['avg_duration_max']:.0f}ms",
            "message": f"Average response time ({avg_duration:.0f}ms) above threshold ({ALERT_THRESHOLDS['avg_duration_max']:.0f}ms)"
        })
    
    # Check sentiment
    sentiment_data = data.get("sentiment_trends", {}).get("daily_sentiment", [])
    if sentiment_data:
        avg_sentiment = sum(d["avg_sentiment"] for d in sentiment_data) / len(sentiment_data)
        if avg_sentiment < ALERT_THRESHOLDS["sentiment_min"]:
            alerts.append({
                "type": "danger",
                "metric": "Customer Sentiment",
                "value": f"{avg_sentiment:.2f}",
                "threshold": f"{ALERT_THRESHOLDS['sentiment_min']:.2f}",
                "message": f"Customer sentiment ({avg_sentiment:.2f}) below threshold ({ALERT_THRESHOLDS['sentiment_min']:.2f})"
            })
    
    return alerts


def generate_sample_data(start_date: Optional[datetime.datetime] = None, end_date: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """Generate realistic sample data for the dashboard."""
    
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = datetime.datetime.now()
    if not start_date:
        start_date = end_date - datetime.timedelta(days=30)
    
    # Generate daily metrics for the specified period
    daily_metrics = []
    current_date = start_date
    days_diff = (end_date - start_date).days
    
    for i in range(days_diff + 1):
        total_convs = random.randint(40, 80)
        success_rate = random.uniform(0.85, 0.98)
        successful_convs = int(total_convs * success_rate)
        
        daily_metrics.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "total_conversations": total_convs,
            "successful_conversations": successful_convs,
            "failed_conversations": total_convs - successful_convs,
            "success_rate": success_rate,
            "avg_duration": random.randint(2000, 4000),
            "avg_message_length": random.randint(20, 40),
            "avg_response_length": random.randint(100, 200),
            "unique_conversations": int(total_convs * 0.9)
        })
        current_date += datetime.timedelta(days=1)
    
    # Calculate overall metrics
    total_convs = sum(d["total_conversations"] for d in daily_metrics)
    successful_convs = sum(d["successful_conversations"] for d in daily_metrics)
    avg_duration = sum(d["avg_duration"] for d in daily_metrics) / len(daily_metrics)
    
    # Generate conversation flows
    flows = [
        {
            "flow_type": "short_conversation",
            "count": int(total_convs * 0.5),
            "avg_duration": 1800,
            "avg_messages": 3.2
        },
        {
            "flow_type": "medium_conversation", 
            "count": int(total_convs * 0.35),
            "avg_duration": 3500,
            "avg_messages": 7.8
        },
        {
            "flow_type": "single_message",
            "count": int(total_convs * 0.1),
            "avg_duration": 1200,
            "avg_messages": 1.0
        },
        {
            "flow_type": "long_conversation",
            "count": int(total_convs * 0.05),
            "avg_duration": 6000,
            "avg_messages": 15.2
        }
    ]
    
    # Generate sentiment trends
    daily_sentiment = []
    for i, day in enumerate(daily_metrics):
        # Vary sentiment slightly day by day
        base_sentiment = random.uniform(0.3, 0.8)
        daily_sentiment.append({
            "date": day["date"],
            "avg_sentiment": base_sentiment,
            "sentiment_label": "positive" if base_sentiment > 0.5 else "neutral",
            "message_count": day["total_conversations"]
        })
    
    # Generate sample topics
    sample_topics = [
        {
            "user_message": "I need help with my Lakers tickets",
            "agent_response": "I'd be happy to help you with your Lakers tickets. What specific assistance do you need?",
            "frequency": random.randint(50, 150)
        },
        {
            "user_message": "Can I upgrade my seat?",
            "agent_response": "Absolutely! I can help you upgrade your seat. Let me check what options are available.",
            "frequency": random.randint(30, 100)
        },
        {
            "user_message": "What time does the game start?",
            "agent_response": "The game starts at 7:30 PM. Gates open at 6:00 PM for early entry.",
            "frequency": random.randint(40, 120)
        },
        {
            "user_message": "I lost my ticket confirmation",
            "agent_response": "No worries! I can help you retrieve your ticket confirmation. What's your email address?",
            "frequency": random.randint(20, 80)
        },
        {
            "user_message": "Can I get a refund?",
            "agent_response": "I can help you with refund options. Refunds are available up to 48 hours before the event.",
            "frequency": random.randint(15, 60)
        }
    ]
    
    return {
        "business_metrics": {
            "overall_metrics": {
                "total_conversations": total_convs,
                "successful_conversations": successful_convs,
                "success_rate": successful_convs / total_convs,
                "avg_duration_ms": avg_duration,
                "period_days": 30
            },
            "daily_metrics": daily_metrics
        },
        "conversation_flows": {
            "flows": flows
        },
        "sentiment_trends": {
            "daily_sentiment": daily_sentiment
        },
        "topics": {
            "topics": sample_topics
        },
        "generated_at": datetime.datetime.utcnow().isoformat()
    }


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, username: str = Depends(verify_credentials)):
    """Main dashboard page with authentication."""
    try:
        with open("templates/dashboard.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    WEBSOCKET_CONNECTIONS.append(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        WEBSOCKET_CONNECTIONS.remove(websocket)


@app.get("/api/dashboard")
async def get_full_dashboard(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    username: str = Depends(verify_credentials)
):
    """Get complete dashboard data as JSON with date range support."""
    try:
        # Parse date parameters
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        
        dashboard_data = generate_sample_data(start_dt, end_dt)
        
        # Add alerts
        alerts = check_alerts(dashboard_data)
        dashboard_data["alerts"] = alerts
        
        # Broadcast update to WebSocket clients
        await broadcast_update({
            "type": "dashboard_update",
            "data": dashboard_data,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        
        return JSONResponse(content=dashboard_data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/metrics")
async def get_metrics():
    """Get business metrics as JSON."""
    try:
        data = generate_sample_data()
        return JSONResponse(content=data["business_metrics"])
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/flows")
async def get_conversation_flows():
    """Get conversation flow analysis as JSON."""
    try:
        data = generate_sample_data()
        return JSONResponse(content=data["conversation_flows"])
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/sentiment")
async def get_sentiment_analysis():
    """Get sentiment analysis as JSON."""
    try:
        data = generate_sample_data()
        return JSONResponse(content=data["sentiment_trends"])
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/topics")
async def get_topics():
    """Get conversation topics as JSON."""
    try:
        data = generate_sample_data()
        return JSONResponse(content=data["topics"])
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/export/csv")
async def export_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    username: str = Depends(verify_credentials)
):
    """Export dashboard data as CSV."""
    try:
        # Parse date parameters
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        
        data = generate_sample_data(start_dt, end_dt)
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Date", "Total Conversations", "Successful", "Failed", 
            "Success Rate", "Avg Duration (ms)", "Avg Message Length", 
            "Avg Response Length", "Unique Conversations"
        ])
        
        # Write data
        for day in data["business_metrics"]["daily_metrics"]:
            writer.writerow([
                day["date"],
                day["total_conversations"],
                day["successful_conversations"],
                day["failed_conversations"],
                f"{day['success_rate']:.2%}",
                day["avg_duration"],
                day["avg_message_length"],
                day["avg_response_length"],
                day["unique_conversations"]
            ])
        
        # Return CSV file
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=dashboard_export.csv"}
        )
        
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/export/pdf")
async def export_pdf(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    username: str = Depends(verify_credentials)
):
    """Export dashboard data as PDF report."""
    try:
        # Parse date parameters
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        
        data = generate_sample_data(start_dt, end_dt)
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor(BRAND_COLORS["primary"])
        )
        story.append(Paragraph("Qwen Messaging Agent Analytics Report", title_style))
        story.append(Spacer(1, 12))
        
        # Date range
        date_range = f"Report Period: {start_dt.strftime('%Y-%m-%d') if start_dt else 'Last 30 days'} to {end_dt.strftime('%Y-%m-%d') if end_dt else 'Today'}"
        story.append(Paragraph(date_range, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Key metrics
        story.append(Paragraph("Key Metrics", styles['Heading2']))
        overall = data["business_metrics"]["overall_metrics"]
        
        metrics_data = [
            ["Metric", "Value"],
            ["Total Conversations", str(overall["total_conversations"])],
            ["Success Rate", f"{overall['success_rate']:.1%}"],
            ["Average Duration", f"{overall['avg_duration_ms']:.0f} ms"],
            ["Period (Days)", str(overall["period_days"])]
        ]
        
        metrics_table = Table(metrics_data)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BRAND_COLORS["primary"])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 20))
        
        # Alerts
        alerts = data.get("alerts", [])
        if alerts:
            story.append(Paragraph("Active Alerts", styles['Heading2']))
            for alert in alerts:
                alert_text = f"• {alert['message']}"
                story.append(Paragraph(alert_text, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(buffer.getvalue()),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=dashboard_report.pdf"}
        )
        
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/drill-down/{metric}")
async def get_drill_down(
    metric: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    username: str = Depends(verify_credentials)
):
    """Get detailed drill-down data for a specific metric."""
    try:
        # Parse date parameters
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        
        data = generate_sample_data(start_dt, end_dt)
        
        # Generate detailed breakdown based on metric
        if metric == "conversations":
            drill_data = {
                "metric": "Conversations",
                "breakdown": [
                    {"category": "Ticket Purchase", "count": int(data["business_metrics"]["overall_metrics"]["total_conversations"] * 0.4)},
                    {"category": "Seat Upgrade", "count": int(data["business_metrics"]["overall_metrics"]["total_conversations"] * 0.3)},
                    {"category": "General Support", "count": int(data["business_metrics"]["overall_metrics"]["total_conversations"] * 0.2)},
                    {"category": "Refund Requests", "count": int(data["business_metrics"]["overall_metrics"]["total_conversations"] * 0.1)}
                ]
            }
        elif metric == "sentiment":
            drill_data = {
                "metric": "Sentiment",
                "breakdown": [
                    {"category": "Very Positive", "count": 45, "percentage": 0.36},
                    {"category": "Positive", "count": 35, "percentage": 0.28},
                    {"category": "Neutral", "count": 30, "percentage": 0.24},
                    {"category": "Negative", "count": 10, "percentage": 0.08},
                    {"category": "Very Negative", "count": 5, "percentage": 0.04}
                ]
            }
        else:
            drill_data = {"error": "Unknown metric"}
        
        return JSONResponse(content=drill_data)
        
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/alerts")
async def get_alerts(username: str = Depends(verify_credentials)):
    """Get current alert status."""
    try:
        data = generate_sample_data()
        alerts = check_alerts(data)
        return JSONResponse(content={"alerts": alerts, "thresholds": ALERT_THRESHOLDS})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    args = parser.parse_args()
    
    print(f"🚀 Starting Qwen Messaging Agent Analytics Dashboard")
    print(f"📊 Dashboard URL: http://{args.host}:{args.port}")
    print(f"🔗 API Endpoints:")
    print(f"   - /api/dashboard - Complete dashboard data")
    print(f"   - /api/metrics - Business metrics")
    print(f"   - /api/flows - Conversation flows")
    print(f"   - /api/sentiment - Sentiment analysis")
    print(f"   - /api/topics - Conversation topics")
    print(f"   - /health - Health check")
    print(f"\n✨ Features:")
    print(f"   - Real-time conversation metrics")
    print(f"   - Interactive charts and visualizations")
    print(f"   - Sentiment analysis trends")
    print(f"   - Conversation flow patterns")
    print(f"   - Top conversation topics")
    print(f"   - Auto-refresh every 5 minutes")
    
    uvicorn.run(app, host=args.host, port=args.port, reload=True)
