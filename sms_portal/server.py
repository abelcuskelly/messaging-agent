"""
SMS Portal Server
Web-based interface for SMS testing and customer usage observation
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio
from collections import deque
import os

# Import SMS manager (with graceful fallback)
try:
    from integrations.twilio_integration import get_sms_manager
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("⚠️  Twilio not available - using mock SMS manager")

# Mock SMS manager for testing without Twilio
class MockSMSManager:
    def __init__(self):
        self.messages = deque(maxlen=100)  # Keep last 100 messages
    
    def send_sms(self, to: str, body: str):
        """Mock SMS sending."""
        msg_id = f"SM{'mock' + str(len(self.messages)):06d}"
        message = {
            "sid": msg_id,
            "to": to,
            "from": "+15551111111",
            "body": body,
            "status": "delivered",
            "sent_at": datetime.now().isoformat(),
            "price": "0.00"
        }
        self.messages.append(message)
        return type('obj', (object,), message)()
    
    def get_stats(self):
        """Mock statistics."""
        return {
            "total_sent": len(self.messages),
            "total_failed": 0,
            "success_rate": 1.0,
            "last_24h": len(self.messages)
        }
    
    def get_messages(self, limit=50):
        """Get recent messages."""
        return list(self.messages)[-limit:]


# Initialize FastAPI app
app = FastAPI(title="SMS Portal", description="Testing and monitoring portal for SMS")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active websocket connections
active_connections: List[WebSocket] = []

# Request models
class SendSMSRequest(BaseModel):
    to: str
    body: str
    message_type: str = "test"


class BulkSMSTestRequest(BaseModel):
    recipients: List[str]
    body: str


# SMS Manager (real or mock)
if TWILIO_AVAILABLE:
    sms_manager = get_sms_manager()
else:
    sms_manager = MockSMSManager()


# Broadcast to all connected WebSocket clients
async def broadcast(message: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients."""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            pass  # Connection closed


@app.get("/", response_class=HTMLResponse)
async def portal():
    """Serve the SMS portal dashboard."""
    with open("sms_portal/index.html", "r") as f:
        return f.read()


# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="sms_portal"), name="static")


@app.get("/api/stats")
async def get_stats():
    """Get SMS statistics."""
    stats = sms_manager.get_stats()
    return stats


@app.get("/api/messages")
async def get_messages(limit: int = 50, phone: Optional[str] = None):
    """Get recent SMS messages."""
    if hasattr(sms_manager, 'get_messages'):
        messages = sms_manager.get_messages(limit)
    else:
        # Fallback for mock
        messages = list(sms_manager.messages)[-limit:] if hasattr(sms_manager, 'messages') else []
    
    # Filter by phone if provided
    if phone:
        messages = [m for m in messages if m.get('to') == phone]
    
    return {"messages": messages, "count": len(messages)}


@app.post("/api/send")
async def send_test_sms(request: SendSMSRequest):
    """Send a test SMS message."""
    try:
        # Send SMS
        result = sms_manager.send_sms(request.to, request.body)
        
        # Broadcast to WebSocket clients
        await broadcast({
            "type": "new_message",
            "data": {
                "sid": result.sid if hasattr(result, 'sid') else "unknown",
                "to": request.to,
                "body": request.body,
                "status": getattr(result, 'status', 'sent'),
                "timestamp": datetime.now().isoformat()
            }
        })
        
        return {
            "success": True,
            "sid": getattr(result, 'sid', 'unknown'),
            "status": getattr(result, 'status', 'sent'),
            "message": "SMS sent successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/send/confirmation")
async def send_confirmation_sms(to: str, order_id: str, game: str, date: str):
    """Send a test ticket confirmation SMS."""
    try:
        result = sms_manager.send_ticket_confirmation(
            to=to,
            order_id=order_id,
            game=game,
            date=date,
            seats="Section 101, Row 5",
            total=150.00,
            confirmation_code="TEST123"
        )
        
        return {
            "success": True,
            "sid": getattr(result, 'sid', 'unknown'),
            "message": "Confirmation SMS sent"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/send/reminder")
async def send_reminder_sms(to: str, game: str, date: str, time: str):
    """Send a test game reminder SMS."""
    try:
        result = sms_manager.send_game_reminder(
            to=to,
            game=game,
            date=date,
            time=time,
            venue="Crypto.com Arena",
            seats="Section 101, Row 5"
        )
        
        return {
            "success": True,
            "sid": getattr(result, 'sid', 'unknown'),
            "message": "Reminder SMS sent"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/customers")
async def get_customers():
    """Get list of customers (from SMS history)."""
    messages = sms_manager.get_messages(100) if hasattr(sms_manager, 'get_messages') else []
    
    # Extract unique phone numbers
    customers = set()
    for msg in messages:
        to = msg.get('to', '') or msg.get('To', '')
        if to:
            customers.add(to)
    
    return {
        "customers": list(customers),
        "count": len(customers)
    }


@app.get("/api/customer/{phone}/history")
async def get_customer_history(phone: str, limit: int = 20):
    """Get SMS history for a specific customer."""
    messages = sms_manager.get_messages(100) if hasattr(sms_manager, 'get_messages') else []
    
    # Filter by phone number
    customer_messages = [
        msg for msg in messages
        if msg.get('to') == phone or msg.get('To') == phone
    ][:limit]
    
    return {
        "phone": phone,
        "messages": customer_messages,
        "count": len(customer_messages)
    }


@app.get("/api/customer/{phone}/stats")
async def get_customer_stats(phone: str):
    """Get statistics for a specific customer."""
    messages = sms_manager.get_messages(100) if hasattr(sms_manager, 'get_messages') else []
    
    # Filter by phone number
    customer_messages = [
        msg for msg in messages
        if msg.get('to') == phone or msg.get('To') == phone
    ]
    
    return {
        "phone": phone,
        "total_messages": len(customer_messages),
        "last_message": customer_messages[-1] if customer_messages else None,
        "messages_today": len([
            msg for msg in customer_messages
            if datetime.fromisoformat(msg.get('sent_at', '')).date() == datetime.now().date()
        ])
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial stats
        await websocket.send_json({
            "type": "stats",
            "data": sms_manager.get_stats()
        })
        
        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(5)  # Update every 5 seconds
            await websocket.send_json({
                "type": "stats",
                "data": sms_manager.get_stats()
            })
    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "twilio_available": TWILIO_AVAILABLE,
        "active_connections": len(active_connections)
    }


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting SMS Portal...")
    print("📱 Access the portal at: http://localhost:8080")
    print("🔗 WebSocket endpoint: ws://localhost:8080/ws")
    print("\nFeatures:")
    print("  ✅ SMS Testing Interface")
    print("  ✅ Customer Usage Observation")
    print("  ✅ Real-time Updates")
    print("  ✅ Message History")
    print("  ✅ Statistics Dashboard")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
