"""
Security headers middleware for FastAPI
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to all responses."""
    
    def __init__(self, app, strict_mode: bool = True):
        super().__init__(app)
        self.strict_mode = strict_mode
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        security_headers = {
            # Prevent XSS attacks
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            
            # HTTPS enforcement
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Content Security Policy
            "Content-Security-Policy": self._get_csp(),
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
        
        # Add headers to response
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    def _get_csp(self) -> str:
        """Get Content Security Policy header."""
        if self.strict_mode:
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'self'"
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limits."""
        client_ip = request.client.host
        
        # Simple in-memory rate limiting (use Redis in production)
        current_time = int(time.time() / 60)  # Minute-based buckets
        key = f"{client_ip}:{current_time}"
        
        if key not in self.request_counts:
            self.request_counts[key] = 0
        
        self.request_counts[key] += 1
        
        if self.request_counts[key] > self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
        
        # Clean old entries
        self._cleanup_old_entries(current_time)
        
        response = await call_next(request)
        return response
    
    def _cleanup_old_entries(self, current_time: int):
        """Remove old rate limit entries."""
        keys_to_remove = [
            key for key in self.request_counts.keys()
            if int(key.split(':')[1]) < current_time - 1
        ]
        for key in keys_to_remove:
            del self.request_counts[key]


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Limit request size to prevent DoS attacks."""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check request size."""
        content_length = request.headers.get("content-length")
        
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request too large"}
            )
        
        response = await call_next(request)
        return response


def add_security_middleware(app, strict_mode: bool = True):
    """Add all security middleware to FastAPI app."""
    
    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware, strict_mode=strict_mode)
    
    # Add rate limiting (if not using Redis-based rate limiting)
    if not os.getenv("REDIS_URL"):
        app.add_middleware(RateLimitMiddleware)
    
    # Add request size limiting
    app.add_middleware(RequestSizeMiddleware)
    
    return app
