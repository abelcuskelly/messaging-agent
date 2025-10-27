"""
Stripe Payment API Routes
FastAPI endpoints for payment processing
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Request, Body
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from integrations.payments.stripe_client import (
    StripePaymentManager,
    PaymentItem,
    PaymentIntent,
    CheckoutSession
)
from auth.jwt_auth import get_current_active_user, User, check_scopes
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/payments", tags=["payments"])

# Initialize payment manager
payment_manager = StripePaymentManager()


# Request models
class CreatePaymentIntentRequest(BaseModel):
    amount: float
    currency: str = 'usd'
    customer_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CreateCheckoutRequest(BaseModel):
    items: List[Dict[str, Any]]
    success_url: str
    cancel_url: str
    customer_email: Optional[EmailStr] = None
    customer_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RefundRequest(BaseModel):
    payment_intent_id: str
    amount: Optional[float] = None


# Routes

@router.post("/intent/create")
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    current_user: User = Depends(check_scopes(["admin", "create_payment"]))
):
    """
    Create a Stripe payment intent.
    
    Use this to initiate a payment that will be processed by the customer.
    """
    try:
        intent = payment_manager.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            customer_id=request.customer_id,
            description=request.description,
            metadata=request.metadata
        )
        
        logger.info(
            "Payment intent created via API",
            intent_id=intent.id,
            amount=request.amount,
            user_id=current_user.username
        )
        
        return {
            "success": True,
            "payment_intent": {
                "id": intent.id,
                "amount": intent.amount / 100,  # Convert from cents
                "currency": intent.currency,
                "status": intent.status,
                "client_secret": payment_manager.secret_key  # Would use actual secret
            }
        }
        
    except Exception as e:
        logger.error("Failed to create payment intent", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checkout/create")
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: User = Depends(check_scopes(["admin", "create_payment"]))
):
    """
    Create a Stripe checkout session.
    
    Returns a URL that redirects customers to Stripe's hosted checkout page.
    """
    try:
        # Convert items to PaymentItem objects
        items = [
            PaymentItem(
                name=item['name'],
                description=item.get('description'),
                amount=item['amount'],
                quantity=item.get('quantity', 1),
                metadata=item.get('metadata')
            )
            for item in request.items
        ]
        
        session = payment_manager.create_checkout_session(
            items=items,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            customer_email=request.customer_email,
            customer_id=request.customer_id,
            metadata=request.metadata
        )
        
        logger.info(
            "Checkout session created via API",
            session_id=session.id,
            user_id=current_user.username
        )
        
        return {
            "success": True,
            "checkout_session": {
                "id": session.id,
                "url": session.url,
                "status": session.payment_status
            }
        }
        
    except Exception as e:
        logger.error("Failed to create checkout session", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intent/{payment_intent_id}/status")
async def get_payment_status(
    payment_intent_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get status of a payment intent."""
    try:
        intent = payment_manager.get_payment_status(payment_intent_id)
        
        return {
            "payment_intent": {
                "id": intent.id,
                "amount": intent.amount / 100,  # Convert from cents
                "currency": intent.currency,
                "status": intent.status,
                "customer_id": intent.customer_id,
                "metadata": intent.metadata,
                "created_at": intent.created_at.isoformat() if intent.created_at else None
            }
        }
        
    except Exception as e:
        logger.error("Failed to get payment status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intent/{payment_intent_id}/cancel")
async def cancel_payment(
    payment_intent_id: str,
    current_user: User = Depends(check_scopes(["admin", "cancel_payment"]))
):
    """Cancel a payment intent."""
    try:
        intent = payment_manager.cancel_payment_intent(payment_intent_id)
        
        logger.info(
            "Payment cancelled via API",
            intent_id=payment_intent_id,
            user_id=current_user.username
        )
        
        return {
            "success": True,
            "payment_intent": {
                "id": intent.id,
                "status": intent.status,
                "cancelled": True
            }
        }
        
    except Exception as e:
        logger.error("Failed to cancel payment", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refund")
async def refund_payment(
    request: RefundRequest,
    current_user: User = Depends(check_scopes(["admin", "refund_payment"]))
):
    """Refund a payment."""
    try:
        refund = payment_manager.refund_payment(
            payment_intent_id=request.payment_intent_id,
            amount=request.amount
        )
        
        logger.info(
            "Payment refunded via API",
            payment_intent_id=request.payment_intent_id,
            amount=request.amount,
            user_id=current_user.username
        )
        
        return {
            "success": True,
            "refund": refund
        }
        
    except Exception as e:
        logger.error("Failed to refund payment", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customer/create")
async def create_customer(
    email: EmailStr,
    name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(check_scopes(["admin"]))
):
    """Create a Stripe customer."""
    try:
        customer = payment_manager.create_customer(email, name, metadata)
        
        logger.info(
            "Customer created via API",
            customer_id=customer['id'],
            email=email,
            user_id=current_user.username
        )
        
        return {
            "success": True,
            "customer": customer
        }
        
    except Exception as e:
        logger.error("Failed to create customer", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer/{customer_id}")
async def get_customer(
    customer_id: str,
    current_user: User = Depends(check_scopes(["admin", "view_customers"]))
):
    """Get customer details."""
    try:
        customer = payment_manager.get_customer(customer_id)
        
        return {
            "success": True,
            "customer": customer
        }
        
    except Exception as e:
        logger.error("Failed to get customer", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., name="Stripe-Signature")
):
    """
    Handle Stripe webhook events.
    
    This endpoint receives events from Stripe about payment status changes.
    """
    try:
        # Get raw body
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Process webhook
        event = payment_manager.process_webhook(body_str, stripe_signature)
        
        logger.info("Webhook processed successfully", event_type=event.get('type'))
        
        return {
            "success": True,
            "event": event
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        logger.error("Webhook processing failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/health")
async def payment_health_check(
    current_user: User = Depends(get_current_active_user)
):
    """Check payment system health."""
    return {
        "status": "healthy",
        "stripe_configured": bool(payment_manager.secret_key),
        "webhook_configured": bool(payment_manager.webhook_secret)
    }
