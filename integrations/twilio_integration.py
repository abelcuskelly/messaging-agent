"""
Twilio SMS Integration
Automated SMS messaging for ticket confirmations, reminders, and alerts
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import structlog
from dataclasses import dataclass
import redis
import json

logger = structlog.get_logger()


@dataclass
class SMSMessage:
    """SMS message data."""
    to: str
    body: str
    from_: str
    sid: Optional[str] = None
    status: Optional[str] = None
    sent_at: Optional[str] = None
    error: Optional[str] = None


class TwilioSMSManager:
    """
    Manages SMS messaging via Twilio.
    Handles ticket confirmations, reminders, and customer notifications.
    """
    
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
        redis_client: Optional[redis.Redis] = None
    ):
        """
        Initialize Twilio SMS manager.
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: Twilio phone number
            redis_client: Redis client for tracking sent messages
        """
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.getenv("TWILIO_PHONE_NUMBER")
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError("Twilio credentials not configured")
        
        # Initialize Twilio client
        self.client = Client(self.account_sid, self.auth_token)
        
        # Redis for tracking
        self.redis_client = redis_client or redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
        
        # Statistics
        self.total_sent = 0
        self.total_failed = 0
        
        logger.info("Twilio SMS manager initialized",
                   from_number=self.from_number)
    
    def send_sms(
        self,
        to: str,
        body: str,
        track: bool = True
    ) -> SMSMessage:
        """
        Send SMS message.
        
        Args:
            to: Recipient phone number (E.164 format: +1234567890)
            body: Message body (max 1600 characters)
            track: Whether to track message in Redis
            
        Returns:
            SMSMessage with status
        """
        try:
            # Validate phone number format
            if not to.startswith('+'):
                to = f"+1{to}"  # Assume US if no country code
            
            # Send message
            message = self.client.messages.create(
                body=body,
                from_=self.from_number,
                to=to
            )
            
            self.total_sent += 1
            
            sms_message = SMSMessage(
                to=to,
                body=body,
                from_=self.from_number,
                sid=message.sid,
                status=message.status,
                sent_at=datetime.utcnow().isoformat()
            )
            
            # Track in Redis
            if track:
                self._track_message(sms_message)
            
            logger.info("SMS sent successfully",
                       to=to,
                       sid=message.sid,
                       status=message.status)
            
            return sms_message
            
        except TwilioRestException as e:
            self.total_failed += 1
            
            logger.error("SMS send failed",
                        to=to,
                        error=str(e))
            
            return SMSMessage(
                to=to,
                body=body,
                from_=self.from_number,
                status="failed",
                error=str(e)
            )
    
    def send_ticket_confirmation(
        self,
        to: str,
        order_id: str,
        game: str,
        date: str,
        seats: str,
        total: float,
        confirmation_code: str
    ) -> SMSMessage:
        """Send ticket purchase confirmation SMS."""
        body = f"""🎫 Ticket Confirmation

Order: {order_id}
Game: {game}
Date: {date}
Seats: {seats}
Total: ${total:.2f}

Confirmation: {confirmation_code}

Show this code at the gate or use mobile tickets.

Questions? Reply HELP"""
        
        return self.send_sms(to, body)
    
    def send_game_reminder(
        self,
        to: str,
        game: str,
        date: str,
        time: str,
        venue: str,
        seats: str,
        gate_info: str = "Gates open 1 hour before game"
    ) -> SMSMessage:
        """Send game day reminder SMS."""
        body = f"""🏀 Game Day Reminder

{game}
{date} at {time}
{venue}

Your Seats: {seats}
{gate_info}

Have your tickets ready!

Reply PARKING for parking info."""
        
        return self.send_sms(to, body)
    
    def send_upgrade_notification(
        self,
        to: str,
        game: str,
        old_seats: str,
        new_seats: str,
        price_difference: float
    ) -> SMSMessage:
        """Send seat upgrade confirmation SMS."""
        body = f"""✨ Seat Upgrade Confirmed

Game: {game}
Old Seats: {old_seats}
New Seats: {new_seats}
Additional Cost: ${price_difference:.2f}

Your tickets have been updated!

