## Qwen Messaging Agent on Vertex AI

### Technical Overview
- Image registry: Build/push the training Docker image to Google Artifact Registry in your GCP project (not GitHub). GitHub stores code; Artifact Registry stores the container used by Vertex AI Custom Training.
- Training: Vertex AI runs a Custom Container Training Job on managed GPUs (T4/V100/A100/L4). Artifacts (LoRA and merged weights) are written to Cloud Storage under `gs://$BUCKET_NAME/qwen-messaging-agent/models`.
- Deployment: The merged model is uploaded to the Vertex AI Model Registry and deployed to a Vertex AI Endpoint. The provided FastAPI service calls this endpoint and can be deployed to Cloud Run.
- Data/Cost: See `monitoring.py`, `log_handler.py`, and `cost_calculator.py` for monitoring, logging, and cost estimates.

### Quick Start

1. Set env and build/push training image (uses Cloud Build inside `quick_start.py`):
```bash
cd "qwen-messaging-agent"
export PROJECT_ID=your-project-id REGION=us-central1 BUCKET_NAME=${PROJECT_ID}-vertex-ai-training
python quick_start.py
```

2. After training, deploy merged model:
```bash
python deploy_to_vertex.py
```

3. Configure API (`api/`): set `PROJECT_ID`, `REGION`, `ENDPOINT_ID` env vars and deploy to Cloud Run.

### Build & Push Trainer (Artifact Registry)
Using Cloud Build (recommended):
```bash
export PROJECT_ID=your-project-id
export REGION=us-central1
export IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/ml-training/qwen-trainer:latest"

gcloud builds submit --tag ${IMAGE_URI}
```

Using local Docker:
```bash
export PROJECT_ID=your-project-id
export REGION=us-central1
export IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/ml-training/qwen-trainer:latest"

docker build -t ${IMAGE_URI} .
gcloud auth configure-docker ${REGION}-docker.pkg.dev
docker push ${IMAGE_URI}
```

### Run Training Job (Vertex AI)
Python SDK (as used by `quick_start.py`):
```bash
python quick_start.py
```

gcloud CLI alternative:
```bash
export PROJECT_ID=your-project-id
export REGION=us-central1
export BUCKET_NAME=${PROJECT_ID}-vertex-ai-training
export IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/ml-training/qwen-trainer:latest"

gcloud ai custom-jobs create \
  --region=${REGION} \
  --display-name=qwen_messaging_agent \
  --worker-pool-spec=replica-count=1,machine-type=n1-standard-8,accelerator-type=NVIDIA_TESLA_T4,accelerator-count=1,container-image-uri=${IMAGE_URI} \
  --args="--bucket_name=${BUCKET_NAME},--epochs=2,--batch_size=4"
```

Artifacts will be saved under:
```
gs://$BUCKET_NAME/qwen-messaging-agent/models
```

### Deploy Model to Endpoint
```bash
python deploy_to_vertex.py
# Then set ENDPOINT_ID from the printed endpoint in your API env
```

