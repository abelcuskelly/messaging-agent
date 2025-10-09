#!/usr/bin/env python3
"""
Setup CI/CD triggers for automated training and deployment
"""

import os
import subprocess
import argparse
from typing import Optional


def create_training_trigger(
    project_id: str,
    repo_owner: str,
    repo_name: str,
    branch_pattern: str = "main"
):
    """Create Cloud Build trigger for training pipeline."""
    
    trigger_name = "qwen-training-trigger"
    
    cmd = [
        "gcloud", "beta", "builds", "triggers", "create", "github",
        "--name", trigger_name,
        "--region", "global",
        "--repo-owner", repo_owner,
        "--repo-name", repo_name,
        "--branch-pattern", branch_pattern,
        "--build-config", "cloudbuild-train.yaml",
        "--included-files", "qwen-messaging-agent/**,inference/**,cloudbuild-train.yaml",
        "--description", "Automated training pipeline for Qwen messaging agent"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Training trigger created: {trigger_name}")
        print(result.stdout)
        return trigger_name
    except subprocess.CalledProcessError as e:
        print(f"Failed to create training trigger: {e}")
        print(f"Error output: {e.stderr}")
        return None


def create_api_trigger(
    project_id: str,
    repo_owner: str,
    repo_name: str,
    branch_pattern: str = "main"
):
    """Create Cloud Build trigger for API deployment."""
    
    trigger_name = "qwen-api-trigger"
    
    cmd = [
        "gcloud", "beta", "builds", "triggers", "create", "github",
        "--name", trigger_name,
        "--region", "global",
        "--repo-owner", repo_owner,
        "--repo-name", repo_name,
        "--branch-pattern", branch_pattern,
        "--build-config", "cloudbuild-api.yaml",
        "--included-files", "api/**,cloudbuild-api.yaml",
        "--description", "Automated API deployment for Qwen messaging agent"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"API trigger created: {trigger_name}")
        print(result.stdout)
        return trigger_name
    except subprocess.CalledProcessError as e:
        print(f"Failed to create API trigger: {e}")
        print(f"Error output: {e.stderr}")
        return None


def create_hpt_trigger(
    project_id: str,
    repo_owner: str,
    repo_name: str,
    branch_pattern: str = "hpt-*"
):
    """Create Cloud Build trigger for hyperparameter tuning."""
    
    trigger_name = "qwen-hpt-trigger"
    
    # Create a custom build config for HPT
    hpt_build_config = """
steps:
  - name: gcr.io/cloud-builders/docker
    args:
      - build
      - -t
      - "$_REGION-docker.pkg.dev/$PROJECT_ID/$_REPO/$_TRAIN_IMAGE:$_TAG"
      - -f
      - qwen-messaging-agent/Dockerfile
      - qwen-messaging-agent/
    id: 'build-trainer'

  - name: gcr.io/cloud-builders/docker
    args:
      - push
      - "$_REGION-docker.pkg.dev/$PROJECT_ID/$_REPO/$_TRAIN_IMAGE:$_TAG"
    id: 'push-trainer'
    waitFor: ['build-trainer']

  - name: gcr.io/google.com/cloudsdktool/cloud-sdk
    entrypoint: python
    args:
      - hyperparameter_tuning.py
      - --project_id
      - $PROJECT_ID
      - --region
      - $_REGION
      - --bucket_name
      - $_BUCKET_NAME
      - --image_uri
      - $_REGION-docker.pkg.dev/$PROJECT_ID/$_REPO/$_TRAIN_IMAGE:$_TAG
      - --max_trials
      - $_MAX_TRIALS
      - --parallel_trials
      - $_PARALLEL_TRIALS
    id: 'submit-hpt'
    waitFor: ['push-trainer']

images:
  - "$_REGION-docker.pkg.dev/$PROJECT_ID/$_REPO/$_TRAIN_IMAGE:$_TAG"

substitutions:
  _REGION: us-central1
  _REPO: ml-training
  _TRAIN_IMAGE: qwen-trainer
  _TAG: latest
  _BUCKET_NAME: ${PROJECT_ID}-vertex-ai-training
  _MAX_TRIALS: 20
  _PARALLEL_TRIALS: 4

options:
  machineType: "E2_HIGHCPU_8"
  logging: CLOUD_LOGGING_ONLY

timeout: "7200s"
"""
    
    # Write HPT build config to temp file
    hpt_config_path = "cloudbuild-hpt.yaml"
    with open(hpt_config_path, "w") as f:
        f.write(hpt_build_config)
    
    cmd = [
        "gcloud", "beta", "builds", "triggers", "create", "github",
        "--name", trigger_name,
        "--region", "global",
        "--repo-owner", repo_owner,
        "--repo-name", repo_name,
        "--branch-pattern", branch_pattern,
        "--build-config", hpt_config_path,
        "--included-files", "qwen-messaging-agent/**,hyperparameter_tuning.py,cloudbuild-hpt.yaml",
        "--description", "Automated hyperparameter tuning for Qwen messaging agent"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"HPT trigger created: {trigger_name}")
        print(result.stdout)
        return trigger_name
    except subprocess.CalledProcessError as e:
        print(f"Failed to create HPT trigger: {e}")
        print(f"Error output: {e.stderr}")
        return None


def list_triggers():
    """List all Cloud Build triggers."""
    cmd = ["gcloud", "builds", "triggers", "list"]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Existing Cloud Build triggers:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Failed to list triggers: {e}")


def main():
    parser = argparse.ArgumentParser(description="Setup CI/CD triggers for Qwen messaging agent")
    parser.add_argument("--project_id", type=str, required=True)
    parser.add_argument("--repo_owner", type=str, required=True)
    parser.add_argument("--repo_name", type=str, required=True)
    parser.add_argument("--create_training", action="store_true", help="Create training trigger")
    parser.add_argument("--create_api", action="store_true", help="Create API trigger")
    parser.add_argument("--create_hpt", action="store_true", help="Create HPT trigger")
    parser.add_argument("--list", action="store_true", help="List existing triggers")
    
    args = parser.parse_args()
    
    if args.list:
        list_triggers()
        return
    
    triggers_created = []
    
    if args.create_training:
        trigger = create_training_trigger(args.project_id, args.repo_owner, args.repo_name)
        if trigger:
            triggers_created.append(trigger)
    
    if args.create_api:
        trigger = create_api_trigger(args.project_id, args.repo_owner, args.repo_name)
        if trigger:
            triggers_created.append(trigger)
    
    if args.create_hpt:
        trigger = create_hpt_trigger(args.project_id, args.repo_owner, args.repo_name)
        if trigger:
            triggers_created.append(trigger)
    
    if not any([args.create_training, args.create_api, args.create_hpt]):
        print("No triggers specified. Use --create_training, --create_api, or --create_hpt")
        return
    
    print(f"\nCreated {len(triggers_created)} triggers:")
    for trigger in triggers_created:
        print(f"  - {trigger}")
    
    print(f"\nView triggers at: https://console.cloud.google.com/cloud-build/triggers?project={args.project_id}")


if __name__ == "__main__":
    main()
