"""
Stripe Payment Integration
Process payments through the messaging agent
"""

import os
import stripe
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')


@dataclass
class PaymentItem:
    """Item in a payment."""
    name: str
    description: Optional[str] = None
    amount: float = 0.0
    quantity: int = 1
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PaymentIntent:
    """Payment intent data."""
    id: str
    amount: int  # in cents
    currency: str
    status: str
    customer_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CheckoutSession:
    """Checkout session data."""
    id: str
    url: str
    payment_status: str
    customer_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class StripePaymentManager:
    """
    Stripe payment processing manager.
    Handles payment intents, checkout sessions, and webhooks.
    """
    
    def __init__(self):
        """Initialize Stripe client."""
        self.secret_key = os.getenv('STRIPE_SECRET_KEY')
        self.publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        if not self.secret_key:
            logger.warning("Stripe secret key not configured")
        
        stripe.api_key = self.secret_key
        
        self.logger = logger
    
    def create_payment_intent(
        self,
        amount: float,
        currency: str = 'usd',
        customer_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        metadata_input: Optional[Dict[str, Any]] = None
    ) -> PaymentIntent:
        """
        Create a Stripe payment intent.
        
        Args:
            amount: Amount in dollars
            currency: Currency code (default: 'usd')
            customer_id: Stripe customer ID (optional)
            description: Payment description (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            PaymentIntent object
        """
        if not self.secret_key:
            raise ValueError("Stripe secret key not configured")
        
        # Convert to cents
        amount_cents = int(amount * 100)
        
        params = {
            'amount': amount_cents,
            'currency': currency,
            'payment_method_types': ['card'],
        }
        
        if customer_id:
            params['customer'] = customer_id
        
        if description:
            params['description'] = description
        
        if metadata:
            params['metadata'] = metadata
        
        try:
            intent = stripe.PaymentIntent.create(**params)
            
            self.logger.info(
                "Payment intent created",
                intent_id=intent.id,
                amount=amount,
                customer_id=customer_id
            )
            
            return PaymentIntent(
                id=intent.id,
                amount=intent.amount,
                currency=intent.currency,
                status=intent.status,
                customer_id=intent.customer,
                metadata=intent.metadata,
                created_at=datetime.fromtimestamp(intent.created)
            )
            
        except stripe.error.StripeError as e:
            self.logger.error("Failed to create payment intent", error=str(e))
            raise
    
    def create_checkout_session(
        self,
        items: List[PaymentItem],
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        allow_promotion_codes: bool = True
    ) -> CheckoutSession:
        """
        Create a Stripe checkout session.
        
        Args:
            items: List of items to purchase
            success_url: URL to redirect after success
            cancel_url: URL to redirect after cancellation
            customer_email: Customer email (optional)
            customer_id: Stripe customer ID (optional)
            metadata: Additional metadata (optional)
            allow_promotion_codes: Allow promo codes (default: True)
            
        Returns:
            CheckoutSession object
        """
        if not self.secret_key:
            raise ValueError("Stripe secret key not configured")
        
        # Convert items to Stripe line items
        line_items = [
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.name,
                        'description': item.description,
                    },
                    'unit_amount': int(item.amount * 100),
                },
                'quantity': item.quantity,
            }
            for item in items
        ]
        
        params = {
            'line_items': line_items,
            'mode': 'payment',
            'success_url': success_url,
            'cancel_url': cancel_url,
            'allow_promotion_codes': allow_promotion_codes,
        }
        
        if customer_email:
            params['customer_email'] = customer_email
        
        if customer_id:
            params['customer'] = customer_id
        
        if metadata:
            params['metadata'] = metadata
        
        try:
            session = stripe.checkout.Session.create(**params)
            
            self.logger.info(
                "Checkout session created",
                session_id=session.id,
                customer_email=customer_email,
                amount=sum(item.amount for item in items)
            )
            
            return CheckoutSession(
                id=session.id,
                url=session.url,
                payment_status=session.payment_status,
                customer_id=session.customer,
                metadata=session.metadata,
                created_at=datetime.fromtimestamp(session.created)
            )
            
        except stripe.error.StripeError as e:
            self.logger.error("Failed to create checkout session", error=str(e))
            raise
    
    def get_payment_status(self, payment_intent_id: str) -> PaymentIntent:
        """
        Get status of a payment intent.
        
        Args:
            payment_intent_id: Payment intent ID
            
        Returns:
            PaymentIntent object with status
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return PaymentIntent(
                id=intent.id,
                amount=intent.amount,
                currency=intent.currency,
                status=intent.status,
                customer_id=intent.customer,
                metadata=intent.metadata,
                created_at=datetime.fromtimestamp(intent.created)
            )
            
        except stripe.error.StripeError as e:
            self.logger.error("Failed to get payment status", error=str(e))
            raise
    
    def cancel_payment_intent(self, payment_intent_id: str) -> PaymentIntent:
        """
        Cancel a payment intent.
        
        Args:
            payment_intent_id: Payment intent ID to cancel
            
        Returns:
            PaymentIntent object with cancelled status
        """
        try:
            intent = stripe.PaymentIntent.cancel(payment_intent_id)
            
            self.logger.info("Payment intent cancelled", intent_id=payment_intent_id)
            
            return PaymentIntent(
                id=intent.id,
                amount=intent.amount,
                currency=intent.currency,
                status=intent.status,
                customer_id=intent.customer,
                metadata=intent.metadata,
                created_at=datetime.fromtimestamp(intent.created)
            )
            
        except stripe.error.StripeError as e:
            self.logger.error("Failed to cancel payment", error=str(e))
            raise
    
    def refund_payment(self, payment_intent_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """
        Refund a payment.
        
        Args:
            payment_intent_id: Payment intent ID
            amount: Amount to refund in dollars (None = full refund)
            
        Returns:
            Refund details
        """
        try:
            params = {'payment_intent': payment_intent_id}
            
            if amount:
                params['amount'] = int(amount * 100)  # Convert to cents
            
            refund = stripe.Refund.create(**params)
            
            self.logger.info(
                "Payment refunded",
                refund_id=refund.id,
                payment_intent_id=payment_intent_id,
                amount=amount
            )
            
            return {
                'id': refund.id,
                'amount': refund.amount / 100,  # Convert back to dollars
                'status': refund.status,
                'created_at': datetime.fromtimestamp(refund.created)
            }
            
        except stripe.error.StripeError as e:
            self.logger.error("Failed to refund payment", error=str(e))
            raise
    
    def create_customer(self, email: str, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a Stripe customer.
        
        Args:
            email: Customer email
            name: Customer name (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Customer details
        """
        try:
            params = {'email': email}
            
            if name:
                params['name'] = name
            
            if metadata:
                params['metadata'] = metadata
            
            customer = stripe.Customer.create(**params)
            
            self.logger.info("Customer created", customer_id=customer.id, email=email)
            
            return {
                'id': customer.id,
                'email': customer.email,
                'name': customer.name,
                'created_at': datetime.fromtimestamp(customer.created)
            }
            
        except stripe.error.StripeError as e:
            self.logger.error("Failed to create customer", error=str(e))
            raise
    
    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer details.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Customer details
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)
            
            return {
                'id': customer.id,
                'email': customer.email,
                'name': customer.name,
                'created_at': datetime.fromtimestamp(customer.created),
                'metadata': customer.metadata
            }
            
        except stripe.error.StripeError as e:
            self.logger.error("Failed to get customer", error=str(e))
            raise
    
    def process_webhook(self, payload: str, signature: str) -> Dict[str, Any]:
        """
        Process Stripe webhook event.
        
        Args:
            payload: Webhook payload (raw request body)
            signature: Stripe signature from header
            
        Returns:
            Event details
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured")
            return {}
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            self.logger.info("Webhook event received", event_type=event['type'])
            
            # Handle different event types
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                self.logger.info(
                    "Payment succeeded",
                    payment_intent_id=payment_intent['id'],
                    amount=payment_intent['amount'] / 100
                )
            
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                self.logger.warning(
                    "Payment failed",
                    payment_intent_id=payment_intent['id'],
                    error=payment_intent.get('last_payment_error')
                )
            
            elif event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                self.logger.info(
                    "Checkout completed",
                    session_id=session['id'],
                    customer_email=session.get('customer_details', {}).get('email')
                )
            
            return {
                'type': event['type'],
                'event_id': event['id'],
                'livemode': event['livemode'],
                'data': event['data']
            }
            
        except ValueError as e:
            # Invalid payload
            self.logger.error("Invalid webhook payload", error=str(e))
            raise
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            self.logger.error("Invalid webhook signature", error=str(e))
            raise
