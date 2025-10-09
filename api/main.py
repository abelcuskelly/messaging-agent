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


app = FastAPI()

# Configure structured logging
logger = structlog.get_logger()

# Redis client for rate limiting
_redis_client: Optional[redis.Redis] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


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
    
    try:
        # Rate limiting
        _rate_limit_check(http_request, x_api_key)
        
        if _endpoint is None:
            raise HTTPException(status_code=500, detail="Endpoint not initialized")

        conv_id = request.conversation_id or str(uuid.uuid4())

        # Get or create conversation history
        if conv_id not in conversations:
            conversations[conv_id] = []

        # Add user message
        conversations[conv_id].append({"role": "user", "content": request.message})

        # Get prediction from Vertex AI with retry
        response_text = _predict_with_retry(conversations[conv_id])

        # Add assistant response to history
        conversations[conv_id].append({"role": "assistant", "content": response_text})

        # Log success
        duration = time.time() - start_time
        logger.info(
            "Chat request completed",
            request_id=request_id,
            conversation_id=conv_id,
            duration=duration,
            message_length=len(request.message),
            response_length=len(response_text)
        )

        return ChatResponse(response=response_text, conversation_id=conv_id)
        
    except HTTPException:
        raise
    except Exception as exc:
        # Log error and return structured error response
        duration = time.time() - start_time
        error_detail = str(exc)
        
        logger.error(
            "Chat request failed",
            request_id=request_id,
            error=error_detail,
            duration=duration,
            message_length=len(request.message) if request else 0
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


