# 📱 Twilio SMS Integration Setup Guide

## Overview

The Qwen Messaging Agent now includes **Twilio SMS integration** for automated customer communications via text messaging. This enables:

- ✅ **Ticket Purchase Confirmations**: Automated SMS when customers buy tickets
- ✅ **Game Reminders**: SMS reminders before games
- ✅ **Upgrade Notifications**: Notify customers about seat upgrades
- ✅ **Refund Confirmations**: Send refund status updates
- ✅ **Event Alerts**: Real-time event updates
- ✅ **Customer Support**: Two-way SMS conversations
- ✅ **Bulk Messaging**: Send messages to multiple recipients

---

## 🚀 Quick Start

### **1. Get Your Twilio Credentials**

Sign up at [twilio.com](https://www.twilio.com) and get:

- **Account SID**: Found in your Twilio Console
- **Auth Token**: Found in your Twilio Console
- **Phone Number**: Purchased from Twilio (or use trial number)

**Get your credentials:**
1. Go to [console.twilio.com](https://console.twilio.com)
2. Copy your **Account SID**
3. Copy your **Auth Token** (click to reveal)
4. Get a phone number: Console → Phone Numbers → Buy a Number

### **2. Configure Environment Variables**

Add to your `.env` file:

```bash
# Twilio SMS Integration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567
```

### **3. Install Dependencies**

```bash
pip install twilio>=8.10.0
```

Or install all requirements:

```bash
pip install -r api/requirements.txt
```

### **4. Start Your API Server**

```bash
python api/main.py
```

### **5. Test the Integration**

```bash
# Send a test SMS
curl -X POST http://localhost:8000/sms/send \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+15551234567",
    "body": "Hello from Qwen Messaging Agent!"
  }'
```

---

## 📋 Available Endpoints

### **SMS Operations** (Requires Authentication)

#### **1. Send Generic SMS**
```bash
POST /sms/send

# Request
{
  "to": "+15551234567",
  "body": "Your message here"
}

# Response
{
  "message": "SMS sent successfully",
  "sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "status": "queued",
  "to": "+15551234567"
}
```

#### **2. Send Ticket Confirmation**
```bash
POST /sms/confirmation

# Request
{
  "to": "+15551234567",
  "order_id": "ORD-12345",
  "game": "Lakers vs Warriors",
  "date": "2024-01-15",
  "seats": "Section 101, Row 5, Seats 10-12",
  "total": 150.00,
  "confirmation_code": "ABC123"
}

# Response
{
  "message": "Confirmation sent",
  "sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "status": "queued"
}
```

#### **3. Send Game Reminder**
```bash
POST /sms/reminder

# Request
{
  "to": "+15551234567",
  "game": "Lakers vs Warriors",
  "date": "2024-01-15",
  "time": "7:00 PM",
  "venue": "Crypto.com Arena",
  "seats": "Section 101, Row 5, Seats 10-12"
}

# Response
{
  "message": "Reminder sent",
  "sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "status": "queued"
}
```

#### **4. Send Bulk SMS**
```bash
POST /sms/bulk

# Request
{
  "recipients": ["+15551234567", "+15559876543"],
  "body": "Bulk message here",
  "batch_size": 100
}

# Response
{
  "total": 2,
  "sent": 2,
  "failed": 0,
  "results": [...]
}
```

#### **5. Get Message Status**
```bash
GET /sms/status/{message_sid}

# Response
{
  "sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "status": "delivered",
  "to": "+15551234567",
  "sent_at": "2024-01-15T10:00:00Z"
}
```

#### **6. Get Message History**
```bash
GET /sms/history/{phone}?limit=10

# Response
{
  "phone": "+15551234567",
  "messages": [...],
  "count": 10
}
```

#### **7. Get SMS Statistics**
```bash
GET /sms/stats

# Response
{
  "total_sent": 1000,
  "total_failed": 5,
  "success_rate": 0.995,
  "last_24h": 150
}
```

---

## 🔗 Webhook Endpoints (No Auth Required)

Twilio sends webhook requests to these endpoints automatically.

### **Incoming SMS Webhook**

**Endpoint**: `POST /sms/webhook/incoming`

**Purpose**: Handle incoming SMS messages from customers

**Configure in Twilio Console**:
1. Go to Phone Numbers → Manage → Active Numbers
2. Click your number
3. Set **Messaging** → **A MESSAGE COMES IN** to:
   ```
   https://your-api.com/sms/webhook/incoming
   ```

**Handler**: Automatically replies to customer messages

### **Status Callback Webhook**

**Endpoint**: `POST /sms/webhook/status`

**Purpose**: Receive message delivery status updates

**Configure in Twilio Console**:
1. Go to Phone Numbers → Manage → Active Numbers
2. Click your number
3. Set **Messaging** → **STATUS CALLBACK URL** to:
   ```
   https://your-api.com/sms/webhook/status
   ```

---

## 🧪 Testing

### **1. Test Message Sending**

```python
from integrations.twilio_integration import get_sms_manager

# Send a test message
sms_manager = get_sms_manager()
message = sms_manager.send_sms(
    to="+15551234567",
    body="Test message from Qwen Agent"
)

print(f"Message SID: {message.sid}")
print(f"Status: {message.status}")
```

### **2. Test Ticket Confirmation**

```python
message = sms_manager.send_ticket_confirmation(
    to="+15551234567",
    order_id="ORD-12345",
    game="Lakers vs Warriors",
    date="2024-01-15",
    seats="Section 101, Row 5",
    total=150.00,
    confirmation_code="ABC123"
)
```

### **3. Test Game Reminder**

```python
message = sms_manager.send_game_reminder(
    to="+15551234567",
    game="Lakers vs Warriors",
    date="2024-01-15",
    time="7:00 PM",
    venue="Crypto.com Arena",
    seats="Section 101, Row 5"
)
```

### **4. Test Bulk Messaging**

```python
results = sms_manager.send_bulk_sms(
    recipients=["+15551234567", "+15559876543"],
    body="Season ticket special event!",
    batch_size=100
)

print(f"Sent: {results['sent']}")
print(f"Failed: {results['failed']}")
```

---

## 🔐 Authentication & Permissions

### **Required Scopes**

- **`send_sms`**: Send individual SMS messages
- **`admin`**: Full access including bulk messaging
- **`view_sms_history`**: View message history
- **`view_dashboard`**: View SMS statistics

### **Getting Authentication Token**

```bash
# Register a user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "SecurePassword123!"
  }'

# Login to get token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=SecurePassword123!"

# Use token in requests
curl -X POST http://localhost:8000/sms/send \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to": "+15551234567", "body": "Hello"}'
```

---

## 💰 Pricing & Costs

### **Twilio SMS Pricing**

- **US SMS**: $0.0075 per message (send and receive)
- **International SMS**: Varies by country
- **Trial Account**: $15.50 credit (1,000+ messages)

### **Cost Optimization Tips**

1. **Batch Messages**: Use `send_bulk_sms()` for multiple recipients
2. **Schedule Messages**: Use `SMSScheduler` for timed messages
3. **Template Messages**: Reuse message templates to save costs
4. **Monitor Usage**: Track statistics with `/sms/stats`

---

## 🛡️ Security Best Practices

### **1. Protect Your Credentials**

- ✅ Never commit `.env` file to version control
- ✅ Use environment variables for all Twilio credentials
- ✅ Rotate Auth Token regularly (every 90 days)
- ✅ Use different credentials for dev/staging/production

### **2. Secure Webhooks**

Twilio webhooks are **automatically secured** - no authentication needed. Twilio verifies webhook authenticity using:

- Request signature validation
- HTTPS enforcement
- Caller ID verification

### **3. Rate Limiting**

SMS endpoints respect your API rate limits:
- Default: 60 requests/minute
- Configure via `RATE_LIMIT_PER_MINUTE` environment variable

---

## 📊 Monitoring & Logging

### **View SMS Logs**

All SMS operations are logged to:
- **Console**: Structured logs with `structlog`
- **BigQuery**: Conversation analytics (if configured)
- **Redis**: Message tracking and history

### **Monitor Statistics**

```bash
# Get SMS stats
curl -X GET http://localhost:8000/sms/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **Track Message Status**

```bash
# Check message delivery
curl -X GET http://localhost:8000/sms/status/SMxxxx \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔧 Troubleshooting

### **Error: "Twilio credentials not configured"**

**Solution**: Check your environment variables:
```bash
# Verify credentials are set
echo $TWILIO_ACCOUNT_SID
echo $TWILIO_AUTH_TOKEN
echo $TWILIO_PHONE_NUMBER

# Add to .env file
vim .env
```

### **Error: "Failed to send SMS"**

**Common Causes**:
1. **Invalid phone number**: Must be E.164 format (`+15551234567`)
2. **Insufficient Twilio balance**: Add funds to your Twilio account
3. **Incorrect phone number**: Verify the recipient number

**Solution**:
```bash
# Format phone numbers correctly
# Bad: 5551234567
# Good: +1555124567
```

### **Error: "Message not delivered"**

**Check Status**:
```bash
# Get message status
curl -X GET http://localhost:8000/sms/status/SMxxxx \
  -H "Authorization: Bearer YOUR_TOKEN"

# Common statuses:
# - "queued": Sending
# - "sent": Delivered to carrier
# - "delivered": Customer received
# - "failed": Delivery failed
# - "undelivered": Could not deliver
```

---

## 📚 Additional Resources

- **Twilio Documentation**: [twilio.com/docs](https://www.twilio.com/docs)
- **Twilio Console**: [console.twilio.com](https://console.twilio.com)
- **SMS Best Practices**: [twilio.com/docs/sms/tutorials](https://www.twilio.com/docs/sms/tutorials)
- **Twilio Support**: [support.twilio.com](https://support.twilio.com)

---

## ✅ Success Checklist

- [ ] Twilio account created
- [ ] Credentials added to `.env` file
- [ ] Phone number purchased
- [ ] Dependencies installed (`pip install twilio`)
- [ ] API server started (`python api/main.py`)
- [ ] Test SMS sent successfully
- [ ] Webhooks configured in Twilio Console
- [ ] Incoming messages working
- [ ] Status callbacks working

---

## 🎉 You're Ready!

Your Twilio SMS integration is now configured and ready to use. Start sending automated SMS messages to your customers!

**Next Steps**:
1. Test sending a confirmation SMS
2. Set up webhook URLs in Twilio Console
3. Start automating your customer communications
4. Monitor usage and costs in the Twilio Console

**Need Help?**
- Check the [README.md](README.md) for API documentation
- Review [SECURITY.md](SECURITY.md) for security best practices
- Contact Twilio support for SMS-specific issues

---

**Happy Messaging! 📱✨**
