"""
Model Ensemble Implementation
Combine multiple models for improved accuracy and reliability
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import structlog
import numpy as np

logger = structlog.get_logger()


class EnsembleStrategy(Enum):
    """Ensemble aggregation strategies."""
    VOTING = "voting"              # Majority vote
    WEIGHTED = "weighted"          # Weighted average
    CONFIDENCE = "confidence"      # Use most confident prediction
    FALLBACK = "fallback"          # Try models in order until success
    BEST_OF_N = "best_of_n"       # Select best from N models


@dataclass
class ModelConfig:
    """Configuration for a model in the ensemble."""
    name: str
    endpoint_id: str
    weight: float = 1.0
    priority: int = 0  # For fallback strategy
    timeout: float = 5.0
    enabled: bool = True


@dataclass
class PredictionResult:
    """Result from a single model prediction."""
    model_name: str
    response: str
    confidence: float
    latency_ms: float
    success: bool
    error: Optional[str] = None


class ModelEnsemble:
    """
    Ensemble of multiple models for improved predictions.
    Supports various aggregation strategies.
    """
    
    def __init__(
        self,
        models: List[ModelConfig],
        strategy: EnsembleStrategy = EnsembleStrategy.WEIGHTED,
        min_models: int = 2,
        max_latency_ms: float = 5000
    ):
        """
        Initialize model ensemble.
        
        Args:
            models: List of model configurations
            strategy: Aggregation strategy
            min_models: Minimum models that must succeed
            max_latency_ms: Maximum acceptable latency
        """
        self.models = {m.name: m for m in models}
        self.strategy = strategy
        self.min_models = min_models
        self.max_latency_ms = max_latency_ms
        
        # Statistics
        self.total_predictions = 0
        self.model_stats = {m.name: {"calls": 0, "successes": 0, "failures": 0} for m in models}
        
        logger.info("Model ensemble initialized",
                   models=[m.name for m in models],
                   strategy=strategy.value)
    
    async def predict(self, messages: List[Dict[str, str]]) -> str:
        """
        Make prediction using ensemble.
        
        Args:
            messages: Conversation messages
            
        Returns:
            Aggregated response string
        """
        self.total_predictions += 1
        start_time = time.time()
        
        # Get enabled models
        enabled_models = [m for m in self.models.values() if m.enabled]
        
        if not enabled_models:
            raise ValueError("No enabled models in ensemble")
        
        # Execute predictions based on strategy
        if self.strategy == EnsembleStrategy.FALLBACK:
            result = await self._predict_fallback(messages, enabled_models)
        else:
            result = await self._predict_parallel(messages, enabled_models)
        
        total_latency = (time.time() - start_time) * 1000
        
        logger.info("Ensemble prediction completed",
                   strategy=self.strategy.value,
                   latency_ms=total_latency,
                   models_used=len(result))
        
        return self._aggregate_results(result)
    
    async def _predict_parallel(
        self,
        messages: List[Dict[str, str]],
        models: List[ModelConfig]
    ) -> List[PredictionResult]:
        """Execute predictions in parallel."""
        tasks = [
            self._call_model(model, messages)
            for model in models
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = [
            r for r in results
            if isinstance(r, PredictionResult) and r.success
        ]
        
        if len(successful_results) < self.min_models:
            raise ValueError(f"Only {len(successful_results)} models succeeded, need {self.min_models}")
        
        return successful_results
    
    async def _predict_fallback(
        self,
        messages: List[Dict[str, str]],
        models: List[ModelConfig]
    ) -> List[PredictionResult]:
        """Execute predictions with fallback strategy."""
        # Sort by priority
        sorted_models = sorted(models, key=lambda m: m.priority, reverse=True)
        
        for model in sorted_models:
            try:
                result = await self._call_model(model, messages)
                if result.success:
                    return [result]
            except Exception as e:
                logger.warning("Model failed, trying next",
                             model=model.name,
                             error=str(e))
                continue
        
        raise ValueError("All models in fallback chain failed")
    
    async def _call_model(
        self,
        model: ModelConfig,
        messages: List[Dict[str, str]]
    ) -> PredictionResult:
        """Call a single model."""
        start_time = time.time()
        
        try:
            # Simulate model call (in production, call actual endpoint)
            await asyncio.sleep(0.1)  # Simulate latency
            
            # Mock response
            response = f"Response from {model.name}: {messages[-1]['content']}"
            confidence = 0.85 + (hash(model.name) % 15) / 100  # Mock confidence
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Update stats
            self.model_stats[model.name]["calls"] += 1
            self.model_stats[model.name]["successes"] += 1
            
            return PredictionResult(
                model_name=model.name,
                response=response,
                confidence=confidence,
                latency_ms=latency_ms,
                success=True
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            # Update stats
            self.model_stats[model.name]["calls"] += 1
            self.model_stats[model.name]["failures"] += 1
            
            logger.error("Model prediction failed",
                        model=model.name,
                        error=str(e))
            
            return PredictionResult(
                model_name=model.name,
                response="",
                confidence=0.0,
                latency_ms=latency_ms,
                success=False,
                error=str(e)
            )
    
    def _aggregate_results(self, results: List[PredictionResult]) -> str:
        """Aggregate results based on strategy."""
        
        if self.strategy == EnsembleStrategy.VOTING:
            return self._voting_aggregation(results)
        
        elif self.strategy == EnsembleStrategy.WEIGHTED:
            return self._weighted_aggregation(results)
        
        elif self.strategy == EnsembleStrategy.CONFIDENCE:
            return self._confidence_aggregation(results)
        
        elif self.strategy == EnsembleStrategy.FALLBACK:
            # Fallback returns first successful result
            return results[0].response if results else ""
        
        elif self.strategy == EnsembleStrategy.BEST_OF_N:
            return self._best_of_n_aggregation(results)
        
        else:
            # Default to first result
            return results[0].response if results else ""
    
    def _voting_aggregation(self, results: List[PredictionResult]) -> str:
        """Majority voting aggregation."""
        # Count occurrences of each response
        response_counts = {}
        for result in results:
            response_counts[result.response] = response_counts.get(result.response, 0) + 1
        
        # Return most common response
        if response_counts:
            return max(response_counts.items(), key=lambda x: x[1])[0]
        return ""
    
    def _weighted_aggregation(self, results: List[PredictionResult]) -> str:
        """Weighted aggregation based on model weights and confidence."""
        # Calculate weighted scores
        weighted_responses = {}
        
        for result in results:
            model = self.models[result.model_name]
            weight = model.weight * result.confidence
            
            if result.response in weighted_responses:
                weighted_responses[result.response] += weight
            else:
                weighted_responses[result.response] = weight
        
        # Return highest weighted response
        if weighted_responses:
            return max(weighted_responses.items(), key=lambda x: x[1])[0]
        return ""
    
    def _confidence_aggregation(self, results: List[PredictionResult]) -> str:
        """Select response with highest confidence."""
        if not results:
            return ""
        
        best_result = max(results, key=lambda r: r.confidence)
        return best_result.response
    
    def _best_of_n_aggregation(self, results: List[PredictionResult]) -> str:
        """Select best response based on composite score."""
        if not results:
            return ""
        
        # Calculate composite score (confidence * 0.7 + speed * 0.3)
        scored_results = []
        max_latency = max(r.latency_ms for r in results)
        
        for result in results:
            speed_score = 1.0 - (result.latency_ms / max_latency) if max_latency > 0 else 1.0
            composite_score = result.confidence * 0.7 + speed_score * 0.3
            scored_results.append((composite_score, result))
        
        best_result = max(scored_results, key=lambda x: x[0])[1]
        return best_result.response
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ensemble statistics."""
        return {
            "total_predictions": self.total_predictions,
            "strategy": self.strategy.value,
            "models": self.model_stats,
            "enabled_models": [name for name, model in self.models.items() if model.enabled],
            "config": {
                "min_models": self.min_models,
                "max_latency_ms": self.max_latency_ms
            }
        }
    
    def enable_model(self, model_name: str):
        """Enable a model in the ensemble."""
        if model_name in self.models:
            self.models[model_name].enabled = True
            logger.info("Model enabled", model=model_name)
    
    def disable_model(self, model_name: str):
        """Disable a model in the ensemble."""
        if model_name in self.models:
            self.models[model_name].enabled = False
            logger.info("Model disabled", model=model_name)


