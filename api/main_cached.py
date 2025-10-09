"""
FastAPI Application with Redis Caching Layer
Enhanced version with comprehensive caching for performance
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
import os
import sys
import uuid
import time
import hashlib
from typing import Optional, Dict, List
import structlog

# Add cache module to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cache.redis_cache import get_cache_manager, CacheManager
from auth.jwt_auth import get_current_active_user, User
from auth.auth_routes import router as auth_router

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Qwen Messaging Agent API with Caching",
    description="High-performance API with Redis caching layer",
    version="2.1.0"
)

# Include auth routes
app.include_router(auth_router)

# Initialize cache manager
cache_manager: CacheManager = get_cache_manager()

# Mock endpoint for demonstration (replace with actual Vertex AI)
class MockEndpoint:
    def predict(self, instances):
        # Simulate model prediction
        import time
        time.sleep(0.5)  # Simulate latency
        return type('obj', (object,), {
            'predictions': [{'response': f"This is a response to: {instances[0]['messages'][-1]['content']}"}]
        })()

_endpoint = MockEndpoint()

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    use_cache: bool = True  # Allow cache bypass

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    cached: bool = False
    cache_key: Optional[str] = None


@app.post("/chat", response_model=ChatResponse)
async def chat_with_cache(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Chat endpoint with intelligent caching.
    Caches responses for similar queries to improve performance.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    cached_response = False
    cache_key = None
    
    try:
        # Check cache first if enabled
        if request.use_cache:
            cached = cache_manager.get_chat_response(request.message)
            if cached:
                logger.info(
                    "Cache hit for chat",
                    request_id=request_id,
                    username=current_user.username,
                    duration_ms=int((time.time() - start_time) * 1000)
                )
                return ChatResponse(
                    response=cached,
                    conversation_id=request.conversation_id or str(uuid.uuid4()),
                    cached=True,
                    cache_key=hashlib.md5(request.message.lower().strip().encode()).hexdigest()[:16]
                )
        
        # Generate response (expensive operation)
        messages = [{"role": "user", "content": request.message}]
        prediction = _endpoint.predict(instances=[{"messages": messages}])
        response_text = prediction.predictions[0]["response"]
        
        # Cache the response
        cache_manager.cache_chat_response(
            message=request.message,
            response=response_text,
            conversation_id=request.conversation_id
        )
        
        cache_key = hashlib.md5(request.message.lower().strip().encode()).hexdigest()[:16]
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "Chat request completed",
            request_id=request_id,
            username=current_user.username,
            duration_ms=duration_ms,
            cached=False
        )
        
        return ChatResponse(
            response=response_text,
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            cached=False,
            cache_key=cache_key
        )
        
    except Exception as e:
        logger.error("Chat request failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge-base/search")
@cache_manager.cached(prefix="kb_search:", ttl=3600)
async def search_knowledge_base(
    query: str,
    top_k: int = 5,
    current_user: User = Depends(get_current_active_user)
):
    """
    Search knowledge base with caching.
    Results are cached for 1 hour.
    """
    # Check cache first
    cached_results = cache_manager.get_knowledge_base_results(query)
    if cached_results:
        logger.info("KB cache hit", query=query, username=current_user.username)
        return {"results": cached_results, "cached": True}
    
    # Simulate knowledge base search (expensive operation)
    import time
    time.sleep(1)  # Simulate search latency
    
    results = [
        {"id": f"doc_{i}", "content": f"Result {i} for query: {query}", "score": 0.9 - i*0.1}
        for i in range(min(top_k, 5))
    ]
    
    # Cache results
    cache_manager.cache_knowledge_base_query(query, results)
    
    logger.info("KB search completed", query=query, username=current_user.username)
    return {"results": results, "cached": False}


@app.post("/embeddings")
async def get_embeddings(
    text: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get text embeddings with caching.
    Embeddings are cached for 7 days.
    """
    # Check cache first
    cached_embedding = cache_manager.get_embedding(text)
    if cached_embedding:
        logger.info("Embedding cache hit", username=current_user.username)
        return {"embedding": cached_embedding, "cached": True}
    
    # Generate embedding (expensive operation)
    import time
    import random
    time.sleep(0.5)  # Simulate embedding generation
    
    # Mock embedding
    embedding = [random.random() for _ in range(768)]
    
    # Cache embedding
    cache_manager.cache_embedding(text, embedding)
    
    logger.info("Embedding generated", username=current_user.username)
    return {"embedding": embedding, "cached": False}