Reply DETAILS for more info."""
        
        return self.send_sms(to, body)
    
    def send_refund_confirmation(
        self,
        to: str,
        order_id: str,
        game: str,
        refund_amount: float,
        processing_days: int = 5
    ) -> SMSMessage:
        """Send refund confirmation SMS."""
        body = f"""💰 Refund Processed

Order: {order_id}
Game: {game}
Refund Amount: ${refund_amount:.2f}

Your refund will be processed within {processing_days} business days.

Questions? Reply HELP"""
        
        return self.send_sms(to, body)
    
    def send_event_alert(
        self,
        to: str,
        alert_type: str,
        game: str,
        message: str
    ) -> SMSMessage:
        """Send event alert (cancellation, time change, etc.)."""
        body = f"""⚠️ Event Alert

{alert_type.upper()}
Game: {game}

{message}

For assistance, call 1-800-TICKETS"""
        
        return self.send_sms(to, body)
    
    def send_promotional(
        self,
        to: str,
        offer: str,
        expiry: str,
        promo_code: str
    ) -> SMSMessage:
        """Send promotional offer SMS."""
        body = f"""🎉 Special Offer!

{offer}

Use code: {promo_code}
Expires: {expiry}

Visit our website to redeem.

Reply STOP to unsubscribe."""
        
        return self.send_sms(to, body)
    
    def send_bulk_sms(
        self,
        recipients: List[str],
        body: str,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Send SMS to multiple recipients in batches.
        
        Args:
            recipients: List of phone numbers
            body: Message body
            batch_size: Number of messages per batch
            
        Returns:
            Summary of sent messages
        """
        results = {
            "total": len(recipients),
            "sent": 0,
            "failed": 0,
            "messages": []
        }
        
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            
            for phone in batch:
                message = self.send_sms(phone, body, track=True)
                
                if message.status != "failed":
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                
                results["messages"].append({
                    "to": phone,
                    "status": message.status,
                    "sid": message.sid
                })
        
        logger.info("Bulk SMS completed",
                   total=results["total"],
                   sent=results["sent"],
                   failed=results["failed"])
        
        return results
    
    def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """Get status of a sent message."""
        try:
            message = self.client.messages(message_sid).fetch()
            
            return {
                "sid": message.sid,
                "status": message.status,
                "to": message.to,
                "from": message.from_,
                "body": message.body,
                "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                "price": message.price,
                "error_code": message.error_code,
                "error_message": message.error_message
            }
            
        except TwilioRestException as e:
            logger.error("Failed to get message status",
                        sid=message_sid,
                        error=str(e))
            return {"error": str(e)}
    
    def _track_message(self, message: SMSMessage):
        """Track sent message in Redis."""
        if not self.redis_client:
            return
        
        try:
            # Store message details
            key = f"sms:{message.sid}"
            self.redis_client.set(
                key,
                json.dumps({
                    "to": message.to,
                    "body": message.body,
                    "status": message.status,
                    "sent_at": message.sent_at
                }),
                ex=86400 * 30  # 30 days
            )
            
            # Track by phone number
            phone_key = f"sms:phone:{message.to}"
            self.redis_client.lpush(phone_key, message.sid)
            self.redis_client.ltrim(phone_key, 0, 99)  # Keep last 100
            
        except Exception as e:
            logger.error("Failed to track message", error=str(e))
    
    def get_user_messages(self, phone: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get message history for a phone number."""
        if not self.redis_client:
            return []
        
        try:
            phone_key = f"sms:phone:{phone}"
            message_sids = self.redis_client.lrange(phone_key, 0, limit - 1)
            
            messages = []
            for sid in message_sids:
                message_data = self.redis_client.get(f"sms:{sid}")
                if message_data:
                    messages.append(json.loads(message_data))
            
            return messages
            
        except Exception as e:
            logger.error("Failed to get user messages", error=str(e))
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get SMS statistics."""
        return {
            "total_sent": self.total_sent,
            "total_failed": self.total_failed,
            "success_rate": (
                self.total_sent / (self.total_sent + self.total_failed)
                if (self.total_sent + self.total_failed) > 0 else 0
            ),
            "from_number": self.from_number
        }


class TwilioWebhookHandler:
    """Handle incoming Twilio webhooks for SMS replies and status updates."""
    
    def __init__(self, sms_manager: TwilioSMSManager):
        self.sms_manager = sms_manager
        
        # Auto-reply keywords
        self.auto_replies = {
            "HELP": "For assistance, call 1-800-TICKETS or visit our website. Reply STOP to unsubscribe.",
            "STOP": "You've been unsubscribed from SMS notifications. Text START to re-subscribe.",
            "START": "Welcome back! You'll now receive ticket confirmations and reminders.",
            "PARKING": "Parking info: General $25-40, Premium $50-75, Valet $60-80. Parking opens 2 hours before game.",
            "DETAILS": "For detailed ticket information, check your email confirmation or visit your account on our website."
        }
    
    def handle_incoming_sms(self, from_number: str, body: str) -> Optional[str]:
        """
        Handle incoming SMS from customer.
        
        Args:
            from_number: Sender's phone number
            body: Message body
            
        Returns:
            Auto-reply message if applicable
        """
        body_upper = body.strip().upper()
        
        logger.info("Incoming SMS received",
                   from_number=from_number,
                   body=body[:50])
        
        # Check for auto-reply keywords
        for keyword, reply in self.auto_replies.items():
            if keyword in body_upper:
                # Send auto-reply
                self.sms_manager.send_sms(from_number, reply)
                
                logger.info("Auto-reply sent",
                           keyword=keyword,
                           to=from_number)
                
                return reply
        
        # Forward to support team for manual handling
        logger.info("SMS forwarded to support",
                   from_number=from_number,
                   body=body)
        
        return None
    
    def handle_status_callback(
        self,
        message_sid: str,
        status: str,
        error_code: Optional[str] = None
    ):
        """
        Handle message status callback from Twilio.
        
        Args:
            message_sid: Twilio message SID
            status: Message status (queued, sent, delivered, failed, etc.)
            error_code: Error code if failed
        """
        logger.info("SMS status update",
                   sid=message_sid,
                   status=status,
                   error_code=error_code)
        
        # Update status in Redis
        try:
            key = f"sms:{message_sid}"
            message_data = self.sms_manager.redis_client.get(key)
            
            if message_data:
                data = json.loads(message_data)
                data["status"] = status
                data["updated_at"] = datetime.utcnow().isoformat()
                
                if error_code:
                    data["error_code"] = error_code
                
                self.sms_manager.redis_client.set(key, json.dumps(data), ex=86400 * 30)
                
        except Exception as e:
            logger.error("Failed to update message status", error=str(e))


class SMSTemplates:
    """Pre-defined SMS templates for common scenarios."""
    
    @staticmethod
    def ticket_confirmation(
        order_id: str,
        game: str,
        date: str,
        seats: str,
        total: float,
        confirmation_code: str
    ) -> str:
        """Ticket purchase confirmation template."""
        return f"""🎫 Ticket Confirmed!

Order #{order_id}
{game}
{date}
Seats: {seats}
Total: ${total:.2f}

Code: {confirmation_code}

View tickets: tickets.example.com/{order_id}"""
    
    @staticmethod
    def game_reminder_24h(
        game: str,
        date: str,
        time: str,
        venue: str,
        seats: str
    ) -> str:
        """24-hour game reminder template."""
        return f"""🏀 Game Tomorrow!

{game}
{date} at {time}
{venue}

Your Seats: {seats}

Gates open 1 hour early. Arrive early for best experience!"""
    
    @staticmethod
    def game_reminder_2h(
        game: str,
        time: str,
        seats: str,
        parking_tip: str = "Parking fills up fast!"
    ) -> str:
        """2-hour game reminder template."""
        return f"""⏰ Game Starts Soon!

Game time: {time}
Your Seats: {seats}

{parking_tip}

Have your tickets ready!"""
    
    @staticmethod
    def upgrade_available(
        game: str,
        current_seats: str,
        upgrade_seats: str,
        price: float
    ) -> str:
        """Seat upgrade offer template."""
        return f"""✨ Upgrade Available!

{game}

Current: {current_seats}
Upgrade to: {upgrade_seats}
Price: ${price:.2f}

Reply YES to upgrade or visit our app."""
    
    @staticmethod
    def refund_processed(
        order_id: str,
        amount: float,
        processing_days: int = 5
    ) -> str:
        """Refund confirmation template."""
        return f"""💰 Refund Confirmed

Order #{order_id}
Amount: ${amount:.2f}

Refund will appear in {processing_days} business days.

Thank you for your patience."""
    
    @staticmethod
    def event_cancelled(
        game: str,
        date: str,
        refund_info: str = "Full refund will be processed automatically"
    ) -> str:
        """Event cancellation notification template."""
        return f"""⚠️ Event Cancelled

{game}
{date}

{refund_info}

We apologize for the inconvenience. Check email for details."""
    
    @staticmethod
    def event_rescheduled(
        game: str,
        old_date: str,
        new_date: str,
        new_time: str
    ) -> str:
        """Event rescheduled notification template."""
        return f"""📅 Event Rescheduled

{game}

Original: {old_date}
New Date: {new_date} at {new_time}

Your tickets are still valid. No action needed."""


class SMSScheduler:
    """Schedule SMS messages for future delivery."""
    
    def __init__(self, sms_manager: TwilioSMSManager):
        self.sms_manager = sms_manager
    
    def schedule_game_reminders(
        self,
        phone: str,
        game: str,
        game_datetime: datetime,
        venue: str,
        seats: str
    ):
        """
        Schedule automated reminders for a game.
        
        Sends:
        - 24 hours before game
        - 2 hours before game
        """
        # 24-hour reminder
        reminder_24h = game_datetime - timedelta(hours=24)
        body_24h = SMSTemplates.game_reminder_24h(
            game=game,
            date=game_datetime.strftime("%A, %B %d"),
            time=game_datetime.strftime("%I:%M %p"),
            venue=venue,
            seats=seats
        )
        
        # 2-hour reminder
        reminder_2h = game_datetime - timedelta(hours=2)
        body_2h = SMSTemplates.game_reminder_2h(
            game=game,
            time=game_datetime.strftime("%I:%M %p"),
            seats=seats
        )
        
        # In production, use a task queue (Celery, Cloud Tasks, etc.)
        logger.info("Game reminders scheduled",
                   phone=phone,
                   game=game,
                   reminder_24h=reminder_24h.isoformat(),
                   reminder_2h=reminder_2h.isoformat())
        
        return {
            "scheduled": True,
            "reminders": [
                {"time": reminder_24h.isoformat(), "type": "24h"},
                {"time": reminder_2h.isoformat(), "type": "2h"}
            ]
        }


# Global SMS manager instance
_sms_manager: Optional[TwilioSMSManager] = None


def get_sms_manager() -> TwilioSMSManager:
    """Get or create global SMS manager."""
    global _sms_manager
    
    if _sms_manager is None:
        _sms_manager = TwilioSMSManager()
        logger.info("SMS manager instance created")
    
    return _sms_manager


if __name__ == "__main__":
    print("📱 Twilio SMS Integration Test")
    print("\nMake sure you have set environment variables:")
    print("  TWILIO_ACCOUNT_SID")
    print("  TWILIO_AUTH_TOKEN")
    print("  TWILIO_PHONE_NUMBER")
    print("\nPress Enter to run test...")
    input()
    
    try:
        # Initialize
        sms_manager = get_sms_manager()
        
        # Test phone number (replace with your number)
        test_phone = os.getenv("TEST_PHONE_NUMBER", "+1234567890")
        
        print(f"\n📤 Sending test SMS to {test_phone}...")
        
        # Send test confirmation
        message = sms_manager.send_ticket_confirmation(
            to=test_phone,
            order_id="TEST123",
            game="Lakers vs Warriors",
            date="March 15, 2024 at 7:30 PM",
            seats="Section 101, Row A, Seats 1-2",
            total=450.00,
            confirmation_code="CONF-ABC123"
        )
        
        if message.status != "failed":
            print(f"✅ SMS sent successfully!")
            print(f"   SID: {message.sid}")
            print(f"   Status: {message.status}")
        else:
            print(f"❌ SMS failed: {message.error}")
        
        # Get stats
        stats = sms_manager.get_stats()
        print(f"\n📊 SMS Statistics:")
        print(f"   Total Sent: {stats['total_sent']}")
        print(f"   Total Failed: {stats['total_failed']}")
        print(f"   Success Rate: {stats['success_rate']:.1%}")
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease set the required environment variables:")
        print("  export TWILIO_ACCOUNT_SID=your_account_sid")
        print("  export TWILIO_AUTH_TOKEN=your_auth_token")
        print("  export TWILIO_PHONE_NUMBER=+1234567890")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
