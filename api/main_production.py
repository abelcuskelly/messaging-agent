"""
Production-Ready FastAPI Application
Complete with all critical enhancements:
- OAuth2/JWT Authentication
- Redis Caching
- Distributed Tracing
- Circuit Breakers
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import uuid
import time
from typing import Optional, Dict, List
import structlog
from contextlib import asynccontextmanager

# Add modules to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tracing.telemetry import get_telemetry, TelemetryMiddleware, TracedCache, TracedEndpoint
from cache.redis_cache import get_cache_manager
from auth.jwt_auth import get_current_active_user, User
from auth.auth_routes import router as auth_router
from resilience.circuit_breaker import circuit_breaker, get_circuit_breaker_manager, CircuitBreakerError

# Initialize services
telemetry = get_telemetry()
logger = structlog.get_logger()
circuit_manager = get_circuit_breaker_manager()

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("🚀 Production API starting with all enhancements")
    
    # Initialize telemetry
    telemetry.instrument_fastapi(app)
    
    # Initialize services
    global traced_cache, traced_endpoint, cache_manager
    cache_manager = get_cache_manager()
    traced_cache = TracedCache(cache_manager.cache, telemetry)
    
    # Register circuit breakers
    circuit_manager.register("model_inference", failure_threshold=3, recovery_timeout=30, timeout=5.0)
    circuit_manager.register("cache_operations", failure_threshold=5, recovery_timeout=15)
    circuit_manager.register("external_api", failure_threshold=3, recovery_timeout=60, timeout=10.0)
    
    logger.info("✅ Circuit breakers registered",
               breakers=list(circuit_manager.breakers.keys()))
    
    # Mock endpoint for demo
    class MockEndpoint:
        def predict(self, instances):
            import time
            time.sleep(0.1)
            return type('obj', (object,), {
                'predictions': [{'response': f"Response: {instances[0]['messages'][-1]['content']}"}]
            })()
    
    traced_endpoint = TracedEndpoint(MockEndpoint(), telemetry)
    
    logger.info("✅ All services initialized")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")
    stats = cache_manager.cache.get_stats()
    logger.info("Final stats", cache=stats)

# Initialize FastAPI app
app = FastAPI(
    title="Qwen Messaging Agent - Production API",
    description="Production-ready API with complete observability and resilience",
    version="4.0.0",
    lifespan=lifespan
)

# Add CORS with security restrictions
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "https://yourdomain.com").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# Add telemetry middleware
app.middleware("http")(TelemetryMiddleware(app, telemetry))

# Include auth routes
app.include_router(auth_router)

# Global services
traced_cache = None
traced_endpoint = None
cache_manager = None
conversations: Dict[str, List[Dict]] = {}

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    use_cache: bool = True
    fallback_on_error: bool = True

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    trace_id: str
    cached: bool = False
    duration_ms: float
    circuit_state: Optional[str] = None
    fallback_used: bool = False


@circuit_breaker("model_inference", failure_threshold=3, recovery_timeout=30, timeout=5.0)
def call_model_with_circuit_breaker(messages: list) -> str:
    """Call model with circuit breaker protection."""
    if traced_endpoint:
        prediction = traced_endpoint.predict([{"messages": messages}])
        return prediction.predictions[0]["response"]
    return "Model unavailable"


@app.post("/chat", response_model=ChatResponse)
@telemetry.traced("chat.request")
async def production_chat(
    request: ChatRequest,
    http_request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Production chat endpoint with complete resilience.
    Features:
    - Authentication & authorization
    - Distributed tracing
    - Caching with circuit breaker
    - Graceful degradation
    - Fallback responses
    """
    start_time = time.time()
    fallback_used = False
    circuit_state = None
    
    with telemetry.span("chat.process") as span:
        span.set_attribute("user.id", current_user.username)
        span.set_attribute("message.length", len(request.message))
        
        # Check cache with circuit breaker
        cached_response = None
        if request.use_cache:
            try:
                with telemetry.span("chat.cache_lookup"):
                    cache_key = f"chat:{hash(request.message.lower().strip())}"
                    
                    # Use circuit breaker for cache operations
                    cache_breaker = circuit_manager.get("cache_operations")
                    if cache_breaker:
                        cached_response = cache_breaker.call(
                            traced_cache.get, cache_key
                        )
                    else:
                        cached_response = traced_cache.get(cache_key)
                    
                    if cached_response:
                        duration_ms = (time.time() - start_time) * 1000
                        span.set_attribute("cache.hit", True)
                        
                        # Get trace ID
                        carrier = {}
                        telemetry.inject_context(carrier)
                        
                        return ChatResponse(
                            response=cached_response,
                            conversation_id=request.conversation_id or str(uuid.uuid4()),
                            trace_id=carrier.get("traceparent", str(uuid.uuid4())),
                            cached=True,
                            duration_ms=duration_ms,
                            circuit_state="closed"
                        )
            
            except CircuitBreakerError as e:
                logger.warning("Cache circuit breaker open", error=str(e))
                span.set_attribute("cache.circuit_open", True)
            except Exception as e:
                logger.error("Cache lookup failed", error=str(e))
        
        # Generate response with circuit breaker
        try:
            with telemetry.span("chat.generate_response"):
                conv_id = request.conversation_id or str(uuid.uuid4())
                if conv_id not in conversations:
                    conversations[conv_id] = []
                
                conversations[conv_id].append({
                    "role": "user",
                    "content": request.message
                })
                
                # Call model with circuit breaker protection
                with telemetry.span("model.inference_protected"):
                    response_text = call_model_with_circuit_breaker(conversations[conv_id])
                    
                    # Get circuit state
                    model_breaker = circuit_manager.get("model_inference")
                    circuit_state = model_breaker.state.value if model_breaker else "unknown"
                
                conversations[conv_id].append({
                    "role": "assistant",
                    "content": response_text
                })
                
                # Cache response (with circuit breaker)
                if request.use_cache:
                    try:
                        cache_breaker = circuit_manager.get("cache_operations")
                        if cache_breaker:
                            cache_breaker.call(
                                traced_cache.set, cache_key, response_text, 3600
                            )
                    except Exception as e:
                        logger.warning("Failed to cache response", error=str(e))
        
        except CircuitBreakerError as e:
            # Circuit breaker open - use fallback
            logger.warning("Model circuit breaker open", error=str(e))
            span.set_attribute("circuit_breaker.open", True)
            
            if request.fallback_on_error:
                response_text = self._get_fallback_response(request.message)
                fallback_used = True
                circuit_state = "open"
            else:
                raise HTTPException(
                    status_code=503,
                    detail="Service temporarily unavailable. Circuit breaker is open."
                )
        
        except Exception as e:
            logger.error("Model inference failed", error=str(e))
            
            if request.fallback_on_error:
                response_text = self._get_fallback_response(request.message)
                fallback_used = True
            else:
                raise HTTPException(status_code=500, detail=str(e))
        
        duration_ms = (time.time() - start_time) * 1000
        span.set_attribute("duration_ms", duration_ms)
        span.set_attribute("fallback_used", fallback_used)
        
        # Get trace ID
        carrier = {}
        telemetry.inject_context(carrier)
        
        return ChatResponse(
            response=response_text,
            conversation_id=conv_id,
            trace_id=carrier.get("traceparent", str(uuid.uuid4())),
            cached=False,
            duration_ms=duration_ms,
            circuit_state=circuit_state,
            fallback_used=fallback_used
        )


