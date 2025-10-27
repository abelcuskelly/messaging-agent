# 💳 Stripe Payment Integration

## Overview

Process payments directly through your messaging agent using Stripe. Customers can purchase tickets, upgrades, and services seamlessly within chat conversations.

---

## 🚀 Quick Start

### **1. Configure Stripe Credentials**

Add to your `.env` file:

```bash
# Stripe Keys
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

### **2. Get Your Stripe Keys**

1. Go to [dashboard.stripe.com](https://dashboard.stripe.com)
2. Navigate to Developers → API Keys
3. Copy **Secret key** (starts with `sk_`)
4. Copy **Publishable key** (starts with `pk_`)

### **3. Set Up Webhooks**

1. Go to Developers → Webhooks
2. Click **Add endpoint**
3. Set URL: `https://your-api.com/payments/webhook`
4. Select events to listen for:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `checkout.session.completed`
5. Copy the **Signing secret**

### **4. Test the Integration**

```python
from integrations.payments.stripe_client import StripePaymentManager

# Initialize manager
payment_manager = StripePaymentManager()

# Create a payment intent
intent = payment_manager.create_payment_intent(
    amount=100.00,
    currency='usd',
    description='Lakers tickets'
)

print(f"Payment Intent: {intent.id}")
print(f"Status: {intent.status}")
```

---

## 💰 Payment Methods

### **1. Payment Intent (Direct Payment)**

**Use when**: You want to handle the payment directly in your app.

```python
# Create payment intent
intent = payment_manager.create_payment_intent(
    amount=150.00,
    currency='usd',
    description='Premium seat upgrade',
    metadata={'order_id': 'ORD123'}
)

# Client uses: stripe.confirmCardPayment(client_secret)
```

**API Call:**
```bash
POST /payments/intent/create
{
  "amount": 150.00,
  "currency": "usd",
  "description": "Premium seat upgrade",
  "metadata": {
    "order_id": "ORD123",
    "ticket_type": "premium"
  }
}
```

### **2. Checkout Session (Hosted Payment)**

**Use when**: You want Stripe to handle the entire payment page.

```python
# Create checkout session
session = payment_manager.create_checkout_session(
    items=[
        PaymentItem(
            name='Lakers vs Warriors',
            description='Section 101, Row 5',
            amount=200.00,
            quantity=2
        )
    ],
    success_url='https://yoursite.com/success',
    cancel_url='https://yoursite.com/cancel',
    customer_email='customer@example.com'
)

# Redirect customer to session.url
```

**API Call:**
```bash
POST /payments/checkout/create
{
  "items": [
    {
      "name": "Lakers vs Warriors",
      "description": "Section 101, Row 5",
      "amount": 200.00,
      "quantity": 2
    }
  ],
  "success_url": "https://yoursite.com/success",
  "cancel_url": "https://yoursite.com/cancel",
  "customer_email": "customer@example.com"
}
```

---

## 📋 API Endpoints

### **Create Payment Intent**

```bash
POST /payments/intent/create
{
  "amount": 100.00,
  "currency": "usd",
  "description": "Ticket purchase",
  "metadata": {"order_id": "123"}
}
```

**Response:**
```json
{
  "success": true,
  "payment_intent": {
    "id": "pi_xxx",
    "amount": 100.00,
    "currency": "usd",
    "status": "requires_payment_method",
    "client_secret": "pi_xxx_secret_xxx"
  }
}
```

### **Create Checkout Session**

```bash
POST /payments/checkout/create
{
  "items": [
    {"name": "Ticket", "amount": 50.00, "quantity": 1}
  ],
  "success_url": "https://yoursite.com/success",
  "cancel_url": "https://yoursite.com/cancel"
}
```

**Response:**
```json
{
  "success": true,
  "checkout_session": {
    "id": "cs_xxx",
    "url": "https://checkout.stripe.com/xxx",
    "status": "open"
  }
}
```

### **Get Payment Status**

```bash
GET /payments/intent/{payment_intent_id}/status
```

**Response:**
```json
{
  "payment_intent": {
    "id": "pi_xxx",
    "amount": 100.00,
    "status": "succeeded",
    "customer_id": "cus_xxx",
    "metadata": {"order_id": "123"}
  }
}
```

### **Cancel Payment**

```bash
POST /payments/intent/{payment_intent_id}/cancel
```

### **Refund Payment**

```bash
POST /payments/refund
{
  "payment_intent_id": "pi_xxx",
  "amount": 100.00  // Optional: partial refund
}
```

### **Create Customer**

```bash
POST /payments/customer/create?email=customer@example.com&name=John Doe
```

### **Get Customer**

```bash
GET /payments/customer/{customer_id}
```

### **Webhook Handler**

```bash
POST /payments/webhook
# Stripe sends events to this endpoint
```

---

## 🤖 Integration with Messaging Agent

### **Initiate Payment in Chat**

