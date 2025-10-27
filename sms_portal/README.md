# 📱 SMS Portal - Testing & Monitoring Dashboard

## Overview

The SMS Portal is a web-based interface for:
- ✅ **Testing SMS functionality** without writing code
- ✅ **Observing customer usage** and SMS patterns
- ✅ **Monitoring SMS statistics** in real-time
- ✅ **Viewing message history** and customer interactions
- ✅ **Sending test messages** with one click

---

## 🚀 Quick Start

### **1. Install Dependencies**

```bash
pip install fastapi uvicorn
```

### **2. Start the Portal**

```bash
# From the project root
cd sms_portal
python server.py
```

Or:

```bash
python -m sms_portal.server
```

### **3. Access the Dashboard**

Open your browser to:

```
http://localhost:8080
```

---

## 📋 Features

### **1. SMS Testing**

Send test SMS messages with a simple interface:
- Enter phone number
- Type message
- Click "Send Test SMS"

**Quick Tests Available:**
- ✅ Ticket Confirmation
- ✅ Game Reminder  
- ✅ Upgrade Notification

### **2. Real-time Statistics**

View live statistics:
- Total SMS sent
- Total failed
- Success rate
- Last 24 hours count

Updates automatically via WebSocket!

### **3. Message History**

View all sent SMS messages:
- Phone number
- Message content
- Status (sent, delivered, failed)
- Timestamp
- Message SID

### **4. Customer Observation**

Monitor customer interactions:
- View all customers
- See message history per customer
- Track communication patterns
- Customer statistics

### **5. Activity Feed**

Real-time activity updates:
- New messages sent
- Status changes
- System events

---

## 🧪 Testing Workflows

### **Test 1: Generic SMS**

1. Go to **Testing** tab
2. Enter phone number: `+15551234567`
3. Enter message: `Test message from portal`
4. Click **Send Test SMS**
5. Check **Messages** tab for confirmation

### **Test 2: Ticket Confirmation**

1. Go to **Testing** tab
2. Click **Ticket Confirmation** button
3. Enter phone number
4. Message sent automatically with:
   - Order ID
   - Game details
   - Seat information
   - Confirmation code

### **Test 3: Game Reminder**

1. Go to **Testing** tab
2. Click **Game Reminder** button
3. Enter phone number
4. Reminder sent with:
   - Game details
   - Date and time
   - Venue information
   - Seat information

---

## 🔍 Customer Observation

### **View All Customers**

1. Go to **Customers** tab
2. See list of all phone numbers
3. Click **View History** for a customer
4. See their complete message history

### **Filter Messages by Phone**

1. Go to **Messages** tab
2. Enter phone number in filter
3. See messages for that customer only

---

## 📊 Statistics Monitoring

### **Overview**

The statistics dashboard shows:
- **Total Sent**: All SMS messages sent
- **Total Failed**: Failed messages
- **Success Rate**: Percentage of successful messages
- **Last 24 Hours**: Recent activity count

### **Real-time Updates**

Stats update automatically via WebSocket:
- Updates every 5 seconds
- No page refresh needed
- Live status indicator

---

## 🔧 Configuration

### **Environment Variables**

The portal uses the same Twilio credentials as the main API:

```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567
```

### **Mock Mode**

If Twilio is not configured, the portal runs in **mock mode**:
- Simulates SMS sending
- Stores messages in memory
- Perfect for testing UI
- No Twilio account needed!

---

## 🌐 API Endpoints

### **Statistics**

```
GET /api/stats
```

Returns:
```json
{
  "total_sent": 100,
  "total_failed": 5,
  "success_rate": 0.95,
  "last_24h": 45
}
```

### **Messages**

```
GET /api/messages?limit=50&phone=+15551234567
```

Returns:
```json
{
  "messages": [...],
  "count": 50
}
```

### **Customers**

```
GET /api/customers
```

Returns:
```json
{
  "customers": ["+15551234567", "+15559876543"],
  "count": 2
}
```

### **Send SMS**

```
POST /api/send
{
  "to": "+15551234567",
  "body": "Test message"
}
```

### **Send Confirmation**

```
POST /api/send/confirmation
{
  "to": "+15551234567",
  "order_id": "ORD-123",
  "game": "Lakers vs Warriors",
  "date": "2024-01-15"
}
```

### **Send Reminder**

```
POST /api/send/reminder
{
  "to": "+15551234567",
  "game": "Lakers vs Warriors",
  "date": "2024-01-15",
  "time": "7:00 PM"
}
```

### **WebSocket**

```
ws://localhost:8080/ws
```

For real-time updates.

---

## 🎨 Customization

### **Themes**

Edit `style.css` to customize:
- Colors
- Fonts
- Layout
- Animations

### **Layout**

Edit `index.html` to add:
- New tabs
- New sections
- Custom panels

---

## 🐛 Troubleshooting

### **Portal Won't Start**

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
pip install fastapi uvicorn
```

### **WebSocket Not Connecting**

**Symptoms**: Status shows "Disconnected"

**Solution**: Check if port 8080 is available
```bash
lsof -i :8080
```

### **Messages Not Loading**

**Error**: Cannot fetch messages

**Solution**: Make sure Twilio is configured or running in mock mode

### **Stats Not Updating**

**Symptoms**: Statistics stuck at zero

**Solution**: Check WebSocket connection indicator

---

## 📚 Additional Resources

- **Main API**: [README.md](../README.md)
- **Twilio Setup**: [TWILIO_SETUP.md](../TWILIO_SETUP.md)
- **Security**: [SECURITY.md](../SECURITY.md)

---

## ✅ Success Checklist

- [ ] Portal starts without errors
- [ ] Dashboard loads at http://localhost:8080
- [ ] WebSocket shows "Connected"
- [ ] Stats display correctly
- [ ] Can send test SMS
- [ ] Messages appear in history
- [ ] Customers list loads
- [ ] Activity feed updates

---

## 🎉 You're Ready!

Your SMS Portal is now ready for testing and monitoring!

**Next Steps**:
1. Send a test SMS
2. Monitor real-time statistics
3. View customer history
4. Track communication patterns

**Happy Testing! 📱✨**
