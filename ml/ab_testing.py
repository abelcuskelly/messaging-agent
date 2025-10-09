"""
Model A/B Testing Framework
Compare multiple models and track performance metrics
"""

import os
import json
import random
import hashlib
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import structlog
from dataclasses import dataclass, asdict
from collections import defaultdict
import redis

logger = structlog.get_logger()


class ExperimentStatus(Enum):
    """A/B test experiment status."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class ModelVariant:
    """Model variant configuration."""
    name: str
    model_id: str
    endpoint_id: str
    weight: float  # Traffic allocation (0.0 to 1.0)
    description: str = ""
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


@dataclass
class ExperimentMetrics:
    """Metrics for an A/B test experiment."""
    variant_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    success_rate: float = 0.0
    user_satisfaction: float = 0.0
    conversion_rate: float = 0.0
    
    def update(self, success: bool, latency_ms: float, satisfaction: Optional[float] = None):
        """Update metrics with new request data."""
        self.total_requests += 1
        self.total_latency_ms += latency_ms
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        self.avg_latency_ms = self.total_latency_ms / self.total_requests
        self.success_rate = self.successful_requests / self.total_requests
        
        if satisfaction is not None:
            # Running average for satisfaction
            self.user_satisfaction = (
                (self.user_satisfaction * (self.total_requests - 1) + satisfaction) 
                / self.total_requests
            )


class ABTestExperiment:
    """A/B test experiment for model comparison."""
    
    def __init__(
        self,
        name: str,
        variants: List[ModelVariant],
        redis_client: Optional[redis.Redis] = None,
        duration_days: int = 7,
        min_sample_size: int = 100
    ):
        """
        Initialize A/B test experiment.
        
        Args:
            name: Experiment identifier
            variants: List of model variants to test
            redis_client: Redis client for storing metrics
            duration_days: Experiment duration
            min_sample_size: Minimum samples before statistical significance
        """
        self.name = name
        self.variants = {v.name: v for v in variants}
        self.redis_client = redis_client
        self.duration_days = duration_days
        self.min_sample_size = min_sample_size
        
        # Validate weights sum to 1.0
        total_weight = sum(v.weight for v in variants)
        if not 0.99 <= total_weight <= 1.01:
            raise ValueError(f"Variant weights must sum to 1.0, got {total_weight}")
        
        # State
        self.status = ExperimentStatus.DRAFT
        self.started_at = None
        self.ended_at = None
        
        # Metrics
        self.metrics: Dict[str, ExperimentMetrics] = {
            v.name: ExperimentMetrics(variant_name=v.name)
            for v in variants
        }
        
        # User assignments (for consistency)
        self.user_assignments: Dict[str, str] = {}
        
        logger.info("A/B test experiment created",
                   name=name,
                   variants=[v.name for v in variants])
    
    def start(self):
        """Start the experiment."""
        self.status = ExperimentStatus.RUNNING
        self.started_at = datetime.utcnow()
        logger.info("A/B test started", name=self.name)
    
    def pause(self):
        """Pause the experiment."""
        self.status = ExperimentStatus.PAUSED
        logger.info("A/B test paused", name=self.name)
    
    def complete(self):
        """Complete the experiment."""
        self.status = ExperimentStatus.COMPLETED
        self.ended_at = datetime.utcnow()
        logger.info("A/B test completed", name=self.name)
    
    def assign_variant(self, user_id: str) -> ModelVariant:
        """
        Assign user to a variant.
        Uses consistent hashing to ensure same user always gets same variant.
        """
        # Check if user already assigned
        if user_id in self.user_assignments:
            variant_name = self.user_assignments[user_id]
            return self.variants[variant_name]
        
        # Assign based on hash and weights
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        random.seed(user_hash)
        
        # Weighted random selection
        rand_val = random.random()
        cumulative_weight = 0.0
        
        for variant in self.variants.values():
            cumulative_weight += variant.weight
            if rand_val <= cumulative_weight:
                self.user_assignments[user_id] = variant.name
                logger.debug("User assigned to variant",
                           user_id=user_id,
                           variant=variant.name)
                return variant
        
        # Fallback to first variant
        first_variant = list(self.variants.values())[0]
        self.user_assignments[user_id] = first_variant.name
        return first_variant
    
    def record_request(
        self,
        variant_name: str,
        success: bool,
        latency_ms: float,
        satisfaction: Optional[float] = None
    ):
        """Record request metrics for a variant."""
        if variant_name not in self.metrics:
            logger.error("Unknown variant", variant=variant_name)
            return
        
        self.metrics[variant_name].update(success, latency_ms, satisfaction)
        
        # Store in Redis if available
        if self.redis_client:
            key = f"ab_test:{self.name}:{variant_name}"
            self.redis_client.set(
                key,
                json.dumps(asdict(self.metrics[variant_name])),
                ex=86400 * 30  # 30 days
            )
    
    def get_results(self) -> Dict[str, Any]:
        """Get experiment results with statistical analysis."""
        results = {
            "experiment": self.name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_days": self.duration_days,
            "variants": {},
            "winner": None,
            "statistical_significance": False
        }
        
        # Collect metrics for each variant
        for variant_name, metrics in self.metrics.items():
            results["variants"][variant_name] = {
                "metrics": asdict(metrics),
                "variant_config": asdict(self.variants[variant_name])
            }
        
        # Determine winner if enough samples
        if all(m.total_requests >= self.min_sample_size for m in self.metrics.values()):
            results["statistical_significance"] = True
            
            # Find best variant (highest success rate * user satisfaction / latency)
            best_score = 0
            best_variant = None
            
            for variant_name, metrics in self.metrics.items():
                if metrics.total_requests == 0:
                    continue
                
                # Composite score
                score = (
                    metrics.success_rate * 0.4 +
                    metrics.user_satisfaction * 0.3 +
                    (1 - min(metrics.avg_latency_ms / 5000, 1.0)) * 0.3
                )
                
                if score > best_score:
                    best_score = score
                    best_variant = variant_name
            
            results["winner"] = best_variant
            results["winner_score"] = best_score
        
        return results
    
    def get_variant_comparison(self) -> Dict[str, Any]:
        """Get side-by-side variant comparison."""
        comparison = {
            "experiment": self.name,
            "variants": []
        }
        
        for variant_name, metrics in self.metrics.items():
            comparison["variants"].append({
                "name": variant_name,
                "requests": metrics.total_requests,
                "success_rate": f"{metrics.success_rate:.1%}",
                "avg_latency": f"{metrics.avg_latency_ms:.0f}ms",
                "satisfaction": f"{metrics.user_satisfaction:.2f}",
                "weight": self.variants[variant_name].weight
            })
        
        return comparison


class ABTestManager:
    """Manages multiple A/B test experiments."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
        self.experiments: Dict[str, ABTestExperiment] = {}
    
    def create_experiment(
        self,
        name: str,
        variants: List[ModelVariant],
        duration_days: int = 7,
        min_sample_size: int = 100
    ) -> ABTestExperiment:
        """Create a new A/B test experiment."""
        if name in self.experiments:
            raise ValueError(f"Experiment '{name}' already exists")
        
        experiment = ABTestExperiment(
            name=name,
            variants=variants,
            redis_client=self.redis_client,
            duration_days=duration_days,
            min_sample_size=min_sample_size
        )
        
        self.experiments[name] = experiment
        logger.info("A/B test experiment created", name=name)
        
        return experiment
    
    def get_experiment(self, name: str) -> Optional[ABTestExperiment]:
        """Get experiment by name."""
        return self.experiments.get(name)
    
    def list_experiments(self) -> List[Dict[str, Any]]:
        """List all experiments."""
        return [
            {
                "name": exp.name,
                "status": exp.status.value,
                "variants": [v.name for v in exp.variants.values()],
                "started_at": exp.started_at.isoformat() if exp.started_at else None
            }
            for exp in self.experiments.values()
        ]
    
    def get_variant_for_user(self, experiment_name: str, user_id: str) -> Optional[ModelVariant]:
        """Get assigned variant for user."""
        experiment = self.get_experiment(experiment_name)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return None
        
        return experiment.assign_variant(user_id)


