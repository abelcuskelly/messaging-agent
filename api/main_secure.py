"""
Secure FastAPI Application with OAuth2/JWT Authentication
Enhanced version of main.py with proper authentication
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from google.cloud import aiplatform
import os
import sys
import uuid
import time
import json
import structlog
from typing import Optional, Dict, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import redis

# Add auth module to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.jwt_auth import get_current_active_user, User, check_scopes, api_key_auth
from auth.auth_routes import router as auth_router
from log_handler import ConversationLogger

# Initialize structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Qwen Messaging Agent API",
    description="Secure API for sports ticketing chatbot with OAuth2/JWT authentication",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth_router)

# Initialize services
_endpoint = None
_redis_client: Optional[redis.Redis] = None
_conversation_logger: Optional[ConversationLogger] = None

# Conversation storage
conversations: Dict[str, List[Dict]] = {}

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str

class ErrorResponse(BaseModel):
    error: str
    detail: str
    request_id: str
    timestamp: str


def _get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client for caching and rate limiting."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True,
                socket_connect_timeout=5
            )
            _redis_client.ping()
            logger.info("Redis client initialized")
        except Exception as e:
            logger.warning("Redis connection failed", error=str(e))
            _redis_client = None
    return _redis_client


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


def _rate_limit_check(request: Request, user: User) -> None:
    """Check rate limits for authenticated user."""
    redis_client = _get_redis_client()
    if not redis_client:
        return  # Skip rate limiting if Redis unavailable
    
    # Rate limit by user
    key = f"rate_limit:user:{user.username}"
    
    try:
        current = redis_client.incr(key)
        if current == 1:
            redis_client.expire(key, 60)  # 1 minute window
        
        limit = 100 if "premium" in user.scopes else 50  # Different limits based on user tier
        
        if current > limit:
            logger.warning("Rate limit exceeded", username=user.username, count=current)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {limit} requests per minute."
            )
    except redis.RedisError as e:
        logger.error("Rate limit check failed", error=str(e))
        # Don't block on Redis errors


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


# Authentication dependencies
async def get_current_user_or_api_key(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> User:
    """Allow authentication via JWT token or API key."""
    
    # Try API key first (for service-to-service)
    if x_api_key:
        key_data = api_key_auth.validate_api_key(x_api_key)
        if key_data:
            # Create a service user from API key
            return User(
                username=f"service:{key_data.get('service')}",
                scopes=key_data.get("scopes", []),
                disabled=False
            )
    
    # Fall back to JWT authentication
    if authorization:
        from auth.jwt_auth import oauth2_scheme, get_current_user
        token = authorization.replace("Bearer ", "")
        return await get_current_user(token)
    
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide Bearer token or X-API-Key"
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user_or_api_key)
):
    """
    Chat endpoint with authentication.
    Requires either JWT token or API key.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Check if user has chat scope
    if "chat" not in current_user.scopes:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. 'chat' scope required."
        )
    
    try:
        # Rate limiting
        _rate_limit_check(http_request, current_user)
        
        # Get or create conversation
        conv_id = request.conversation_id or str(uuid.uuid4())
        if conv_id not in conversations:
            conversations[conv_id] = []
        
        # Add user message
        conversations[conv_id].append({
            "role": "user",
            "content": request.message
        })
        
        # Get response
        response_text = _predict_with_retry(conversations[conv_id])
        
        # Add assistant response
        conversations[conv_id].append({
            "role": "assistant",
            "content": response_text
        })
        
        # Keep conversation size manageable
        if len(conversations[conv_id]) > 20:
            conversations[conv_id] = conversations[conv_id][-20:]
        
        # Log success
        duration = time.time() - start_time
        duration_ms = int(duration * 1000)
        
        logger.info(
            "Chat request completed",
            request_id=request_id,
            username=current_user.username,
            conversation_id=conv_id,
            duration=duration,
            message_length=len(request.message),
            response_length=len(response_text)
        )
        
        # Log to BigQuery
        conversation_logger = _get_conversation_logger()
        if conversation_logger:
            conversation_logger.log_interaction(
                conversation_id=conv_id,
                user_message=request.message,
                agent_response=response_text,
                request_id=request_id,
                duration_ms=duration_ms,
                status="success",
                metadata={"username": current_user.username}
            )
        
        return ChatResponse(response=response_text, conversation_id=conv_id)
        
    except HTTPException:
        raise
    except Exception as exc:
        duration = time.time() - start_time
        duration_ms = int(duration * 1000)
        error_detail = str(exc)
        
        logger.error(
            "Chat request failed",
            request_id=request_id,
            username=current_user.username,
            error=error_detail,
            duration=duration
        )
        
        # Log error to BigQuery
        conversation_logger = _get_conversation_logger()
        if conversation_logger and request:
            conversation_logger.log_error(
                conversation_id=request.conversation_id or "unknown",
                user_message=request.message,
                error_detail=error_detail,
                request_id=request_id,
                duration_ms=duration_ms,
                metadata={"username": current_user.username}
            )
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Chat request failed",
                detail=error_detail,
                request_id=request_id,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            ).model_dump()
        )


