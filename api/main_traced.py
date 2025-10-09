"""
FastAPI Application with OpenTelemetry Distributed Tracing
Complete observability with traces, metrics, and logs
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

# Initialize telemetry
telemetry = get_telemetry()
logger = structlog.get_logger()

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Application starting with telemetry")
    telemetry.instrument_fastapi(app)
    
    # Initialize services
    global traced_cache, traced_endpoint
    cache_manager = get_cache_manager()
    traced_cache = TracedCache(cache_manager.cache, telemetry)
    
    # Mock endpoint for demo (replace with actual)
    class MockEndpoint:
        def predict(self, instances):
            import time
            time.sleep(0.1)
            return type('obj', (object,), {
                'predictions': [{'response': f"Response to: {instances[0]['messages'][-1]['content']}"}]
            })()
    
    traced_endpoint = TracedEndpoint(MockEndpoint(), telemetry)
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")
    stats = cache_manager.cache.get_stats()
    logger.info("Final cache stats", **stats)

# Initialize FastAPI app
app = FastAPI(
    title="Qwen Messaging Agent API with Telemetry",
    description="Fully observable API with distributed tracing",
    version="3.0.0",
    lifespan=lifespan
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add telemetry middleware
app.middleware("http")(TelemetryMiddleware(app, telemetry))

# Include auth routes
app.include_router(auth_router)

# Global services
traced_cache = None
traced_endpoint = None
conversations: Dict[str, List[Dict]] = {}

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    trace_id: Optional[str] = None  # Allow trace propagation

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    trace_id: str
    cached: bool = False
    duration_ms: float


@app.post("/chat", response_model=ChatResponse)
@telemetry.traced("chat.request")
async def chat_with_tracing(
    request: ChatRequest,
    http_request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Chat endpoint with full observability.
    Traces cache lookups, model predictions, and response generation.
    """
    start_time = time.time()
    
    # Get or create trace context
    if request.trace_id:
        carrier = {"traceparent": request.trace_id}
        telemetry.extract_context(carrier)
    
    with telemetry.span("chat.process") as span:
        # Add span attributes
        span.set_attribute("user.id", current_user.username)
        span.set_attribute("message.length", len(request.message))
        span.set_attribute("conversation.id", request.conversation_id or "new")
        
        # Check cache
        with telemetry.span("chat.cache_lookup"):
            cache_key = f"chat:{hash(request.message.lower().strip())}"
            cached_response = traced_cache.get(cache_key) if traced_cache else None
        
        if cached_response:
            duration_ms = (time.time() - start_time) * 1000
            span.set_attribute("cache.hit", True)
            span.set_attribute("duration_ms", duration_ms)
            
            logger.info("Chat cache hit", 
                       user=current_user.username,
                       duration_ms=duration_ms)
            
            # Get current trace ID
            carrier = {}
            telemetry.inject_context(carrier)
            trace_id = carrier.get("traceparent", str(uuid.uuid4()))
            
            return ChatResponse(
                response=cached_response,
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                trace_id=trace_id,
                cached=True,
                duration_ms=duration_ms
            )
        
        # Generate response
        with telemetry.span("chat.generate_response"):
            # Get or create conversation
            conv_id = request.conversation_id or str(uuid.uuid4())
            if conv_id not in conversations:
                conversations[conv_id] = []
            
            # Add user message
            conversations[conv_id].append({
                "role": "user",
                "content": request.message
            })
            
            # Model prediction with tracing
            with telemetry.span("model.inference"):
                if traced_endpoint:
                    prediction = traced_endpoint.predict([{"messages": conversations[conv_id]}])
                    response_text = prediction.predictions[0]["response"]
                else:
                    response_text = f"Mock response to: {request.message}"
            
            # Add assistant response
            conversations[conv_id].append({
                "role": "assistant",
                "content": response_text
            })
            
            # Cache response
            with telemetry.span("chat.cache_store"):
                if traced_cache:
                    traced_cache.set(cache_key, response_text, 3600)
        
        duration_ms = (time.time() - start_time) * 1000
        span.set_attribute("cache.hit", False)
        span.set_attribute("duration_ms", duration_ms)
        span.set_attribute("response.length", len(response_text))
        
        # Get current trace ID
        carrier = {}
        telemetry.inject_context(carrier)
        trace_id = carrier.get("traceparent", str(uuid.uuid4()))
        
        logger.info("Chat request completed",
                   user=current_user.username,
                   conversation_id=conv_id,
                   duration_ms=duration_ms,
                   trace_id=trace_id)
        
        return ChatResponse(
            response=response_text,
            conversation_id=conv_id,
            trace_id=trace_id,
            cached=False,
            duration_ms=duration_ms
        )


