"""
Redis Caching Layer for Performance Optimization
Implements multi-tier caching with TTL management and cache warming
"""

import os
import json
import hashlib
import pickle
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
import redis
from redis.sentinel import Sentinel
import structlog
from functools import wraps
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = structlog.get_logger()


class CacheConfig:
    """Cache configuration and TTL settings."""
    
    # TTL settings for different cache types (in seconds)
    TTL_SETTINGS = {
        "chat_response": 3600,        # 1 hour for chat responses
        "knowledge_base": 86400,      # 24 hours for KB queries
        "user_session": 1800,         # 30 minutes for session data
        "model_prediction": 7200,     # 2 hours for model predictions
        "api_response": 600,          # 10 minutes for API responses
        "embeddings": 604800,         # 7 days for embeddings
        "search_results": 3600,       # 1 hour for search results
        "conversation_summary": 7200, # 2 hours for summaries
    }
    
    # Cache key prefixes
    PREFIXES = {
        "chat": "chat:",
        "kb": "kb:",
        "session": "session:",
        "model": "model:",
        "api": "api:",
        "embed": "embed:",
        "search": "search:",
        "summary": "summary:",
    }


class RedisCache:
    """Advanced Redis caching with connection pooling and failover."""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
        use_sentinel: bool = False,
        sentinel_hosts: List[tuple] = None,
        max_connections: int = 50
    ):
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", 6379))
        self.db = db
        self.use_sentinel = use_sentinel
        
        # Initialize Redis connection
        if use_sentinel and sentinel_hosts:
            self._init_sentinel(sentinel_hosts)
        else:
            self._init_standalone(max_connections)
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "evictions": 0
        }
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    def _init_standalone(self, max_connections: int):
        """Initialize standalone Redis connection with pooling."""
        try:
            pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                max_connections=max_connections,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.client = redis.Redis(connection_pool=pool, decode_responses=False)
            self.client.ping()
            logger.info("Redis cache initialized", host=self.host, port=self.port)
        except Exception as e:
            logger.error("Redis initialization failed", error=str(e))
            raise
    
    def _init_sentinel(self, sentinel_hosts: List[tuple]):
        """Initialize Redis with Sentinel for high availability."""
        try:
            sentinel = Sentinel(sentinel_hosts)
            self.client = sentinel.master_for(
                'mymaster',
                socket_timeout=5,
                db=self.db
            )
            self.client.ping()
            logger.info("Redis Sentinel initialized", hosts=sentinel_hosts)
        except Exception as e:
            logger.error("Redis Sentinel initialization failed", error=str(e))
            raise
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments."""
        # Create a unique key from arguments
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.client.get(key)
            if value is not None:
                self.stats["hits"] += 1
                logger.debug("Cache hit", key=key)
                return pickle.loads(value)
            else:
                self.stats["misses"] += 1
                logger.debug("Cache miss", key=key)
                return None
        except Exception as e:
            self.stats["errors"] += 1
            logger.error("Cache get error", key=key, error=str(e))
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            serialized = pickle.dumps(value)
            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)
            logger.debug("Cache set", key=key, ttl=ttl)
            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error("Cache set error", key=key, error=str(e))
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            result = self.client.delete(key)
            if result:
                self.stats["evictions"] += 1
                logger.debug("Cache delete", key=key)
            return bool(result)
        except Exception as e:
            self.stats["errors"] += 1
            logger.error("Cache delete error", key=key, error=str(e))
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error("Cache exists error", key=key, error=str(e))
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key."""
        try:
            return bool(self.client.expire(key, ttl))
        except Exception as e:
            logger.error("Cache expire error", key=key, error=str(e))
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "total_requests": total
        }
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                self.stats["evictions"] += deleted
                logger.info("Cache pattern cleared", pattern=pattern, count=deleted)
                return deleted
            return 0
        except Exception as e:
            logger.error("Cache clear pattern error", pattern=pattern, error=str(e))
            return 0
    
    def flush_all(self) -> bool:
        """Flush entire cache (use with caution)."""
        try:
            self.client.flushdb()
            logger.warning("Cache flushed")
            return True
        except Exception as e:
            logger.error("Cache flush error", error=str(e))
            return False