# Global A/B test manager
_ab_test_manager: Optional[ABTestManager] = None


def get_ab_test_manager() -> ABTestManager:
    """Get or create global A/B test manager."""
    global _ab_test_manager
    
    if _ab_test_manager is None:
        _ab_test_manager = ABTestManager()
        logger.info("A/B test manager initialized")
    
    return _ab_test_manager


def create_sample_experiment():
    """Create a sample A/B test experiment."""
    manager = get_ab_test_manager()
    
    # Define variants
    variants = [
        ModelVariant(
            name="qwen-4b-baseline",
            model_id="Qwen/Qwen3-4B-Instruct-2507",
            endpoint_id="baseline-endpoint-id",
            weight=0.5,
            description="Baseline Qwen 4B model"
        ),
        ModelVariant(
            name="qwen-4b-finetuned",
            model_id="Qwen/Qwen3-4B-Instruct-2507-finetuned",
            endpoint_id="finetuned-endpoint-id",
            weight=0.5,
            description="Fine-tuned Qwen 4B model with LoRA"
        )
    ]
    
    # Create experiment
    experiment = manager.create_experiment(
        name="qwen-baseline-vs-finetuned",
        variants=variants,
        duration_days=7,
        min_sample_size=100
    )
    
    experiment.start()
    
    logger.info("Sample A/B test created and started")
    return experiment
