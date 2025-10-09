"""
Twilio API Routes
FastAPI endpoints for SMS operations and webhooks
"""

from fastapi import APIRouter, HTTPException, Request, Form, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .twilio_integration import get_sms_manager, TwilioWebhookHandler, SMSScheduler
from auth.jwt_auth import get_current_active_user, User, check_scopes
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/sms", tags=["sms"])


# Request models
class SendSMSRequest(BaseModel):
    to: str
    body: str


class TicketConfirmationRequest(BaseModel):
    to: str
    order_id: str
    game: str
    date: str
    seats: str
    total: float
    confirmation_code: str


class GameReminderRequest(BaseModel):
    to: str
    game: str
    date: str
    time: str
    venue: str
    seats: str


class BulkSMSRequest(BaseModel):
    recipients: List[str]
    body: str
    batch_size: int = 100


# Routes

@router.post("/send")
async def send_sms(
    request: SendSMSRequest,
    current_user: User = Depends(check_scopes(["admin", "send_sms"]))
):
    """Send SMS message (admin only)."""
    sms_manager = get_sms_manager()
    
    message = sms_manager.send_sms(request.to, request.body)
    
    if message.status == "failed":
        raise HTTPException(status_code=500, detail=message.error)
    
    return {
        "message": "SMS sent successfully",
        "sid": message.sid,
        "status": message.status,
        "to": message.to
    }


@router.post("/confirmation")
async def send_ticket_confirmation(
    request: TicketConfirmationRequest,
    current_user: User = Depends(check_scopes(["send_sms"]))
):
    """Send ticket purchase confirmation SMS."""
    sms_manager = get_sms_manager()
    
    message = sms_manager.send_ticket_confirmation(
        to=request.to,
        order_id=request.order_id,
        game=request.game,
        date=request.date,
        seats=request.seats,
        total=request.total,
        confirmation_code=request.confirmation_code
    )
    
    if message.status == "failed":
        raise HTTPException(status_code=500, detail=message.error)
    
    logger.info("Ticket confirmation sent",
               order_id=request.order_id,
               to=request.to,
               by_user=current_user.username)
    
    return {
        "message": "Confirmation sent",
        "sid": message.sid,
        "status": message.status
    }


@router.post("/reminder")
async def send_game_reminder(
    request: GameReminderRequest,
    current_user: User = Depends(check_scopes(["send_sms"]))
):
    """Send game reminder SMS."""
    sms_manager = get_sms_manager()
    
    message = sms_manager.send_game_reminder(
        to=request.to,
        game=request.game,
        date=request.date,
        time=request.time,
        venue=request.venue,
        seats=request.seats
    )
    
    if message.status == "failed":
        raise HTTPException(status_code=500, detail=message.error)
    
    return {
        "message": "Reminder sent",
        "sid": message.sid,
        "status": message.status
    }


@router.post("/bulk")
async def send_bulk_sms(
    request: BulkSMSRequest,
    current_user: User = Depends(check_scopes(["admin"]))
):
    """Send bulk SMS messages (admin only)."""
    sms_manager = get_sms_manager()
    
    results = sms_manager.send_bulk_sms(
        recipients=request.recipients,
        body=request.body,
        batch_size=request.batch_size
    )
    
    logger.info("Bulk SMS sent",
               total=results["total"],
               sent=results["sent"],
               by_user=current_user.username)
    
    return results


@router.get("/status/{message_sid}")
async def get_message_status(
    message_sid: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get status of a sent SMS message."""
    sms_manager = get_sms_manager()
    
    status = sms_manager.get_message_status(message_sid)
    
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    
    return status


@router.get("/history/{phone}")
async def get_message_history(
    phone: str,
    limit: int = 10,
    current_user: User = Depends(check_scopes(["admin", "view_sms_history"]))
):
    """Get SMS history for a phone number."""
    sms_manager = get_sms_manager()
    
    messages = sms_manager.get_user_messages(phone, limit)
    
    return {
        "phone": phone,
        "messages": messages,
        "count": len(messages)
    }


@router.get("/stats")
async def get_sms_stats(
    current_user: User = Depends(check_scopes(["admin", "view_dashboard"]))
):
    """Get SMS statistics."""
    sms_manager = get_sms_manager()
    
    stats = sms_manager.get_stats()
    
    return stats


# Webhook endpoints (no auth required - Twilio validates)

@router.post("/webhook/incoming")
async def twilio_incoming_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...)
):
    """
    Handle incoming SMS from Twilio.
    Twilio sends POST requests when customers reply to SMS.
    """
    sms_manager = get_sms_manager()
    webhook_handler = TwilioWebhookHandler(sms_manager)
    
    # Handle incoming message
    reply = webhook_handler.handle_incoming_sms(From, Body)
    
    # Return TwiML response
    if reply:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply}</Message>
</Response>"""
    else:
        return """<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>"""


@router.post("/webhook/status")
async def twilio_status_webhook(
    MessageSid: str = Form(...),
    MessageStatus: str = Form(...),
    ErrorCode: Optional[str] = Form(None)
):
    """
    Handle message status callbacks from Twilio.
    Twilio sends POST requests when message status changes.
    """
    sms_manager = get_sms_manager()
    webhook_handler = TwilioWebhookHandler(sms_manager)
    
    # Handle status update
    webhook_handler.handle_status_callback(
        message_sid=MessageSid,
        status=MessageStatus,
        error_code=ErrorCode
    )
    
    return {"status": "received"}
