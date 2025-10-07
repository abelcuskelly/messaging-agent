#!/usr/bin/env python3
"""
Quick start script for training Qwen3 messaging agent on Vertex AI
Run this in an environment with gcloud configured and Artifact Registry set up
"""

import os
import time
import subprocess
from google.cloud import aiplatform, storage


# Configuration - update these before running
PROJECT_ID = os.getenv("PROJECT_ID", "your-project-id")
REGION = os.getenv("REGION", "us-central1")
BUCKET_NAME = os.getenv("BUCKET_NAME", f"{PROJECT_ID}-vertex-ai-training")
DISPLAY_NAME = os.getenv("DISPLAY_NAME", "qwen-messaging-agent")


def setup_environment():
    """Set up Cloud Storage bucket and initialize Vertex AI SDK."""
    print("Setting up environment...")

    storage_client = storage.Client(project=PROJECT_ID)
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        if not bucket.exists():
            storage_client.create_bucket(BUCKET_NAME, location=REGION)
            print(f"Bucket {BUCKET_NAME} created")
        else:
            print(f"Bucket {BUCKET_NAME} already exists")
    except Exception as e:
        print(f"Bucket exists or error: {e}")

    aiplatform.init(
        project=PROJECT_ID,
        location=REGION,
        staging_bucket=f"gs://{BUCKET_NAME}",
    )
    print("Vertex AI initialized")


def build_and_push_container():
    """Build and push training container via Cloud Build to Artifact Registry."""
    print("Building container (Cloud Build)...")

    image_uri = f"{REGION}-docker.pkg.dev/{PROJECT_ID}/ml-training/qwen-trainer:latest"

    # Build from the training project directory
    project_dir = os.path.join(os.path.dirname(__file__))

    subprocess.run(
        [
            "gcloud",
            "builds",
            "submit",
            "--tag",
            image_uri,
            "--timeout",
            "45m",
            project_dir,
        ],
        check=True,
    )

    print(f"Image pushed: {image_uri}")
    return image_uri


def submit_training_job(image_uri: str):
    """Submit a custom container training job to Vertex AI."""
    print("Submitting training job...")

    job = aiplatform.CustomContainerTrainingJob(
        display_name=f"{DISPLAY_NAME}-{int(time.time())}",
        container_uri=image_uri,
    )

    model = job.run(
        args=[
            "--bucket_name",
            BUCKET_NAME,
            "--epochs",
            "2",  # start smaller for quick validation
            "--batch_size",
            "4",
            "--learning_rate",
            "2e-4",
        ],
        replica_count=1,
        machine_type="n1-standard-8",
        accelerator_type="NVIDIA_TESLA_T4",
        accelerator_count=1,
        boot_disk_size_gb=200,
        sync=False,
    )

    print(f"Training job submitted: {job.resource_name}")
    print(
        "Monitor at: https://console.cloud.google.com/vertex-ai/training/custom-jobs"
    )
    return model


def main():
    if PROJECT_ID == "your-project-id":
        raise RuntimeError(
            "Please set PROJECT_ID/REGION/BUCKET_NAME env vars before running."
        )
    setup_environment()
    image_uri = build_and_push_container()
    submit_training_job(image_uri)
    print("\nTraining job started successfully!")


if __name__ == "__main__":
    main()


