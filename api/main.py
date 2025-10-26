from fastapi import FastAPI, HTTPException, Depends, Header, Request
from pydantic import BaseModel
from google.cloud import aiplatform
import os
import uuid
import time
import json
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import redis
from typing import Optional
from log_handler import ConversationLogger

# Import orchestration optimizations
import sys
sys.path.append('..')
from orchestration import get_optimizer, PerformanceMetrics

# Import security utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from security.sanitization import sanitize_user_input, sanitize_for_logging
from security.middleware import add_security_middleware

# Import Twilio SMS routes (if available)
try:
    from integrations.twilio_routes import router as twilio_router
    TWILIO_ENABLED = True
except ImportError:
    print("⚠️  Twilio integration not available. Install twilio package.")
    TWILIO_ENABLED = False
    twilio_router = None


app = FastAPI()

# Add security middleware
add_security_middleware(app, strict_mode=True)

# Include Twilio SMS routes (if available)
if TWILIO_ENABLED and twilio_router:
    app.include_router(twilio_router)
    logger.info("Twilio SMS integration enabled")

# Configure structured logging
logger = structlog.get_logger()

# Redis client for rate limiting
_redis_client: Optional[redis.Redis] = None

# BigQuery logger
_conversation_logger: Optional[ConversationLogger] = None

# Initialize optimizer
optimizer = get_optimizer()
optimizer.enable_caching = True
optimizer.enable_batching = True
logger.info("Orchestration optimizer initialized", caching=True, batching=True)


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    user_id: str | None = None  # For context prefetching


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    cached: bool = False
    response_time_ms: float = 0


class ErrorResponse(BaseModel):
    error: str
    detail: str
    request_id: str
    timestamp: str


# In-memory conversation storage (use Redis/Firestore in production)
conversations: dict[str, list[dict[str, str]]] = {}

# Lazy-initialized Vertex AI Endpoint
_endpoint: aiplatform.Endpoint | None = None


def _endpoint_path() -> str:
    project_id = os.getenv("PROJECT_ID", "your-project-id")
    region = os.getenv("REGION", "us-central1")
    endpoint_id = os.getenv("ENDPOINT_ID", "your-endpoint-id")
    return f"projects/{project_id}/locations/{region}/endpoints/{endpoint_id}"


def _get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client for rate limiting."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                _redis_client = redis.from_url(redis_url, decode_responses=True)
                _redis_client.ping()  # Test connection
                logger.info("Redis connected", url=redis_url)
            except Exception as e:
                logger.warning("Redis connection failed", error=str(e))
                _redis_client = None
    return _redis_client


def _rate_limit_check(request: Request, x_api_key: str | None = None) -> None:
    """Check rate limits using Redis or in-memory fallback."""
    client = _get_redis_client()
    if not client:
        return  # No rate limiting if Redis unavailable
    
    # Use API key or IP as identifier
    identifier = x_api_key or request.client.host
    key = f"rate_limit:{identifier}"
    
    # Allow 60 requests per minute
    limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    window = 60
    
    try:
        current = client.incr(key)
        if current == 1:
            client.expire(key, window)
        if current > limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limit} requests per minute"
            )
    except redis.RedisError as e:
        logger.warning("Rate limit check failed", error=str(e))


def _get_conversation_logger() -> Optional[ConversationLogger]:
    """Get BigQuery conversation logger."""
    global _conversation_logger
    if _conversation_logger is None:
        try:
            _conversation_logger = ConversationLogger()
            logger.info("BigQuery conversation logger initialized")
        except Exception as e:
            logger.warning("BigQuery logger initialization failed", error=str(e))
            _conversation_logger = None
    return _conversation_logger


