#!/usr/bin/env python3
"""
Hyperparameter Tuning for Qwen Messaging Agent
Uses Vertex AI Hyperparameter Tuning with Bayesian optimization
"""

import os
import argparse
from google.cloud import aiplatform
from google.cloud.aiplatform import hyperparameter_tuning as hpt


def create_hpt_job(
    project_id: str,
    region: str,
    bucket_name: str,
    image_uri: str,
    max_trial_count: int = 20,
    parallel_trial_count: int = 4
):
    """Create and submit a hyperparameter tuning job."""
    
    aiplatform.init(project=project_id, location=region)
    
    # Define hyperparameter search space
    hyperparameter_spec = {
        "learning_rate": hpt.DoubleParameterSpec(
            min=1e-5, 
            max=5e-4, 
            scale="log",
            description="Learning rate for AdamW optimizer"
        ),
        "batch_size": hpt.DiscreteParameterSpec(
            values=[2, 4, 8, 16],
            description="Training batch size per device"
        ),
        "lora_r": hpt.DiscreteParameterSpec(
            values=[16, 32, 64, 128],
            description="LoRA rank (r parameter)"
        ),
        "lora_alpha": hpt.DiscreteParameterSpec(
            values=[16, 32, 64, 128],
            description="LoRA alpha parameter"
        ),
        "lora_dropout": hpt.DoubleParameterSpec(
            min=0.01,
            max=0.2,
            scale="linear",
            description="LoRA dropout rate"
        ),
        "warmup_ratio": hpt.DoubleParameterSpec(
            min=0.01,
            max=0.1,
            scale="linear", 
            description="Warmup ratio for learning rate scheduler"
        ),
        "weight_decay": hpt.DoubleParameterSpec(
            min=0.001,
            max=0.1,
            scale="log",
            description="Weight decay for regularization"
        )
    }
    
    # Create custom training job
    job = aiplatform.CustomContainerTrainingJob(
        display_name="qwen-hpt-training",
        container_uri=image_uri,
        command=["python", "-m", "trainer.train"],
    )
    
    # Submit hyperparameter tuning job
    hpt_job = job.run(
        # Base arguments (same for all trials)
        args=[
            "--bucket_name", bucket_name,
            "--epochs", "2",  # Keep epochs low for HPT
            "--dataset_name", "OpenAssistant/oasst2",
            "--wandb_project", "qwen-hpt",
        ],
        # Resource configuration
        replica_count=1,
        machine_type="n1-standard-8",
        accelerator_type="NVIDIA_TESLA_T4",
        accelerator_count=1,
        boot_disk_size_gb=200,
        
        # Hyperparameter tuning configuration
        hyperparameter_tuning_job=hpt.HyperparameterTuningJob(
            max_trial_count=max_trial_count,
            parallel_trial_count=parallel_trial_count,
            hyperparameter_spec=hyperparameter_spec,
            metric_spec={"eval_loss": "minimize"},  # Minimize validation loss
            algorithm=hpt.Algorithm.BAYESIAN_OPTIMIZATION,
        ),
        
        # Job configuration
        sync=False,  # Don't wait for completion
        enable_web_access=True,
        enable_dashboard_access=True,
    )
    
    print(f"Hyperparameter tuning job submitted: {hpt_job.resource_name}")
    print(f"Max trials: {max_trial_count}, Parallel trials: {parallel_trial_count}")
    print(f"Monitor at: https://console.cloud.google.com/vertex-ai/training/hyperparameter-tuning-jobs")
    
    return hpt_job


def get_best_trial(hpt_job_resource_name: str):
    """Get the best trial from a completed HPT job."""
    hpt_job = aiplatform.HyperparameterTuningJob(hpt_job_resource_name)
    
    if hpt_job.state != aiplatform.JobState.JOB_STATE_SUCCEEDED:
        print(f"HPT job not completed yet. Current state: {hpt_job.state}")
        return None
    
    # Get all trials
    trials = hpt_job.trials
    
    if not trials:
        print("No trials found")
        return None
    
    # Find best trial (lowest eval_loss)
    best_trial = min(trials, key=lambda t: t.final_measurement.metrics.get("eval_loss", float("inf")))
    
    print(f"Best trial: {best_trial.id}")
    print(f"Best eval_loss: {best_trial.final_measurement.metrics.get('eval_loss', 'N/A')}")
    print("Best hyperparameters:")
    for param_name, param_value in best_trial.parameters.items():
        print(f"  {param_name}: {param_value}")
    
    return best_trial


def main():
    parser = argparse.ArgumentParser(description="Run hyperparameter tuning for Qwen messaging agent")
    parser.add_argument("--project_id", type=str, required=True)
    parser.add_argument("--region", type=str, default="us-central1")
    parser.add_argument("--bucket_name", type=str, required=True)
    parser.add_argument("--image_uri", type=str, required=True)
    parser.add_argument("--max_trials", type=int, default=20)
    parser.add_argument("--parallel_trials", type=int, default=4)
    parser.add_argument("--get_best", type=str, help="Get best trial from HPT job resource name")
    
    args = parser.parse_args()
    
    if args.get_best:
        get_best_trial(args.get_best)
    else:
        create_hpt_job(
            project_id=args.project_id,
            region=args.region,
            bucket_name=args.bucket_name,
            image_uri=args.image_uri,
            max_trial_count=args.max_trials,
            parallel_trial_count=args.parallel_trials
        )


if __name__ == "__main__":
    main()