class CacheManager:
    """High-level cache management with decorators and strategies."""
    
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache
        self.config = CacheConfig()
    
    def cached(
        self,
        prefix: str = "general:",
        ttl: int = 3600,
        key_func: Optional[Callable] = None
    ):
        """Decorator for caching function results."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self.cache._generate_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_value = self.cache.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.cache.set(cache_key, result, ttl)
                return result
            
            # Add async version
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self.cache._generate_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_value = self.cache.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function and cache result
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                self.cache.set(cache_key, result, ttl)
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
        return decorator
    
    def cache_chat_response(self, message: str, response: str, conversation_id: str = None):
        """Cache chat responses for similar queries."""
        # Create semantic key from message
        message_hash = hashlib.md5(message.lower().strip().encode()).hexdigest()[:16]
        key = f"{self.config.PREFIXES['chat']}{message_hash}"
        
        cache_data = {
            "response": response,
            "message": message,
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        ttl = self.config.TTL_SETTINGS["chat_response"]
        self.cache.set(key, cache_data, ttl)
        
        # Also cache by exact message for faster lookup
        exact_key = f"{self.config.PREFIXES['chat']}exact:{message_hash}"
        self.cache.set(exact_key, response, ttl // 2)
    
    def get_chat_response(self, message: str) -> Optional[str]:
        """Get cached chat response for similar query."""
        message_hash = hashlib.md5(message.lower().strip().encode()).hexdigest()[:16]
        
        # Try exact match first
        exact_key = f"{self.config.PREFIXES['chat']}exact:{message_hash}"
        exact_response = self.cache.get(exact_key)
        if exact_response:
            return exact_response
        
        # Try semantic match
        key = f"{self.config.PREFIXES['chat']}{message_hash}"
        cache_data = self.cache.get(key)
        if cache_data:
            return cache_data.get("response")
        
        return None
    
    def cache_knowledge_base_query(self, query: str, results: List[Dict]):
        """Cache knowledge base search results."""
        query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()[:16]
        key = f"{self.config.PREFIXES['kb']}{query_hash}"
        
        cache_data = {
            "query": query,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        ttl = self.config.TTL_SETTINGS["knowledge_base"]
        self.cache.set(key, cache_data, ttl)
    
    def get_knowledge_base_results(self, query: str) -> Optional[List[Dict]]:
        """Get cached knowledge base results."""
        query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()[:16]
        key = f"{self.config.PREFIXES['kb']}{query_hash}"
        
        cache_data = self.cache.get(key)
        if cache_data:
            return cache_data.get("results")
        
        return None
    
    def cache_embedding(self, text: str, embedding: List[float]):
        """Cache text embeddings."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        key = f"{self.config.PREFIXES['embed']}{text_hash}"
        
        ttl = self.config.TTL_SETTINGS["embeddings"]
        self.cache.set(key, embedding, ttl)
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        key = f"{self.config.PREFIXES['embed']}{text_hash}"
        
        return self.cache.get(key)
    
    def warm_cache(self, common_queries: List[str], fetch_func: Callable):
        """Pre-populate cache with common queries."""
        logger.info("Warming cache", query_count=len(common_queries))
        
        for query in common_queries:
            # Check if already cached
            if not self.get_chat_response(query):
                try:
                    # Fetch response
                    response = fetch_func(query)
                    # Cache it
                    self.cache_chat_response(query, response)
                except Exception as e:
                    logger.error("Cache warming failed", query=query, error=str(e))
        
        logger.info("Cache warming complete")
    
    def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a specific user."""
        pattern = f"*user:{user_id}*"
        deleted = self.cache.clear_pattern(pattern)
        logger.info("User cache invalidated", user_id=user_id, deleted=deleted)
        return deleted
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get comprehensive cache information."""
        info = {
            "stats": self.cache.get_stats(),
            "config": {
                "ttl_settings": self.config.TTL_SETTINGS,
                "prefixes": self.config.PREFIXES
            }
        }
        
        # Get Redis server info
        try:
            redis_info = self.cache.client.info()
            info["redis_info"] = {
                "version": redis_info.get("redis_version"),
                "used_memory": redis_info.get("used_memory_human"),
                "connected_clients": redis_info.get("connected_clients"),
                "uptime_days": redis_info.get("uptime_in_days")
            }
        except:
            pass
        
        return info


# Global cache instance
_cache_instance: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance."""
    global _cache_instance
    
    if _cache_instance is None:
        redis_cache = RedisCache()
        _cache_instance = CacheManager(redis_cache)
        logger.info("Cache manager initialized")
    
    return _cache_instance


# Example usage functions
@get_cache_manager().cached(prefix="expensive_computation:", ttl=7200)
def expensive_computation(x: int, y: int) -> int:
    """Example of cached expensive computation."""
    import time
    time.sleep(2)  # Simulate expensive operation
    return x * y * 1000


@get_cache_manager().cached(prefix="api_call:", ttl=600)
async def cached_api_call(endpoint: str, params: dict) -> dict:
    """Example of cached API call."""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint, params=params) as response:
            return await response.json()
