"""
Request Batching for Cost Optimization
Batch multiple requests to reduce API calls and costs
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import structlog
import uuid

logger = structlog.get_logger()


@dataclass
class BatchRequest:
    """Individual request in a batch."""
    request_id: str
    user_id: str
    message: str
    conversation_id: str
    timestamp: float = field(default_factory=time.time)
    priority: int = 0  # Higher = more priority
    
    # Response tracking
    response: Optional[str] = None
    completed: bool = False
    error: Optional[str] = None


@dataclass
class BatchResult:
    """Result of batch processing."""
    batch_id: str
    request_count: int
    successful: int
    failed: int
    total_duration_ms: float
    avg_duration_per_request_ms: float
    cost_saved_percentage: float


class RequestBatcher:
    """
    Batches requests for efficient processing.
    Reduces API calls and costs by processing multiple requests together.
    """
    
    def __init__(
        self,
        max_batch_size: int = 10,
        max_wait_time_ms: int = 100,
        min_batch_size: int = 2,
        enable_priority: bool = True
    ):
        """
        Initialize request batcher.
        
        Args:
            max_batch_size: Maximum requests per batch
            max_wait_time_ms: Maximum time to wait for batch to fill
            min_batch_size: Minimum requests before processing
            enable_priority: Enable priority-based batching
        """
        self.max_batch_size = max_batch_size
        self.max_wait_time_ms = max_wait_time_ms
        self.min_batch_size = min_batch_size
        self.enable_priority = enable_priority
        
        # Pending requests
        self.pending_requests: List[BatchRequest] = []
        self.request_futures: Dict[str, asyncio.Future] = {}
        
        # Statistics
        self.total_requests = 0
        self.total_batches = 0
        self.total_cost_saved = 0.0
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        # Background task
        self._batch_task = None
        self._running = False
        
        logger.info("Request batcher initialized",
                   max_batch_size=max_batch_size,
                   max_wait_time_ms=max_wait_time_ms)
    
    async def start(self):
        """Start the batch processing task."""
        if not self._running:
            self._running = True
            self._batch_task = asyncio.create_task(self._process_batches())
            logger.info("Batch processor started")
    
    async def stop(self):
        """Stop the batch processing task."""
        self._running = False
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
        logger.info("Batch processor stopped")
    
    async def add_request(
        self,
        user_id: str,
        message: str,
        conversation_id: str,
        priority: int = 0
    ) -> str:
        """
        Add request to batch queue.
        
        Returns:
            Response string when batch is processed
        """
        request = BatchRequest(
            request_id=str(uuid.uuid4()),
            user_id=user_id,
            message=message,
            conversation_id=conversation_id,
            priority=priority
        )
        
        # Create future for response
        future = asyncio.Future()
        
        async with self._lock:
            self.pending_requests.append(request)
            self.request_futures[request.request_id] = future
            self.total_requests += 1
            
            logger.debug("Request added to batch",
                        request_id=request.request_id,
                        pending_count=len(self.pending_requests))
        
        # Wait for response
        return await future
    
    async def _process_batches(self):
        """Background task to process batches."""
        while self._running:
            try:
                await asyncio.sleep(self.max_wait_time_ms / 1000)
                
                async with self._lock:
                    if len(self.pending_requests) >= self.min_batch_size:
                        await self._process_current_batch()
                    elif len(self.pending_requests) > 0:
                        # Check if oldest request exceeded wait time
                        oldest = min(self.pending_requests, key=lambda r: r.timestamp)
                        if (time.time() - oldest.timestamp) * 1000 >= self.max_wait_time_ms:
                            await self._process_current_batch()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Batch processing error", error=str(e))
    
    async def _process_current_batch(self):
        """Process current batch of requests."""
        if not self.pending_requests:
            return
        
        # Get batch
        batch_size = min(len(self.pending_requests), self.max_batch_size)
        
        # Sort by priority if enabled
        if self.enable_priority:
            self.pending_requests.sort(key=lambda r: r.priority, reverse=True)
        
        batch = self.pending_requests[:batch_size]
        self.pending_requests = self.pending_requests[batch_size:]
        
        batch_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info("Processing batch",
                   batch_id=batch_id,
                   size=len(batch))
        
        # Process batch (this is where you'd call your ML model)
        responses = await self._call_model_batch(batch)
        
        # Complete futures
        for request, response in zip(batch, responses):
            future = self.request_futures.pop(request.request_id, None)
            if future and not future.done():
                if response.get("error"):
                    future.set_exception(Exception(response["error"]))
                else:
                    future.set_result(response["response"])
        
        # Calculate metrics
        duration_ms = (time.time() - start_time) * 1000
        successful = sum(1 for r in responses if not r.get("error"))
        
        # Calculate cost savings
        # Single requests would take ~100ms each, batch takes duration_ms total
        single_request_time = 100 * len(batch)
        cost_saved = ((single_request_time - duration_ms) / single_request_time) * 100
        
        self.total_batches += 1
        self.total_cost_saved += cost_saved
        
        logger.info("Batch processed",
                   batch_id=batch_id,
                   size=len(batch),
                   successful=successful,
                   duration_ms=duration_ms,
                   cost_saved_pct=cost_saved)
        
        return BatchResult(
            batch_id=batch_id,
            request_count=len(batch),
            successful=successful,
            failed=len(batch) - successful,
            total_duration_ms=duration_ms,
            avg_duration_per_request_ms=duration_ms / len(batch),
            cost_saved_percentage=cost_saved
        )
    
    async def _call_model_batch(self, batch: List[BatchRequest]) -> List[Dict[str, Any]]:
        """
        Call ML model with batch of requests.
        In production, this would call your actual model endpoint.
        """
        # Simulate batch inference
        await asyncio.sleep(0.05 * len(batch))  # Simulated batch processing time
        
        responses = []
        for request in batch:
            # Simulate response generation
            responses.append({
                "request_id": request.request_id,
                "response": f"Batched response to: {request.message}",
                "error": None
            })
        
        return responses
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batching statistics."""
        avg_batch_size = self.total_requests / self.total_batches if self.total_batches > 0 else 0
        avg_cost_saved = self.total_cost_saved / self.total_batches if self.total_batches > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "total_batches": self.total_batches,
            "avg_batch_size": avg_batch_size,
            "pending_requests": len(self.pending_requests),
            "avg_cost_saved_pct": avg_cost_saved,
            "config": {
                "max_batch_size": self.max_batch_size,
                "max_wait_time_ms": self.max_wait_time_ms,
                "min_batch_size": self.min_batch_size
            }
        }