@app.get("/conversations")
async def get_user_conversations(
    current_user: User = Depends(check_scopes(["chat", "view_history"]))
):
    """Get conversation history for authenticated user."""
    # In production, filter by user
    user_conversations = {}
    for conv_id, messages in conversations.items():
        # Simple filtering - in production, store user association
        user_conversations[conv_id] = {
            "message_count": len(messages),
            "last_message": messages[-1] if messages else None
        }
    
    return {"conversations": user_conversations}


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(check_scopes(["chat", "delete_history"]))
):
    """Delete a conversation."""
    if conversation_id in conversations:
        del conversations[conversation_id]
        logger.info("Conversation deleted", 
                   conversation_id=conversation_id,
                   username=current_user.username)
        return {"message": "Conversation deleted"}
    else:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )


@app.get("/health")
async def health():
    """Public health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/ready")
async def readiness(current_user: User = Depends(get_current_active_user)):
    """Protected readiness check."""
    checks = {
        "vertex_endpoint": False,
        "redis": False,
        "bigquery": False,
        "overall": False
    }
    
    # Check Vertex AI endpoint
    try:
        if _endpoint is not None:
            checks["vertex_endpoint"] = True
    except Exception as e:
        logger.warning("Vertex endpoint check failed", error=str(e))
    
    # Check Redis
    try:
        redis_client = _get_redis_client()
        if redis_client:
            redis_client.ping()
            checks["redis"] = True
    except Exception as e:
        logger.warning("Redis check failed", error=str(e))
    
    # Check BigQuery logger
    try:
        if _get_conversation_logger():
            checks["bigquery"] = True
    except Exception as e:
        logger.warning("BigQuery check failed", error=str(e))
    
    checks["overall"] = checks["vertex_endpoint"]
    status_code = 200 if checks["overall"] else 503
    
    return checks, status_code


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global _endpoint
    
    try:
        # Initialize Vertex AI endpoint
        project_id = os.getenv("PROJECT_ID")
        endpoint_id = os.getenv("ENDPOINT_ID")
        location = os.getenv("LOCATION", "us-central1")
        
        if project_id and endpoint_id:
            aiplatform.init(project=project_id, location=location)
            _endpoint = aiplatform.Endpoint(endpoint_id)
            logger.info("Vertex AI endpoint initialized", endpoint_id=endpoint_id)
        else:
            logger.warning("Vertex AI endpoint not configured")
        
        # Initialize Redis
        _get_redis_client()
        
        # Initialize BigQuery logger
        _get_conversation_logger()
        
        # Create default admin user (for testing - remove in production)
        from auth.jwt_auth import auth_manager, UserCreate
        try:
            admin_user = UserCreate(
                username="admin",
                email="admin@example.com",
                password=os.getenv("ADMIN_PASSWORD", secrets.token_urlsafe(16)),
                full_name="System Administrator"
            )
            user = auth_manager.create_user(admin_user)
            # Update scopes to include admin
            user_data = auth_manager.get_user("admin")
            if user_data:
                user_dict = user_data.dict()
                user_dict["scopes"] = ["chat", "view_dashboard", "view_history", "delete_history", "admin"]
                auth_manager.redis_client.set(
                    f"user:admin",
                    json.dumps(user_dict),
                    ex=86400 * 30
                )
            logger.info("Default admin user created")
            admin_password = os.getenv("ADMIN_PASSWORD", secrets.token_urlsafe(16))
            print(f"🔑 Admin password: {admin_password}")
            print("⚠️  Change this password immediately!")
        except:
            pass  # User already exists
        
    except Exception as e:
        logger.error("Startup initialization failed", error=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global _redis_client, _conversation_logger
    
    if _redis_client:
        _redis_client.close()
    
    logger.info("Application shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