@app.get("/trace/{trace_id}")
@telemetry.traced("trace.lookup")
async def get_trace_info(
    trace_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get trace information for debugging.
    In production, this would query your tracing backend.
    """
    with telemetry.span("trace.query") as span:
        span.set_attribute("trace.id", trace_id)
        span.set_attribute("user.id", current_user.username)
        
        # Mock trace data (in production, query Jaeger/Tempo)
        trace_data = {
            "trace_id": trace_id,
            "service": telemetry.config.service_name,
            "environment": telemetry.config.environment,
            "spans": [
                {
                    "name": "chat.request",
                    "duration_ms": 150,
                    "children": [
                        {"name": "cache.lookup", "duration_ms": 5},
                        {"name": "model.inference", "duration_ms": 100},
                        {"name": "cache.store", "duration_ms": 3}
                    ]
                }
            ],
            "metrics": {
                "total_duration_ms": 150,
                "cache_hit": False,
                "model_latency_ms": 100
            }
        }
        
        return trace_data


@app.get("/metrics")
async def get_metrics():
    """
    Get application metrics.
    Prometheus format available at :9090/metrics
    """
    with telemetry.span("metrics.collect"):
        # Get cache stats
        cache_stats = {}
        if traced_cache:
            cache_stats = traced_cache.cache.get_stats()
        
        # Calculate metrics
        metrics = {
            "cache": cache_stats,
            "telemetry": {
                "service": telemetry.config.service_name,
                "version": telemetry.config.service_version,
                "environment": telemetry.config.environment,
                "prometheus_endpoint": f"http://localhost:{telemetry.config.prometheus_port}/metrics"
            },
            "traces": {
                "jaeger_ui": f"http://localhost:16686/search?service={telemetry.config.service_name}",
                "sampling_rate": telemetry.config.sampling_rate
            }
        }
        
        return metrics


@app.post("/trace/baggage")
@telemetry.traced("baggage.set")
async def set_baggage(
    key: str,
    value: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Set baggage for trace propagation.
    Baggage is propagated across service boundaries.
    """
    token = telemetry.add_baggage(key, value)
    
    logger.info("Baggage set", key=key, value=value, user=current_user.username)
    
    return {
        "message": "Baggage set",
        "key": key,
        "value": value
    }


@app.get("/trace/baggage/{key}")
@telemetry.traced("baggage.get")
async def get_baggage(
    key: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get baggage value from current trace context."""
    value = telemetry.get_baggage(key)
    
    return {
        "key": key,
        "value": value
    }


@app.post("/simulate/distributed")
@telemetry.traced("simulate.distributed_call")
async def simulate_distributed_call(
    service: str = "downstream-service",
    current_user: User = Depends(get_current_active_user)
):
    """
    Simulate a distributed service call with trace propagation.
    Demonstrates how traces flow across service boundaries.
    """
    with telemetry.span("distributed.prepare") as span:
        span.set_attribute("target.service", service)
        span.set_attribute("user.id", current_user.username)
        
        # Prepare headers with trace context
        headers = {}
        telemetry.inject_context(headers)
        
        # Simulate service call
        with telemetry.span("distributed.call", {
            "service.name": service,
            "rpc.method": "process"
        }):
            import asyncio
            await asyncio.sleep(0.1)  # Simulate network latency
            
            # Simulate processing in downstream service
            with telemetry.span(f"{service}.process"):
                await asyncio.sleep(0.05)  # Simulate processing
                result = f"Processed by {service}"
        
        return {
            "result": result,
            "trace_headers": headers,
            "service": service
        }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "telemetry": "enabled"
    }


@app.get("/ready")
async def readiness():
    """Readiness check with telemetry."""
    with telemetry.span("readiness.check"):
        checks = {
            "cache": False,
            "telemetry": True,
            "overall": False
        }
        
        # Check cache
        try:
            if traced_cache:
                traced_cache.cache.client.ping()
                checks["cache"] = True
        except Exception as e:
            logger.warning("Cache check failed", error=str(e))
        
        checks["overall"] = checks["cache"] and checks["telemetry"]
        status_code = 200 if checks["overall"] else 503
        
        return checks, status_code


# Error handler with tracing
@app.exception_handler(Exception)
async def traced_exception_handler(request: Request, exc: Exception):
    """Handle exceptions with proper tracing."""
    with telemetry.span("error.handler") as span:
        span.record_exception(exc)
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
        
        telemetry.error_counter.add(1, {"type": "unhandled_exception"})
        
        logger.error("Unhandled exception", 
                    error=str(exc),
                    path=request.url.path,
                    method=request.method)
        
        return {
            "error": "Internal server error",
            "message": str(exc),
            "trace_id": span.get_span_context().trace_id
        }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting API with OpenTelemetry Distributed Tracing")
    print("\n📊 Metrics available at: http://localhost:9090/metrics")
    print("🔍 Jaeger UI available at: http://localhost:16686")
    print("\nMake sure Jaeger is running:")
    print("  docker run -p 16686:16686 -p 14250:14250 jaegertracing/all-in-one")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