class AdaptiveBatcher:
    """
    Adaptive request batcher that adjusts batch size based on load.
    Optimizes for both latency and cost.
    """
    
    def __init__(self, base_batcher: RequestBatcher):
        self.batcher = base_batcher
        self.load_history: List[Tuple[float, int]] = []  # (timestamp, pending_count)
        self.max_history = 100
    
    async def add_request(
        self,
        user_id: str,
        message: str,
        conversation_id: str,
        priority: int = 0
    ) -> str:
        """Add request with adaptive batching."""
        # Track load
        self.load_history.append((time.time(), len(self.batcher.pending_requests)))
        if len(self.load_history) > self.max_history:
            self.load_history.pop(0)
        
        # Adjust batch parameters based on load
        self._adjust_batch_parameters()
        
        return await self.batcher.add_request(user_id, message, conversation_id, priority)
    
    def _adjust_batch_parameters(self):
        """Adjust batch size and wait time based on current load."""
        if len(self.load_history) < 10:
            return
        
        # Calculate recent load
        recent_load = [count for _, count in self.load_history[-10:]]
        avg_load = sum(recent_load) / len(recent_load)
        
        # Adjust batch size
        if avg_load > 20:
            # High load - increase batch size for efficiency
            self.batcher.max_batch_size = min(20, self.batcher.max_batch_size + 1)
            self.batcher.max_wait_time_ms = min(200, self.batcher.max_wait_time_ms + 10)
        elif avg_load < 5:
            # Low load - decrease batch size for latency
            self.batcher.max_batch_size = max(5, self.batcher.max_batch_size - 1)
            self.batcher.max_wait_time_ms = max(50, self.batcher.max_wait_time_ms - 10)
        
        logger.debug("Batch parameters adjusted",
                    avg_load=avg_load,
                    max_batch_size=self.batcher.max_batch_size,
                    max_wait_time_ms=self.batcher.max_wait_time_ms)


# Global batcher instance
_batcher: Optional[RequestBatcher] = None
_adaptive_batcher: Optional[AdaptiveBatcher] = None


async def get_request_batcher() -> RequestBatcher:
    """Get or create global request batcher."""
    global _batcher
    
    if _batcher is None:
        _batcher = RequestBatcher(
            max_batch_size=10,
            max_wait_time_ms=100,
            min_batch_size=2
        )
        await _batcher.start()
        logger.info("Request batcher initialized and started")
    
    return _batcher


async def get_adaptive_batcher() -> AdaptiveBatcher:
    """Get or create global adaptive batcher."""
    global _adaptive_batcher
    
    if _adaptive_batcher is None:
        batcher = await get_request_batcher()
        _adaptive_batcher = AdaptiveBatcher(batcher)
        logger.info("Adaptive batcher initialized")
    
    return _adaptive_batcher
