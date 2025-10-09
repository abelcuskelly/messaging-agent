"""
A/B Testing API Routes
Endpoints for managing and monitoring A/B tests
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .ab_testing import (
    get_ab_test_manager, ModelVariant, ExperimentStatus,
    ABTestManager, ABTestExperiment
)
from auth.jwt_auth import get_current_active_user, User, check_scopes
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/ab-tests", tags=["ab_testing"])


class VariantCreate(BaseModel):
    """Request model for creating a variant."""
    name: str
    model_id: str
    endpoint_id: str
    weight: float
    description: Optional[str] = ""
    config: Optional[Dict[str, Any]] = {}


class ExperimentCreate(BaseModel):
    """Request model for creating an experiment."""
    name: str
    variants: List[VariantCreate]
    duration_days: int = 7
    min_sample_size: int = 100


class MetricRecord(BaseModel):
    """Request model for recording metrics."""
    variant_name: str
    success: bool
    latency_ms: float
    satisfaction: Optional[float] = None


@router.post("/experiments")
async def create_experiment(
    experiment: ExperimentCreate,
    current_user: User = Depends(check_scopes(["admin"]))
):
    """Create a new A/B test experiment (admin only)."""
    try:
        manager = get_ab_test_manager()
        
        # Convert variants
        variants = [
            ModelVariant(
                name=v.name,
                model_id=v.model_id,
                endpoint_id=v.endpoint_id,
                weight=v.weight,
                description=v.description or "",
                config=v.config or {}
            )
            for v in experiment.variants
        ]
        
        # Create experiment
        exp = manager.create_experiment(
            name=experiment.name,
            variants=variants,
            duration_days=experiment.duration_days,
            min_sample_size=experiment.min_sample_size
        )
        
        logger.info("Experiment created",
                   name=experiment.name,
                   by_user=current_user.username)
        
        return {
            "message": "Experiment created",
            "name": exp.name,
            "status": exp.status.value,
            "variants": [v.name for v in variants]
        }
        
    except Exception as e:
        logger.error("Failed to create experiment", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/experiments/{name}/start")
async def start_experiment(
    name: str,
    current_user: User = Depends(check_scopes(["admin"]))
):
    """Start an A/B test experiment."""
    manager = get_ab_test_manager()
    experiment = manager.get_experiment(name)
    
    if not experiment:
        raise HTTPException(status_code=404, detail=f"Experiment '{name}' not found")
    
    experiment.start()
    
    logger.info("Experiment started", name=name, by_user=current_user.username)
    return {"message": f"Experiment '{name}' started"}


@router.post("/experiments/{name}/pause")
async def pause_experiment(
    name: str,
    current_user: User = Depends(check_scopes(["admin"]))
):
    """Pause an A/B test experiment."""
    manager = get_ab_test_manager()
    experiment = manager.get_experiment(name)
    
    if not experiment:
        raise HTTPException(status_code=404, detail=f"Experiment '{name}' not found")
    
    experiment.pause()
    
    logger.info("Experiment paused", name=name, by_user=current_user.username)
    return {"message": f"Experiment '{name}' paused"}


@router.post("/experiments/{name}/complete")
async def complete_experiment(
    name: str,
    current_user: User = Depends(check_scopes(["admin"]))
):
    """Complete an A/B test experiment."""
    manager = get_ab_test_manager()
    experiment = manager.get_experiment(name)
    
    if not experiment:
        raise HTTPException(status_code=404, detail=f"Experiment '{name}' not found")
    
    experiment.complete()
    
    logger.info("Experiment completed", name=name, by_user=current_user.username)
    return {"message": f"Experiment '{name}' completed"}


@router.get("/experiments")
async def list_experiments(
    current_user: User = Depends(get_current_active_user)
):
    """List all A/B test experiments."""
    manager = get_ab_test_manager()
    experiments = manager.list_experiments()
    
    return {"experiments": experiments}


@router.get("/experiments/{name}")
async def get_experiment_details(
    name: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed experiment information."""
    manager = get_ab_test_manager()
    experiment = manager.get_experiment(name)
    
    if not experiment:
        raise HTTPException(status_code=404, detail=f"Experiment '{name}' not found")
    
    return {
        "name": experiment.name,
        "status": experiment.status.value,
        "variants": [
            {
                "name": v.name,
                "model_id": v.model_id,
                "weight": v.weight,
                "description": v.description
            }
            for v in experiment.variants.values()
        ],
        "started_at": experiment.started_at.isoformat() if experiment.started_at else None,
        "duration_days": experiment.duration_days,
        "min_sample_size": experiment.min_sample_size
    }


@router.get("/experiments/{name}/results")
async def get_experiment_results(
    name: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get experiment results with statistical analysis."""
    manager = get_ab_test_manager()
    experiment = manager.get_experiment(name)
    
    if not experiment:
        raise HTTPException(status_code=404, detail=f"Experiment '{name}' not found")
    
    results = experiment.get_results()
    return results


@router.get("/experiments/{name}/comparison")
async def get_variant_comparison(
    name: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get side-by-side variant comparison."""
    manager = get_ab_test_manager()
    experiment = manager.get_experiment(name)
    
    if not experiment:
        raise HTTPException(status_code=404, detail=f"Experiment '{name}' not found")
    
    comparison = experiment.get_variant_comparison()
    return comparison


@router.post("/experiments/{name}/record")
async def record_metric(
    name: str,
    metric: MetricRecord,
    current_user: User = Depends(get_current_active_user)
):
    """Record a metric for an experiment variant."""
    manager = get_ab_test_manager()
    experiment = manager.get_experiment(name)
    
    if not experiment:
        raise HTTPException(status_code=404, detail=f"Experiment '{name}' not found")
    
    experiment.record_request(
        variant_name=metric.variant_name,
        success=metric.success,
        latency_ms=metric.latency_ms,
        satisfaction=metric.satisfaction
    )
    
    return {"message": "Metric recorded"}


@router.get("/experiments/{name}/variant")
async def get_user_variant(
    name: str,
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get assigned variant for a user."""
    manager = get_ab_test_manager()
    
    # Use current user if no user_id provided
    user_id = user_id or current_user.username
    
    variant = manager.get_variant_for_user(name, user_id)
    
    if not variant:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment '{name}' not found or not running"
        )
    
    return {
        "experiment": name,
        "user_id": user_id,
        "variant": {
            "name": variant.name,
            "model_id": variant.model_id,
            "endpoint_id": variant.endpoint_id,
            "description": variant.description
        }
    }