```python
from integrations.payments.stripe_client import StripePaymentManager

# Customer asks to purchase tickets
chat_message = "I'd like to buy 2 tickets for the Lakers game"

# Create checkout session
payment_manager = StripePaymentManager()
session = payment_manager.create_checkout_session(
    items=[
        PaymentItem(
            name='Lakers vs Warriors',
            description='Section 101, Seats 5-6',
            amount=200.00,
            quantity=2
        )
    ],
    success_url='https://yoursite.com/success',
    cancel_url='https://yoursite.com/cancel'
)

# Send checkout link to customer
agent_response = f"Great! Here's your secure checkout link: {session.url}"
```

### **Handle Payment Webhooks**

```python
# Webhook automatically triggered by Stripe
# Handle in your webhook endpoint:
if event['type'] == 'checkout.session.completed':
    session = event['data']['object']
    order_id = session['metadata']['order_id']
    
    # Notify customer via SMS or chat
    send_notification(f"Order {order_id} confirmed!")
    
    # Update ticket inventory
    reserve_tickets(order_id)
```

---

## 📊 Payment Statuses

Stripe payment intents have different statuses:

- `requires_payment_method` - Customer needs to enter payment info
- `requires_confirmation` - Payment needs confirmation
- `requires_action` - Customer must authenticate
- `processing` - Payment is being processed
- `requires_capture` - Payment authorized, needs capture
- `succeeded` - Payment completed successfully
- `canceled` - Payment was canceled

---

## 🔒 Security Best Practices

### **1. Never Expose Secret Keys**

```python
# ✅ Good: Load from environment
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# ❌ Bad: Hardcoded
stripe.api_key = "sk_test_xxx"
```

### **2. Always Verify Webhooks**

```python
# ✅ Good: Verify signature
event = stripe.Webhook.construct_event(
    payload, signature, webhook_secret
)

# ❌ Bad: Trust without verification
event = json.loads(payload)
```

### **3. Use Idempotency Keys**

```python
# Prevent duplicate charges
intent = stripe.PaymentIntent.create(
    amount=10000,
    currency='usd',
    idempotency_key=unique_key  # ✅ Recommended
)
```

---

## 🧪 Testing

### **Test Cards**

Use Stripe's test cards:

```python
# Successful payment
card_number = "4242 4242 4242 4242"
exp_date = "12/34"
cvc = "123"

# Declined payment
card_number = "4000 0000 0000 0002"

# Requires authentication
card_number = "4000 0025 0000 3155"
```

### **Test Webhooks**

Use Stripe CLI to test webhooks locally:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local endpoint
stripe listen --forward-to localhost:8000/payments/webhook
```

---

## 💡 Common Use Cases

### **1. Ticket Purchase**

```python
# Customer wants tickets
session = payment_manager.create_checkout_session(
    items=[
        PaymentItem(name='Game Ticket', amount=50.00, quantity=2)
    ],
    success_url='https://site.com/tickets',
    cancel_url='https://site.com/browse'
)

# Send checkout link
send_message(f"Ready to purchase! Click here: {session.url}")
```

### **2. Seat Upgrade**

```python
# Upgrade existing order
intent = payment_manager.create_payment_intent(
    amount=upgrade_fee,
    description=f'Upgrade order {order_id}',
    metadata={'order_id': order_id}
)

# Charge for upgrade
```

### **3. Subscription (Season Tickets)**

```python
# Create recurring payment
subscription = stripe.Subscription.create(
    customer=customer_id,
    items=[{'price': 'price_season_tickets'}]
)
```

---

## 🐛 Troubleshooting

### **Payment Fails**

**Problem**: Payment status is `requires_action`

**Solution**: Customer needs to authenticate (3D Secure)

```python
if intent.status == 'requires_action':
    # Return client secret to frontend
    return {"client_secret": intent.client_secret}
```

### **Webhook Not Receiving Events**

**Problem**: Webhook endpoint not receiving events

**Solutions**:
1. Verify webhook URL is accessible
2. Check webhook secret matches
3. View webhook logs in Stripe Dashboard
4. Test with Stripe CLI

### **Refund Not Processing**

**Problem**: Refund stuck in pending

**Solutions**:
1. Check payment status (must be `succeeded`)
2. Verify enough balance in Stripe account
3. Wait 5-10 business days for processing
4. Check refund reason in dashboard

---

## 📈 Monitoring & Analytics

Track payment metrics:

```python
# Get payment stats
stats = {
    'total_revenue': sum(all_payments),
    'successful_payments': count(succeeded),
    'failed_payments': count(failed),
    'refund_rate': refunds / total * 100
}
```

---

## ✅ Success Checklist

- [ ] Stripe account created
- [ ] API keys configured in `.env`
- [ ] Webhook endpoint set up
- [ ] Test payment successful
- [ ] Webhook receiving events
- [ ] Refund processing works
- [ ] Error handling implemented
- [ ] Customer notifications configured

---

## 🎉 You're Ready!

Your messaging agent can now process payments!

**Next Steps**:
1. Test a payment with test cards
2. Set up webhook handling
3. Integrate with chat flows
4. Monitor payment analytics
5. Go live with production keys

**Happy Processing! 💳✨**