def _get_fallback_response(message: str) -> str:
    """Get fallback response when service is unavailable."""
    fallback_responses = {
        "price": "I'm experiencing technical difficulties. Please visit our website for current ticket prices or contact support.",
        "refund": "For refund inquiries, please contact our support team at support@example.com or call 1-800-TICKETS.",
        "upgrade": "Seat upgrades are available up to 2 hours before game time. Please try again shortly or contact support.",
        "default": "I'm currently experiencing technical difficulties. Please try again in a few moments or contact our support team."
    }
    
    message_lower = message.lower()
    for key, response in fallback_responses.items():
        if key in message_lower:
            return response
    
    return fallback_responses["default"]


@app.get("/circuit-breakers")
async def get_circuit_breakers(
    current_user: User = Depends(get_current_active_user)
):
    """Get status of all circuit breakers."""
    if "admin" not in current_user.scopes and "view_dashboard" not in current_user.scopes:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    stats = circuit_manager.get_all_stats()
    return {"circuit_breakers": stats}


@app.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(
    name: str,
    current_user: User = Depends(get_current_active_user)
):
    """Manually reset a circuit breaker (admin only)."""
    if "admin" not in current_user.scopes:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    breaker = circuit_manager.get(name)
    if not breaker:
        raise HTTPException(status_code=404, detail=f"Circuit breaker '{name}' not found")
    
    breaker.reset()
    logger.info("Circuit breaker reset", name=name, by_user=current_user.username)
    
    return {"message": f"Circuit breaker '{name}' reset to CLOSED state"}


@app.post("/circuit-breakers/reset-all")
async def reset_all_circuit_breakers(
    current_user: User = Depends(get_current_active_user)
):
    """Reset all circuit breakers (admin only)."""
    if "admin" not in current_user.scopes:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    circuit_manager.reset_all()
    logger.info("All circuit breakers reset", by_user=current_user.username)
    
    return {"message": "All circuit breakers reset"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "4.0.0",
        "features": [
            "authentication",
            "caching",
            "tracing",
            "circuit_breakers"
        ]
    }


@app.get("/ready")
async def readiness():
    """Comprehensive readiness check."""
    with telemetry.span("readiness.check"):
        checks = {
            "cache": False,
            "telemetry": True,
            "circuit_breakers": False,
            "overall": False
        }
        
        # Check cache
        try:
            if traced_cache:
                traced_cache.cache.client.ping()
                checks["cache"] = True
        except Exception as e:
            logger.warning("Cache check failed", error=str(e))
        
        # Check circuit breakers
        try:
            stats = circuit_manager.get_all_stats()
            open_breakers = [
                name for name, stat in stats.items()
                if stat["state"] == "open"
            ]
            checks["circuit_breakers"] = len(open_breakers) == 0
            checks["open_breakers"] = open_breakers
        except Exception as e:
            logger.warning("Circuit breaker check failed", error=str(e))
        
        checks["overall"] = checks["cache"] and checks["telemetry"]
        status_code = 200 if checks["overall"] else 503
        
        return checks, status_code


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Production API with All Enhancements")
    print("\n✅ Features Enabled:")
    print("   - OAuth2/JWT Authentication")
    print("   - Redis Caching Layer")
    print("   - OpenTelemetry Tracing")
    print("   - Circuit Breakers")
    print("\n📊 Monitoring:")
    print("   - Jaeger UI: http://localhost:16686")
    print("   - Prometheus: http://localhost:9090/metrics")
    print("   - Circuit Breakers: GET /circuit-breakers")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