def _require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Simple header-based API key check. If API_KEY env is set, enforce it."""
    expected = os.getenv("API_KEY")
    if expected:
        if not x_api_key or x_api_key != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")


@app.on_event("startup")
def startup_event():
    global _endpoint
    project_id = os.getenv("PROJECT_ID", "your-project-id")
    region = os.getenv("REGION", "us-central1")
    aiplatform.init(project=project_id, location=region)
    try:
        _endpoint = aiplatform.Endpoint(_endpoint_path())
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to initialize Vertex AI endpoint: {exc}") from exc


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((Exception,)),
)
def _predict_with_retry(messages: list) -> str:
    """Make prediction with retry logic."""
    if _endpoint is None:
        raise RuntimeError("Endpoint not initialized")
    
    prediction = _endpoint.predict(instances=[{"messages": messages}])
    if not prediction.predictions:
        raise ValueError("Empty predictions from endpoint")
    
    return prediction.predictions[0]["response"]


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(_require_api_key)])
async def chat(
    request: ChatRequest,
    http_request: Request,
    x_api_key: str | None = Header(default=None)
):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    cached = False
    
    try:
        # Rate limiting
        _rate_limit_check(http_request, x_api_key)
        
        if _endpoint is None:
            raise HTTPException(status_code=500, detail="Endpoint not initialized")

        conv_id = request.conversation_id or str(uuid.uuid4())

        # Sanitize user input
        sanitized_message = sanitize_user_input(request.message)
        
        # OPTIMIZATION 1: Check cache for common queries
        cached_response = optimizer.get_common_query_response(sanitized_message)
        if cached_response:
            logger.info(
                "Cache hit",
                request_id=request_id,
                conversation_id=conv_id,
                message=sanitize_for_logging(sanitized_message[:50])
            )
            
            response_time = (time.time() - start_time) * 1000
            
            # Record metrics
            metrics = PerformanceMetrics(
                response_time_ms=response_time,
                token_count=0,
                cache_hit=True,
                tool_calls=0,
                rag_queries=0
            )
            optimizer.record_metrics(metrics)
            
            return ChatResponse(
                response=cached_response,
                conversation_id=conv_id,
                cached=True,
                response_time_ms=response_time
            )

        # Get or create conversation history
        if conv_id not in conversations:
            conversations[conv_id] = []

        # Add user message (sanitized)
        conversations[conv_id].append({"role": "user", "content": sanitized_message})

        # OPTIMIZATION 2: Compress prompt if conversation is long
        max_tokens = int(os.getenv("MAX_CONTEXT_TOKENS", "2000"))
        compressed_messages = optimizer.compress_prompt(
            conversations[conv_id],
            max_tokens=max_tokens
        )
        
        if len(compressed_messages) < len(conversations[conv_id]):
            logger.info(
                "Prompt compressed",
                original_length=len(conversations[conv_id]),
                compressed_length=len(compressed_messages)
            )

        # OPTIMIZATION 3: Prefetch user context if user_id provided
        if request.user_id:
            user_context = await optimizer.prefetch_context(request.user_id)
            logger.info(
                "User context prefetched",
                user_id=request.user_id,
                context_keys=list(user_context.keys())
            )

        # Get prediction from Vertex AI with retry
        response_text = _predict_with_retry(compressed_messages)

        # OPTIMIZATION 4: Cache response for common queries
        # Only cache if it's a simple query (short message, no conversation history)
        if len(sanitized_message) < 200 and not request.conversation_id:
            optimizer.cache_response(sanitized_message, response_text)
            logger.info("Response cached", query=sanitize_for_logging(sanitized_message[:50]))

        # Add assistant response to history
        conversations[conv_id].append({"role": "assistant", "content": response_text})

        # Log success
        duration = time.time() - start_time
        duration_ms = int(duration * 1000)
        
        logger.info(
            "Chat request completed",
            request_id=request_id,
            conversation_id=conv_id,
            duration=duration,
            message_length=len(sanitized_message),
            response_length=len(response_text),
            cached=cached,
            compressed=len(compressed_messages) < len(conversations[conv_id])
        )

        # Record performance metrics
        metrics = PerformanceMetrics(
            response_time_ms=duration_ms,
            token_count=len(response_text.split()),  # Rough estimate
            cache_hit=False,
            tool_calls=0,  # TODO: Track actual tool calls
            rag_queries=0  # TODO: Track actual RAG queries
        )
        optimizer.record_metrics(metrics)

        # Log to BigQuery
        conversation_logger = _get_conversation_logger()
        if conversation_logger:
            conversation_logger.log_interaction(
                conversation_id=conv_id,
                user_message=request.message,
                agent_response=response_text,
                request_id=request_id,
                duration_ms=duration_ms,
                status="success"
            )

        return ChatResponse(
            response=response_text,
            conversation_id=conv_id,
            cached=False,
            response_time_ms=duration_ms
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        # Log error and return structured error response
        duration = time.time() - start_time
        duration_ms = int(duration * 1000)
        error_detail = str(exc)
        
        logger.error(
            "Chat request failed",
            request_id=request_id,
            error=error_detail,
            duration=duration,
            message_length=len(request.message) if request else 0
        )

        # Log error to BigQuery
        conversation_logger = _get_conversation_logger()
        if conversation_logger and request:
            conversation_logger.log_error(
                conversation_id=request.conversation_id or "unknown",
                user_message=request.message,
                error_detail=error_detail,
                request_id=request_id,
                duration_ms=duration_ms
            )
        
        # Determine appropriate status code
        if "Rate limit" in error_detail:
            status_code = 429
        elif "not initialized" in error_detail:
            status_code = 503
        else:
            status_code = 500
            
        raise HTTPException(
            status_code=status_code,
            detail=ErrorResponse(
                error="Chat request failed",
                detail=error_detail,
                request_id=request_id,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            ).model_dump()
        )


@app.get("/health")
async def health():
    """Basic health check - always returns healthy if service is running."""
    return {"status": "healthy"}


@app.get("/ready")
async def readiness():
    """Readiness check - validates all dependencies are available."""
    checks = {
        "vertex_endpoint": False,
        "redis": False,
        "overall": False
    }
    
    # Check Vertex AI endpoint
    try:
        if _endpoint is not None:
            # Try a simple prediction to verify endpoint is responsive
            test_messages = [{"role": "user", "content": "test"}]
            prediction = _endpoint.predict(instances=[{"messages": test_messages}])
            if prediction.predictions:
                checks["vertex_endpoint"] = True
    except Exception as e:
        logger.warning("Vertex endpoint readiness check failed", error=str(e))
    
    # Check Redis connection
    try:
        redis_client = _get_redis_client()
        if redis_client:
            redis_client.ping()
            checks["redis"] = True
        else:
            # Redis is optional, so mark as healthy if not configured
            checks["redis"] = True
    except Exception as e:
        logger.warning("Redis readiness check failed", error=str(e))
    
    # Overall readiness
    checks["overall"] = checks["vertex_endpoint"]  # Only require Vertex endpoint
    
    status_code = 200 if checks["overall"] else 503
    return checks, status_code


@app.get("/live")
async def liveness():
    """Liveness check - indicates if the service should be restarted."""
    # Basic liveness - if we can respond, we're alive
    return {"status": "alive", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


@app.get("/metrics")
async def metrics():
    """Get performance metrics from optimizer."""
    stats = optimizer.get_performance_stats()
    return {
        "optimizer_stats": stats,
        "caching_enabled": optimizer.enable_caching,
        "batching_enabled": optimizer.enable_batching
    }


@app.get("/optimizer/stats")
async def optimizer_stats():
    """Detailed optimizer statistics."""
    return optimizer.get_performance_stats()


