"""
GraphQL API Schema
Flexible query interface for messaging agent data
"""

import strawberry
from typing import List, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


# MARK: - Types

@strawberry.type
class Message:
    """Chat message type."""
    role: str
    content: str
    timestamp: str


@strawberry.type
class Conversation:
    """Conversation type."""
    id: str
    user_id: str
    state: str
    intent: Optional[str]
    messages: List[Message]
    created_at: str
    updated_at: str
    message_count: int


@strawberry.type
class User:
    """User type."""
    username: str
    email: Optional[str]
    full_name: Optional[str]
    scopes: List[str]
    disabled: bool


@strawberry.type
class ChatResponse:
    """Chat response type."""
    response: str
    conversation_id: str
    trace_id: Optional[str]
    cached: bool
    duration_ms: Optional[float]


@strawberry.type
class Experiment:
    """A/B test experiment type."""
    name: str
    status: str
    variants: List[str]
    started_at: Optional[str]
    duration_days: int


@strawberry.type
class ExperimentResults:
    """A/B test results type."""
    experiment: str
    status: str
    winner: Optional[str]
    statistical_significance: bool
    variants: strawberry.scalars.JSON


@strawberry.type
class QualityScore:
    """Quality score type."""
    overall_score: float
    coherence_score: float
    relevance_score: float
    safety_score: float
    sentiment_score: float
    passed: bool
    issues: List[str]


@strawberry.type
class CircuitBreakerStatus:
    """Circuit breaker status type."""
    name: str
    state: str
    total_requests: int
    total_successes: int
    total_failures: int
    success_rate: float


@strawberry.type
class CacheStats:
    """Cache statistics type."""
    hits: int
    misses: int
    hit_rate: float
    total_requests: int


@strawberry.type
class SystemHealth:
    """System health type."""
    status: str
    version: str
    cache: bool
    telemetry: bool
    circuit_breakers: bool


# MARK: - Inputs

@strawberry.input
class ChatInput:
    """Chat input type."""
    message: str
    conversation_id: Optional[str] = None
    use_cache: bool = True


@strawberry.input
class LoginInput:
    """Login input type."""
    username: str
    password: str


@strawberry.input
class ExperimentInput:
    """Experiment creation input."""
    name: str
    variant_names: List[str]
    duration_days: int = 7


# MARK: - Query

@strawberry.type
class Query:
    """GraphQL Query root."""
    
    @strawberry.field
    def hello(self) -> str:
        """Simple hello query."""
        return "Hello from Qwen Messaging Agent GraphQL API!"
    
    @strawberry.field
    async def me(self, info: strawberry.Info) -> Optional[User]:
        """Get current authenticated user."""
        # In production, extract from context/auth
        return User(
            username="demo_user",
            email="demo@example.com",
            full_name="Demo User",
            scopes=["chat", "view_dashboard"],
            disabled=False
        )
    
    @strawberry.field
    async def conversation(self, id: str, info: strawberry.Info) -> Optional[Conversation]:
        """Get conversation by ID."""
        # Mock data - in production, query from database
        return Conversation(
            id=id,
            user_id="user_123",
            state="browsing",
            intent="browse_tickets",
            messages=[
                Message(role="user", content="Hello", timestamp=datetime.utcnow().isoformat()),
                Message(role="assistant", content="Hi! How can I help?", timestamp=datetime.utcnow().isoformat())
            ],
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            message_count=2
        )
    
    @strawberry.field
    async def conversations(
        self,
        user_id: Optional[str] = None,
        limit: int = 10,
        info: strawberry.Info = None
    ) -> List[Conversation]:
        """Get list of conversations."""
        # Mock data - in production, query from database
        return [
            Conversation(
                id=f"conv_{i}",
                user_id=user_id or "user_123",
                state="browsing",
                intent="browse_tickets",
                messages=[],
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                message_count=i * 2
            )
            for i in range(min(limit, 5))
        ]
    
    @strawberry.field
    async def experiments(self, info: strawberry.Info) -> List[Experiment]:
        """Get list of A/B test experiments."""
        # Mock data - in production, query from AB test manager
        return [
            Experiment(
                name="baseline-vs-finetuned",
                status="running",
                variants=["baseline", "finetuned"],
                started_at=datetime.utcnow().isoformat(),
                duration_days=7
            )
        ]
    
    @strawberry.field
    async def experiment_results(self, name: str, info: strawberry.Info) -> Optional[ExperimentResults]:
        """Get A/B test experiment results."""
        # Mock data - in production, query from AB test manager
        return ExperimentResults(
            experiment=name,
            status="running",
            winner=None,
            statistical_significance=False,
            variants={
                "baseline": {"requests": 50, "success_rate": 0.92},
                "finetuned": {"requests": 50, "success_rate": 0.95}
            }
        )
    
    @strawberry.field
    async def circuit_breakers(self, info: strawberry.Info) -> List[CircuitBreakerStatus]:
        """Get circuit breaker statuses."""
        # Mock data - in production, query from circuit breaker manager
        return [
            CircuitBreakerStatus(
                name="model_inference",
                state="closed",
                total_requests=100,
                total_successes=95,
                total_failures=5,
                success_rate=0.95
            ),
            CircuitBreakerStatus(
                name="cache_operations",
                state="closed",
                total_requests=200,
                total_successes=198,
                total_failures=2,
                success_rate=0.99
            )
        ]
    
    @strawberry.field
    async def cache_stats(self, info: strawberry.Info) -> CacheStats:
        """Get cache statistics."""
        # Mock data - in production, query from cache manager
        return CacheStats(
            hits=850,
            misses=150,
            hit_rate=0.85,
            total_requests=1000
        )
    
    @strawberry.field
    async def system_health(self, info: strawberry.Info) -> SystemHealth:
        """Get system health status."""
        return SystemHealth(
            status="healthy",
            version="4.0.0",
            cache=True,
            telemetry=True,
            circuit_breakers=True
        )


