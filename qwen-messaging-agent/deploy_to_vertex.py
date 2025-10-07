#!/usr/bin/env python3
"""
Deploy merged model artifacts from GCS to a Vertex AI Endpoint.
Assumes training uploaded to: gs://$BUCKET/qwen-messaging-agent/models/merged
"""

import os
from google.cloud import aiplatform


PROJECT_ID = os.getenv("PROJECT_ID", "your-project-id")
REGION = os.getenv("REGION", "us-central1")
BUCKET_NAME = os.getenv("BUCKET_NAME", f"{PROJECT_ID}-vertex-ai-training")


def main():
    if PROJECT_ID == "your-project-id":
        raise RuntimeError("Please set PROJECT_ID, REGION, BUCKET_NAME env vars.")

    aiplatform.init(project=PROJECT_ID, location=REGION)

    artifact_uri = f"gs://{BUCKET_NAME}/qwen-messaging-agent/models/merged"
    print(f"Uploading model from {artifact_uri} ...")

    model = aiplatform.Model.upload(
        display_name="qwen-messaging-agent",
        artifact_uri=artifact_uri,
        serving_container_image_uri=
            "us-docker.pkg.dev/vertex-ai/prediction/pytorch-gpu.2-1:latest",
    )

    print("Creating endpoint ...")
    endpoint = aiplatform.Endpoint.create(
        display_name="qwen-messaging-agent-endpoint",
    )

    print("Deploying model ... this can take several minutes")
    endpoint.deploy(
        model=model,
        deployed_model_display_name="qwen-messaging-agent-v1",
        machine_type="n1-standard-4",
        accelerator_type="NVIDIA_TESLA_T4",
        accelerator_count=1,
        min_replica_count=1,
        max_replica_count=3,
        traffic_split={"0": 100},
    )

    print(f"Model deployed to endpoint: {endpoint.resource_name}")
    print("Set ENDPOINT_ID to the numeric ID from the endpoint resource for API use.")


if __name__ == "__main__":
    main()


