#!/usr/bin/env python3
import os
from google.cloud import aiplatform


PROJECT_ID = os.getenv("PROJECT_ID", "your-project-id")
REGION = os.getenv("REGION", "us-central1")
BUCKET_NAME = os.getenv("BUCKET_NAME", f"{PROJECT_ID}-vertex-ai-training")


def main():
    if PROJECT_ID == "your-project-id":
        raise RuntimeError("Set PROJECT_ID/REGION/BUCKET_NAME env vars.")

    aiplatform.init(project=PROJECT_ID, location=REGION)

    image_uri = os.getenv(
        "INFER_IMAGE_URI",
        f"{REGION}-docker.pkg.dev/{PROJECT_ID}/ml-training/qwen-infer:latest",
    )

    artifact_uri = os.getenv(
        "MODEL_ARTIFACT_URI",
        f"gs://{BUCKET_NAME}/qwen-messaging-agent/models/merged",
    )

    model = aiplatform.Model.upload(
        display_name="qwen-messaging-agent-infer",
        artifact_uri=artifact_uri,
        serving_container_image_uri=image_uri,
        serving_container_ports=[8080],
        serving_container_predict_route="/predict",
        serving_container_health_route="/health",
        serving_container_environment_variables={
            "HF_MODEL": "Qwen/Qwen3-4B-Instruct-2507",
            "ATTN_IMPL": "flash_attention_2",
        },
    )

    endpoint = aiplatform.Endpoint.create(display_name="qwen-messaging-agent-endpoint-custom")
    endpoint.deploy(
        model=model,
        deployed_model_display_name="qwen-infer-v1",
        machine_type="n1-standard-4",
        accelerator_type="NVIDIA_TESLA_T4",
        accelerator_count=1,
        min_replica_count=1,
        max_replica_count=3,
        traffic_split={"0": 100},
    )
    print(f"Deployed to: {endpoint.resource_name}")


if __name__ == "__main__":
    main()