# MARK: - Mutation

@strawberry.type
class Mutation:
    """GraphQL Mutation root."""
    
    @strawberry.mutation
    async def send_message(self, input: ChatInput, info: strawberry.Info) -> ChatResponse:
        """Send a chat message."""
        # Mock response - in production, call actual chat endpoint
        import time
        start_time = time.time()
        
        response_text = f"Response to: {input.message}"
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info("GraphQL chat mutation", message=input.message[:50])
        
        return ChatResponse(
            response=response_text,
            conversation_id=input.conversation_id or "new_conv_id",
            trace_id="trace_123",
            cached=False,
            duration_ms=duration_ms
        )
    
    @strawberry.mutation
    async def login(self, input: LoginInput, info: strawberry.Info) -> str:
        """Login and get access token."""
        # Mock login - in production, call auth service
        logger.info("GraphQL login mutation", username=input.username)
        return "mock_access_token"
    
    @strawberry.mutation
    async def clear_conversation(self, conversation_id: str, info: strawberry.Info) -> bool:
        """Clear a conversation."""
        logger.info("GraphQL clear conversation", conversation_id=conversation_id)
        return True
    
    @strawberry.mutation
    async def reset_circuit_breaker(self, name: str, info: strawberry.Info) -> bool:
        """Reset a circuit breaker."""
        logger.info("GraphQL reset circuit breaker", name=name)
        return True


# MARK: - Subscription

@strawberry.type
class Subscription:
    """GraphQL Subscription root for real-time updates."""
    
    @strawberry.subscription
    async def message_updates(self, conversation_id: str) -> Message:
        """Subscribe to message updates for a conversation."""
        # Mock subscription - in production, use WebSocket or Redis pub/sub
        import asyncio
        
        while True:
            await asyncio.sleep(5)
            yield Message(
                role="assistant",
                content=f"Update for conversation {conversation_id}",
                timestamp=datetime.utcnow().isoformat()
            )
    
    @strawberry.subscription
    async def system_metrics(self) -> CacheStats:
        """Subscribe to system metrics updates."""
        import asyncio
        import random
        
        while True:
            await asyncio.sleep(10)
            yield CacheStats(
                hits=random.randint(800, 900),
                misses=random.randint(100, 200),
                hit_rate=random.uniform(0.8, 0.9),
                total_requests=1000
            )


# MARK: - Schema

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)