@app.post("/cache/warm")
async def warm_cache(
    queries: List[str],
    current_user: User = Depends(get_current_active_user)
):
    """
    Pre-populate cache with common queries.
    Admin only endpoint.
    """
    if "admin" not in current_user.scopes:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    def fetch_response(query):
        # Simulate fetching response
        return f"Warmed response for: {query}"
    
    cache_manager.warm_cache(queries, fetch_response)
    
    logger.info("Cache warmed", query_count=len(queries), username=current_user.username)
    return {"message": f"Cache warmed with {len(queries)} queries"}


@app.delete("/cache/user/{user_id}")
async def invalidate_user_cache(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Invalidate all cache entries for a specific user.
    Admin only endpoint.
    """
    if "admin" not in current_user.scopes:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    deleted = cache_manager.invalidate_user_cache(user_id)
    
    logger.info("User cache invalidated", user_id=user_id, deleted=deleted)
    return {"message": f"Invalidated {deleted} cache entries for user {user_id}"}


@app.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get cache statistics and information.
    """
    if "admin" not in current_user.scopes and "view_dashboard" not in current_user.scopes:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    cache_info = cache_manager.get_cache_info()
    
    return cache_info


@app.delete("/cache/pattern")
async def clear_cache_pattern(
    pattern: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Clear cache entries matching pattern.
    Admin only endpoint.
    """
    if "admin" not in current_user.scopes:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    deleted = cache_manager.cache.clear_pattern(pattern)
    
    logger.warning("Cache pattern cleared", pattern=pattern, deleted=deleted, username=current_user.username)
    return {"message": f"Deleted {deleted} cache entries matching pattern: {pattern}"}


@app.post("/cache/flush")
async def flush_cache(
    confirm: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """
    Flush entire cache (use with extreme caution).
    Admin only endpoint.
    """
    if "admin" not in current_user.scopes:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Set confirm=true to flush entire cache"
        )
    
    success = cache_manager.cache.flush_all()
    
    if success:
        logger.warning("Cache flushed", username=current_user.username)
        return {"message": "Cache flushed successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to flush cache")


# Cached computation example
@app.get("/compute")
@cache_manager.cached(prefix="computation:", ttl=7200)
async def cached_computation(
    x: int,
    y: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Example of cached expensive computation.
    Results cached for 2 hours.
    """
    import time
    time.sleep(2)  # Simulate expensive computation
    
    result = x * y * 1000
    
    logger.info("Computation completed", x=x, y=y, result=result)
    return {"result": result, "cached": False}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.1.0"}


@app.get("/ready")
async def readiness():
    """Readiness check including cache."""
    checks = {
        "cache": False,
        "overall": False
    }
    
    try:
        # Check Redis cache
        cache_manager.cache.client.ping()
        checks["cache"] = True
    except Exception as e:
        logger.warning("Cache check failed", error=str(e))
    
    checks["overall"] = checks["cache"]
    status_code = 200 if checks["overall"] else 503
    
    return checks, status_code


@app.on_event("startup")
async def startup_event():
    """Initialize services and warm cache on startup."""
    logger.info("Application starting with cache layer")
    
    # Warm cache with common queries
    common_queries = [
        "What are the ticket prices?",
        "What's the refund policy?",
        "Where do the Lakers play?",
        "How do I upgrade my seat?",
        "What time do games start?"
    ]
    
    def mock_fetch(query):
        return f"Cached response for: {query}"
    
    try:
        cache_manager.warm_cache(common_queries, mock_fetch)
        logger.info("Cache warmed on startup")
    except Exception as e:
        logger.error("Cache warming failed", error=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    # Log cache statistics
    stats = cache_manager.cache.get_stats()
    logger.info("Cache statistics at shutdown", **stats)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