### API (Cloud Run)
Minimal proxy to Vertex Endpoint in `api/`.
```bash
cd api
export PROJECT_ID=your-project-id REGION=us-central1
gcloud builds submit --tag gcr.io/${PROJECT_ID}/qwen-api

gcloud run deploy qwen-messaging-api \
  --image gcr.io/${PROJECT_ID}/qwen-api \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

### Key Environment Variables
```bash
PROJECT_ID=your-project-id
REGION=us-central1
BUCKET_NAME=${PROJECT_ID}-vertex-ai-training
ENDPOINT_ID=your-endpoint-id
```

### Infra Requirements
- Enable APIs: `aiplatform.googleapis.com`, `artifactregistry.googleapis.com`, `storage.googleapis.com`, `compute.googleapis.com`.
- Create Artifact Registry repo `ml-training` (Docker) in your region.
- Create/stage Cloud Storage bucket `${PROJECT_ID}-vertex-ai-training`.
- Service accounts need Vertex AI + Storage permissions.

### GPU Notes
- Start with 1× T4 for development; scale to V100/A100 for speed.
- If OOM: reduce batch size to 2; keep gradient checkpointing enabled.

### Structure
- trainer/: training code (LoRA SFT, 4-bit)
- api/: FastAPI proxy to Vertex endpoint
- agent/: agent utilities (tool-calling, RAG, multi-agent)
- monitoring.py, cost_calculator.py, log_handler.py, pipeline.py
- tests/: unit/integration tests; load_test.py for API

### Team Prerequisites & IAM
- GCP roles for engineers (least privilege):
  - Vertex AI User (`roles/aiplatform.user`)
  - Storage Object Admin (`roles/storage.objectAdmin`) on the model bucket
  - Artifact Registry Writer (`roles/artifactregistry.writer`) on the repo
  - Cloud Build Editor (`roles/cloudbuild.builds.editor`) if using Cloud Build
  - Service Account User (`roles/iam.serviceAccountUser`) on the training SA

### One-time GCP Bootstrap
```bash
export PROJECT_ID=your-project-id REGION=us-central1
gcloud config set project ${PROJECT_ID}
gcloud services enable aiplatform.googleapis.com artifactregistry.googleapis.com storage.googleapis.com compute.googleapis.com cloudbuild.googleapis.com
gcloud artifacts repositories create ml-training --repository-format=docker --location=${REGION} --description="ML training images" || true
gsutil mb -l ${REGION} gs://${PROJECT_ID}-vertex-ai-training || true
```

### Local Development Setup
```bash
python3.10 -m venv .venv && source .venv/bin/activate
pip install -r qwen-messaging-agent/requirements.txt
pip install -r api/requirements.txt
```

### Environment Files
Create `.env.training`:
```bash
PROJECT_ID=your-project-id
REGION=us-central1
BUCKET_NAME=${PROJECT_ID}-vertex-ai-training
```
Create `.env.api`:
```bash
PROJECT_ID=your-project-id
REGION=us-central1
ENDPOINT_ID=your-endpoint-id
```

### Secrets Management
- Store sensitive values (e.g., Weights & Biases API key) in Secret Manager and mount or fetch at runtime.
- Example: `gcloud secrets create WANDB_API_KEY --replication-policy=automatic && echo -n "your-key" | gcloud secrets versions add WANDB_API_KEY --data-file=-`

### Dataset Customization
- Edit `trainer/dataset.py` and `prepare_dataset()` in `trainer/train.py` to use first‑party conversation logs.
- Recommended JSONL schema for fine-tuning:
```json
{"messages": [{"role": "user", "content": "I want 2 tickets for tonight."}, {"role": "assistant", "content": "Sure, for which team?"}]}
```
- Ensure messages follow the Qwen chat format; the script applies the tokenizer chat template.

### Model Sizing Guidance
- Recommended default: `Qwen/Qwen3-4B-Instruct-2507` (text-only). Fast, strong alignment, fits on a single T4 with 4‑bit.
- If GPU memory is tight, keep 4‑bit quantization, lower batch size, or shorten `max_seq_length`.

### CI/CD (Cloud Build Trigger)
- Create a trigger to build on pushes to the training directory:
```bash
gcloud beta builds triggers create github \
  --name=qwen-trainer-build \
  --region=global \
  --repo-owner=YOUR_GH_ORG --repo-name=YOUR_REPO \
  --branch-pattern=main \
  --build-config=qwen-messaging-agent/cloudbuild.yaml