class AdaptiveEnsemble(ModelEnsemble):
    """
    Adaptive ensemble that adjusts model selection based on performance.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performance_window = 100  # Track last N predictions
        self.performance_history = []
    
    async def predict(self, messages: List[Dict[str, str]]) -> str:
        """Predict with adaptive model selection."""
        # Adjust model weights based on recent performance
        self._adjust_weights()
        
        # Make prediction
        response = await super().predict(messages)
        
        # Track performance
        self._track_performance()
        
        return response
    
    def _adjust_weights(self):
        """Adjust model weights based on recent performance."""
        for model_name, stats in self.model_stats.items():
            if stats["calls"] > 0:
                success_rate = stats["successes"] / stats["calls"]
                
                # Increase weight for high-performing models
                if success_rate > 0.95:
                    self.models[model_name].weight = min(2.0, self.models[model_name].weight * 1.1)
                elif success_rate < 0.80:
                    self.models[model_name].weight = max(0.5, self.models[model_name].weight * 0.9)
        
        # Normalize weights
        total_weight = sum(m.weight for m in self.models.values())
        for model in self.models.values():
            model.weight /= total_weight
    
    def _track_performance(self):
        """Track performance history."""
        self.performance_history.append({
            "timestamp": time.time(),
            "stats": dict(self.model_stats)
        })
        
        # Keep only recent history
        if len(self.performance_history) > self.performance_window:
            self.performance_history.pop(0)


# Global ensemble instance
_ensemble: Optional[ModelEnsemble] = None


def get_model_ensemble() -> ModelEnsemble:
    """Get or create global model ensemble."""
    global _ensemble
    
    if _ensemble is None:
        # Create default ensemble
        models = [
            ModelConfig(
                name="qwen-4b-primary",
                endpoint_id="primary-endpoint",
                weight=0.5,
                priority=1
            ),
            ModelConfig(
                name="qwen-4b-backup",
                endpoint_id="backup-endpoint",
                weight=0.3,
                priority=2
            ),
            ModelConfig(
                name="qwen-4b-experimental",
                endpoint_id="experimental-endpoint",
                weight=0.2,
                priority=3
            )
        ]
        
        _ensemble = ModelEnsemble(
            models=models,
            strategy=EnsembleStrategy.WEIGHTED,
            min_models=2
        )
        
        logger.info("Model ensemble initialized")
    
    return _ensemble


def create_adaptive_ensemble() -> AdaptiveEnsemble:
    """Create adaptive ensemble with performance-based adjustment."""
    models = [
        ModelConfig(
            name="qwen-4b-primary",
            endpoint_id="primary-endpoint",
            weight=0.5,
            priority=1
        ),
        ModelConfig(
            name="qwen-4b-backup",
            endpoint_id="backup-endpoint",
            weight=0.3,
            priority=2
        ),
        ModelConfig(
            name="qwen-4b-experimental",
            endpoint_id="experimental-endpoint",
            weight=0.2,
            priority=3
        )
    ]
    
    return AdaptiveEnsemble(
        models=models,
        strategy=EnsembleStrategy.WEIGHTED,
        min_models=2
    )
