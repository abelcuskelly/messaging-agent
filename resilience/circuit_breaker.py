"""
Circuit Breaker Pattern Implementation
Prevents cascading failures and enables graceful degradation
"""

import time
import threading
from enum import Enum
from typing import Callable, Optional, Any, Dict
from functools import wraps
from datetime import datetime, timedelta
import structlog
from collections import deque

logger = structlog.get_logger()


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation with configurable thresholds.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests rejected immediately
    - HALF_OPEN: Testing recovery, limited requests allowed
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        success_threshold: int = 2,
        timeout: Optional[float] = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker identifier
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type to catch
            success_threshold: Successes needed in half-open to close
            timeout: Request timeout in seconds
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        self.timeout = timeout
        
        # State management
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._opened_at = None
        
        # Statistics
        self._total_requests = 0
        self._total_failures = 0
        self._total_successes = 0
        self._total_timeouts = 0
        self._total_rejections = 0
        
        # Recent failures for monitoring
        self._recent_failures = deque(maxlen=100)
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.info("Circuit breaker initialized",
                   name=name,
                   failure_threshold=failure_threshold,
                   recovery_timeout=recovery_timeout)
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            self._check_and_update_state()
            return self._state
    
    def _check_and_update_state(self):
        """Check if state should transition."""
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._opened_at is None:
            return False
        
        elapsed = time.time() - self._opened_at
        return elapsed >= self.recovery_timeout
    
    def _transition_to_half_open(self):
        """Transition from OPEN to HALF_OPEN."""
        self._state = CircuitState.HALF_OPEN
        self._success_count = 0
        logger.info("Circuit breaker transitioning to half-open",
                   name=self.name)
    
    def _transition_to_open(self):
        """Transition to OPEN state."""
        self._state = CircuitState.OPEN
        self._opened_at = time.time()
        self._failure_count = 0
        logger.warning("Circuit breaker opened",
                      name=self.name,
                      total_failures=self._total_failures)
    
    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at = None
        logger.info("Circuit breaker closed",
                   name=self.name)
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
        """
        with self._lock:
            self._total_requests += 1
            current_state = self.state
            
            # Reject if circuit is open
            if current_state == CircuitState.OPEN:
                self._total_rejections += 1
                logger.warning("Request rejected - circuit open",
                             name=self.name,
                             state=current_state.value)
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN"
                )
            
            # Allow limited requests in half-open
            if current_state == CircuitState.HALF_OPEN:
                logger.debug("Request allowed in half-open state",
                           name=self.name)
        
        # Execute function
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Check timeout
            if self.timeout and duration > self.timeout:
                self._on_timeout(duration)
                raise TimeoutError(
                    f"Request exceeded timeout: {duration:.2f}s > {self.timeout}s"
                )
            
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure(e)
            raise
    
    def _on_success(self):
        """Handle successful request."""
        with self._lock:
            self._total_successes += 1
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                
                if self._success_count >= self.success_threshold:
                    self._transition_to_closed()
            
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0
    
    def _on_failure(self, exception: Exception):
        """Handle failed request."""
        with self._lock:
            self._total_failures += 1
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            # Record failure details
            self._recent_failures.append({
                "timestamp": datetime.utcnow().isoformat(),
                "exception": str(exception),
                "type": type(exception).__name__
            })
            
            logger.warning("Circuit breaker failure recorded",
                         name=self.name,
                         failure_count=self._failure_count,
                         exception=str(exception))
            
            # Transition based on state
            if self._state == CircuitState.HALF_OPEN:
                # Immediate open on failure in half-open
                self._transition_to_open()
            
            elif self._state == CircuitState.CLOSED:
                # Open if threshold exceeded
                if self._failure_count >= self.failure_threshold:
                    self._transition_to_open()
    
    def _on_timeout(self, duration: float):
        """Handle timeout."""
        with self._lock:
            self._total_timeouts += 1
            logger.warning("Request timeout",
                         name=self.name,
                         duration=duration,
                         timeout=self.timeout)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "total_requests": self._total_requests,
                "total_successes": self._total_successes,
                "total_failures": self._total_failures,
                "total_timeouts": self._total_timeouts,
                "total_rejections": self._total_rejections,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "success_rate": (
                    self._total_successes / self._total_requests
                    if self._total_requests > 0 else 0
                ),
                "opened_at": (
                    datetime.fromtimestamp(self._opened_at).isoformat()
                    if self._opened_at else None
                ),
                "last_failure": (
                    datetime.fromtimestamp(self._last_failure_time).isoformat()
                    if self._last_failure_time else None
                ),
                "recent_failures": list(self._recent_failures)[-10:]  # Last 10
            }
    
    def reset(self):
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._transition_to_closed()
            logger.info("Circuit breaker manually reset", name=self.name)
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator usage."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # For async functions, wrap the call
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self.call, func, *args, **kwargs
            )
        
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper


class CircuitBreakerManager:
    """Manages multiple circuit breakers."""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
    
    def register(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        success_threshold: int = 2,
        timeout: Optional[float] = None
    ) -> CircuitBreaker:
        """Register a new circuit breaker."""
        with self._lock:
            if name in self.breakers:
                logger.warning("Circuit breaker already exists", name=name)
                return self.breakers[name]
            
            breaker = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception,
                success_threshold=success_threshold,
                timeout=timeout
            )
            
            self.breakers[name] = breaker
            logger.info("Circuit breaker registered", name=name)
            return breaker
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self.breakers.get(name)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        with self._lock:
            return {
                name: breaker.get_stats()
                for name, breaker in self.breakers.items()
            }
    
    def reset_all(self):
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self.breakers.values():
                breaker.reset()
            logger.info("All circuit breakers reset")


# Global circuit breaker manager
_manager = CircuitBreakerManager()


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager."""
    return _manager


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception,
    success_threshold: int = 2,
    timeout: Optional[float] = None
):
    """
    Decorator for circuit breaker protection.
    
    Usage:
        @circuit_breaker("external_api", failure_threshold=3, recovery_timeout=30)
        def call_external_api():
            return requests.get("https://api.example.com")
    """
    manager = get_circuit_breaker_manager()
    breaker = manager.register(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=expected_exception,
        success_threshold=success_threshold,
        timeout=timeout
    )
    
    return breaker