```

### Testing & Quality
```bash
cd qwen-messaging-agent
python -m pytest -q tests
python load_test.py  # requires running API at localhost:8080
```

### Monitoring & Logging
- Enable deployment monitoring:
```python
from monitoring import enable_model_monitoring
enable_model_monitoring(endpoint_name="projects/PROJECT/locations/REGION/endpoints/ENDPOINT")
```
- Log interactions to BigQuery via `log_handler.ConversationLogger` (create dataset/table first).

### Rollout & Rollback
- Deploy a new model version to the same endpoint with partial traffic to canary:
```python
endpoint.deploy(model=new_model, traffic_split={"0": 90, "1": 10})
```
- Rollback by adjusting `traffic_split` back to the stable model.

### Troubleshooting
- OOM: reduce `--batch_size`, keep `gradient_checkpointing=True`, or use a larger GPU.
- Permission denied: verify IAM on Artifact Registry, Storage bucket, and Vertex AI.
- Slow training: check Flash Attention install and consider V100/A100.
- Container build failures: ensure base image compatibility and pinned deps in `requirements.txt`.

### Integrating into an Existing Codebase
- Call the Vertex Endpoint directly:
```python
from google.cloud import aiplatform
aiplatform.init(project=PROJECT_ID, location=REGION)
ep = aiplatform.Endpoint("projects/PROJECT/locations/REGION/endpoints/ENDPOINT")
resp = ep.predict(instances=[{"messages": [{"role":"user","content":"Hi"}]}])
print(resp.predictions[0]["response"])
```
- Or call the Cloud Run API:
```bash
curl -X POST "$API_URL/chat" -H "Content-Type: application/json" -d '{"message":"Hi"}'
```

### Model Source (Hugging Face)
- Base model: [Qwen3-4B-Instruct-2507 on Hugging Face](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
- Ensure license compliance and check model card guidance before production use.

### Ticketing Tool Specifications (Proposed)
These tools are exposed to the agent (see `agent/tools.py`). Implement backends in your ticketing system and wire here.

```json
{
  "check_inventory": {
    "description": "Get available seats for an event",
    "parameters": {
      "type": "object",
      "properties": {
        "event_id": {"type": "string"},
        "section": {"type": "string", "nullable": true},
        "quantity": {"type": "integer", "minimum": 1}
      },
      "required": ["event_id", "quantity"]
    }
  },
  "hold_tickets": {
    "description": "Place a temporary hold on seats",
    "parameters": {
      "type": "object",
      "properties": {
        "event_id": {"type": "string"},
        "seat_ids": {"type": "array", "items": {"type": "string"}},
        "expires_in_seconds": {"type": "integer", "default": 300}
      },
      "required": ["event_id", "seat_ids"]
    }
  },
  "create_order": {
    "description": "Create an order from a hold",
    "parameters": {
      "type": "object",
      "properties": {
        "hold_id": {"type": "string"},
        "customer_id": {"type": "string"},
        "payment_method_token": {"type": "string"}
      },
      "required": ["hold_id", "customer_id", "payment_method_token"]
    }
  },
  "upgrade_tickets": {
    "description": "Upgrade existing tickets to better seats",
    "parameters": {
      "type": "object",
      "properties": {
        "order_id": {"type": "string"},
        "target_section": {"type": "string", "nullable": true},
        "max_price_delta": {"type": "number", "nullable": true}
      },
      "required": ["order_id"]
    }
  },
  "release_hold": {
    "description": "Release a temporary hold",
    "parameters": {
      "type": "object",
      "properties": {"hold_id": {"type": "string"}},
      "required": ["hold_id"]
    }
  },
  "get_event_info": {
    "description": "Fetch metadata for an event",
    "parameters": {
      "type": "object",
      "properties": {"event_id": {"type": "string"}},
      "required": ["event_id"]
    }
  }
}
```

Minimal response shapes the agent expects:
```json
{
  "check_inventory": {"seats": [{"id": "A-12", "price": 120.0, "section": "A", "row": "5"}]},
  "hold_tickets": {"hold_id": "HOLD_123", "expires_at": "2025-10-07T01:23:45Z"},
  "create_order": {"order_id": "ORD_456", "status": "confirmed"},
  "upgrade_tickets": {"order_id": "ORD_456", "status": "upgraded", "price_delta": 30.0}
}
```

### Message Flows (Proposed)
- Purchase (pre-game):
  1) User: "Need 2 tickets tonight." → Agent calls `get_event_info` (disambiguate) → `check_inventory` → suggests best options with price.
  2) User selects section → Agent calls `hold_tickets` → confirms timer and price → collects payment → `create_order` → sends order summary + delivery.

- Upgrade (in-game):
  1) User: "Can I upgrade?" → Agent fetches current `order_id`, calls `check_inventory` for better sections within `max_price_delta`.
  2) Agent proposes upgrade → on confirm calls `upgrade_tickets` (or `hold_tickets` + `create_order` + cancel/or credit flow per backend) → returns mobile delivery update.

- Support (changes/refunds):
  1) Identify order → check policy → propose options (exchange/credit/refund) → open ticket if manual approval required.

Safeguards:
- Always confirm totals and policy impacts before charging.
- Time-bound holds; release if user goes idle.
- Use user identity (auth) to gate order creation/upgrade.

### SLAs / SLOs (Suggested)
- Chat response latency: P95 ≤ 2.0s (inference) end-to-end; P99 ≤ 3.5s.
- API availability (Cloud Run): ≥ 99.9% monthly.
- Vertex endpoint autoscaling: min=0/1, max=3; CPU/GPU utilization target 60–70%.
- Error budget: ≤ 0.1% 5xx. Alert at 0.05% over 15m.
- Escalation: Pager alert on SLO breach; rollback traffic to last stable model within 15 minutes.

