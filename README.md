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

### Custom Prediction Container (Optional, Better Performance)
Build & push the inference image:
```bash
cd inference
export PROJECT_ID=your-project-id REGION=us-central1
export INFER_IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/ml-training/qwen-infer:latest"
gcloud builds submit --tag ${INFER_IMAGE_URI}
```

Deploy with custom container:
```bash
export PROJECT_ID=your-project-id REGION=us-central1 BUCKET_NAME=${PROJECT_ID}-vertex-ai-training
export INFER_IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/ml-training/qwen-infer:latest"
export MODEL_ARTIFACT_URI="gs://${BUCKET_NAME}/qwen-messaging-agent/models/merged"
python deploy_inference.py
```

Switch API to the custom endpoint:
1) Note the endpoint resource name printed by the deploy script and extract `ENDPOINT_ID` (the numeric ID at the end).
2) Update Cloud Run env:
```bash
gcloud run services update qwen-messaging-api \
  --region ${REGION} \
  --update-env-vars ENDPOINT_ID=YOUR_NEW_ENDPOINT_ID
```
3) Smoke test:
```bash
curl -X POST "$API_URL/chat" -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" -d '{"message":"Hello!"}'
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

Auth & Rate Limiting:
- Optional API key header: set `API_KEY` env var on Cloud Run; clients must send `X-API-Key: $API_KEY`.
- Redis-based rate limiting: set `REDIS_URL` env var (e.g., `redis://localhost:6379`); defaults to 60 requests/minute per IP/API key.
- Structured logging with request IDs and error handling with retries.

Health Checks:
- `/health` - Basic health check (always returns 200 if service is running)
- `/ready` - Readiness probe (validates Vertex AI endpoint and Redis connectivity)
- `/live` - Liveness probe (indicates if service should be restarted)

**Health Check Features:**
- **Dependency Validation**: `/ready` endpoint tests actual connectivity to Vertex AI endpoint and Redis
- **Graceful Degradation**: Redis failures don't block readiness (Redis is optional)
- **Proper Status Codes**: Returns 503 for readiness failures, 200 for healthy
- **Structured Logging**: Health check failures are logged with context
- **Kubernetes/Cloud Run Ready**: Designed for use with container orchestration health probes
- **Real-time Testing**: `/ready` performs actual prediction test to verify endpoint responsiveness

### Key Environment Variables
```bash
PROJECT_ID=your-project-id
REGION=us-central1
BUCKET_NAME=${PROJECT_ID}-vertex-ai-training
ENDPOINT_ID=your-endpoint-id
API_KEY=your-api-key  # Optional, for auth
REDIS_URL=redis://localhost:6379  # Optional, for rate limiting
RATE_LIMIT_PER_MINUTE=60  # Optional, default 60
TRAINING_DATA_URI=gs://your-bucket/training-data  # For model monitoring
```

### Infra Requirements
- Enable APIs: `aiplatform.googleapis.com`, `artifactregistry.googleapis.com`, `storage.googleapis.com`, `compute.googleapis.com`, `bigquery.googleapis.com`, `monitoring.googleapis.com`.
- Create Artifact Registry repo `ml-training` (Docker) in your region.
- Create/stage Cloud Storage bucket `${PROJECT_ID}-vertex-ai-training`.
- Create BigQuery dataset `messaging_logs` for conversation logging.
- Create Vertex AI Vector Search index for RAG (optional).
- Service accounts need Vertex AI + Storage + BigQuery + Monitoring + Vector Search permissions.

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

### CI/CD (Cloud Build Triggers)
Automated CI/CD is now fully implemented with multiple triggers:

**Training Pipeline Trigger:**
- Builds training and inference containers
- Submits training job to Vertex AI
- Deploys inference container automatically
- Runs on changes to training code

**API Deployment Trigger:**
- Builds and deploys API to Cloud Run
- Updates environment variables automatically
- Runs on changes to API code

**Hyperparameter Tuning Trigger:**
- Automated HPT job submission
- Runs on `hpt-*` branches
- Configurable trial counts and search space

See the [CI/CD Automation](#cicd-automation) section for complete setup instructions.

### Testing & Quality
```bash
cd qwen-messaging-agent
python -m pytest -q tests
python load_test.py  # requires running API at localhost:8080
```

### Monitoring & Logging

**Vertex Model Monitoring:**
- **Drift Detection**: Monitors prediction drift and feature skew between training and serving data
- **Sampling Strategy**: Configurable sampling rate (default 10% of requests)
- **Alert Configuration**: Notification channels for monitoring alerts
- **Dashboard Creation**: Automated Cloud Monitoring dashboard setup

Enable monitoring:
```python
from monitoring import enable_model_monitoring, create_monitoring_dashboard

# Enable model monitoring
monitoring_job = enable_model_monitoring(
    endpoint_name="projects/PROJECT/locations/REGION/endpoints/ENDPOINT",
    sample_rate=0.1,  # 10% sampling
    monitor_interval=3600  # Check every hour
)

# Create monitoring dashboard
dashboard_url = create_monitoring_dashboard(
    project_id="your-project-id",
    endpoint_name="projects/PROJECT/locations/REGION/endpoints/ENDPOINT"
)
```

**BigQuery Logging:**
- **Structured Logging**: All conversations automatically logged with metadata
- **Auto Table Creation**: Creates partitioned BigQuery table automatically
- **Performance Metrics**: Tracks duration, message/response lengths, success rates
- **Error Logging**: Separate error logging with failure details
- **Analytics Support**: Built-in conversation statistics queries
- **Time Partitioning**: Daily partitions for efficient querying

Features:
- Automatic conversation logging on every API request
- Request ID tracking for debugging
- Graceful fallback if BigQuery unavailable
- JSON metadata for flexible analysis
- Conversation statistics and analytics

Query conversation stats:
```python
from log_handler import ConversationLogger

logger = ConversationLogger()
stats = logger.get_conversation_stats(days=7)
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Avg duration: {stats['avg_duration_ms']:.0f}ms")
```

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

### Next Steps
- Build and submit training
  - Set env vars; run `quick_start.py` to build/push image and start the Vertex AI job.
  - Ensure Artifact Registry repo and GCS bucket exist; set WANDB or disable reporting.

- Deploy and wire API
  - After training, deploy model, get `ENDPOINT_ID`, set env in `api/`, deploy to Cloud Run.
  - Smoke test `/chat` and add auth/rate-limits.

- Implement ticketing backends
  - Replace stubs in `agent/tools.py` with real APIs (inventory, holds, orders, upgrades), add retries, timeouts, auth, and idempotency keys.
  - Add policy checks (refund/upgrade windows) and price confirmation prompts.

- Observability and ops
  - Enable Vertex Model Monitoring, BigQuery logging, error alerts.
  - Add budgets/alerts; set endpoint autoscaling min/max; turn on Cloud Armor if public.

- QA and rollout
  - Expand tests for tool-calling paths and upgrades; run `load_test.py` against staging.
  - Canary rollout new models; define rollback procedure.

- Optional improvements
  - RAG for team/event FAQs; index creation and retrieval path.
  - HParam tuning; Pipelines for retraining; CI/CD triggers on main.

### Production Ready Next Steps

**1. Real Ticketing Backend Integration**
- Replace stubs in `agent/tools.py` with actual API calls to your ticketing system
- Add authentication, retries, timeouts, and idempotency keys
- Implement policy checks (refund windows, upgrade eligibility)
- Add webhook notifications for order status changes

**2. Advanced Security & Compliance**
- Add OAuth2/JWT authentication for API endpoints
- Implement request signing and replay protection
- Add PII detection and redaction for conversation logs
- GDPR compliance features (data export, deletion, consent management)

**3. Enhanced Monitoring & Alerting**
- Set up Cloud Monitoring dashboards with custom business metrics
- Add alerting policies for SLO breaches, error rates, latency spikes
- Implement distributed tracing with Cloud Trace
- Add business metrics (conversion rates, ticket sales, customer satisfaction)

**4. Multi-Region Deployment**
- Deploy API and inference containers across multiple regions
- Implement global load balancing with Cloud CDN
- Add region-aware routing for low latency
- Set up cross-region failover and disaster recovery

**5. Advanced Caching & Optimization**
- Add Redis caching for frequent queries and conversation history
- Implement model response caching for similar queries
- Add CDN for static assets and API responses
- Optimize model serving with quantization and model compilation

### Multi-Modal Capabilities

**Features:**
- **Image Processing**: OCR for ticket screenshots, QR code detection, object recognition using Google Vision API
- **Voice Processing**: Speech-to-text transcription, text-to-speech synthesis for phone support
- **Document Processing**: PDF/image parsing for ticket confirmations and receipts using Document AI
- **Multimodal Agent**: Unified agent that processes text, images, audio, and documents simultaneously
- **Tool Integration**: Added multimodal tools to the agent's tool registry for seamless integration

**Image Processing:**
- Extract text from ticket screenshots and confirmations
- Detect and decode QR codes for ticket validation
- Object recognition for ticket types and venues
- Bounding box detection for precise text localization

**Voice Processing:**
- Transcribe phone support calls to text
- Generate voice responses for phone interactions
- Support for multiple languages and audio formats
- Word-level timing for precise transcription

**Document Processing:**
- Parse PDF tickets and receipts
- Extract structured data (dates, prices, seat numbers)
- Entity recognition for ticket information
- Multi-page document support

**Usage:**
```python
from agent.multimodal import MultimodalAgent, ImageProcessor, VoiceProcessor, DocumentProcessor

# Initialize processors
image_processor = ImageProcessor()
voice_processor = VoiceProcessor()
doc_processor = DocumentProcessor()

# Create multimodal agent
multimodal_agent = MultimodalAgent(endpoint, image_processor, voice_processor, doc_processor)

# Process multi-modal input
user_input = {
    "text": "I need help with my ticket",
    "image": "base64_encoded_image_data",
    "audio": "base64_encoded_audio_data",
    "document": "base64_encoded_document_data"
}

response = multimodal_agent.process_multimodal_input(user_input)
```

### Advanced Analytics

**Features:**
- **Conversation Flow Analysis**: Analyzes conversation patterns, lengths, and completion rates
- **Sentiment Analysis**: Tracks customer sentiment using Google Natural Language API
- **Business Intelligence**: Comprehensive metrics and interactive dashboard generation
- **Topic Analysis**: Identifies common conversation topics and keywords
- **Dashboard Creation**: HTML dashboard with interactive charts using Plotly

**Analytics Capabilities:**
- Daily/weekly/monthly conversation metrics
- Success rate and error rate tracking
- Average response times and conversation lengths
- Sentiment trends and customer satisfaction scores
- Conversation flow patterns (single message, short, medium, long conversations)
- Topic frequency analysis and keyword extraction

**Usage:**
```python
from analytics import BusinessIntelligence, ConversationFlowAnalyzer, SentimentAnalyzer

# Initialize analytics
bi = BusinessIntelligence()
flow_analyzer = ConversationFlowAnalyzer()
sentiment_analyzer = SentimentAnalyzer()

# Get business metrics
metrics = bi.get_business_metrics(days=30)
print(f"Success rate: {metrics['overall_metrics']['success_rate']:.2%}")

# Analyze conversation flows
flows = flow_analyzer.analyze_conversation_flows(days=7)
print(f"Flow types: {[f['flow_type'] for f in flows['flows']]}")

# Analyze sentiment
sentiment = sentiment_analyzer.analyze_sentiment("I love this service!")
print(f"Sentiment: {sentiment['sentiment_label']}")

# Create dashboard
dashboard_data = bi.create_dashboard_data(days=30)
dashboard_path = bi.export_dashboard_data(days=30, output_path="dashboard.json")
```

### Integration Ecosystem

**Features:**
- **Webhook Support**: Secure webhook subscriptions with HMAC signing for external notifications
- **Zapier Integration**: External service integrations with event handling and automation
- **Slack Bot**: Internal support bot with mention and message handling for team collaboration
- **Teams Bot**: Microsoft Teams integration for enterprise support and notifications
- **Integration API**: FastAPI endpoints for all integration services with unified management

**Webhook Events:**
- `conversation_completed`: When a chat session ends
- `ticket_purchased`: When a ticket is successfully purchased
- `ticket_upgraded`: When a ticket upgrade is completed
- `error_occurred`: When system errors or failures happen

**Integration Setup:**
```python
from integrations import create_integration_ecosystem

# Create integration ecosystem
integration_api = create_integration_ecosystem()

# Register webhook
integration_api.webhook_manager.register_webhook(
    webhook_id="crm-integration",
    url="https://your-crm.com/webhooks/tickets",
    events=["ticket_purchased", "ticket_upgraded"],
    secret="your-webhook-secret"
)

# Create Zapier trigger
zapier_trigger = integration_api.zapier.create_zapier_trigger(
    trigger_name="ticket-notifications",
    webhook_url="https://hooks.zapier.com/hooks/catch/your-zap-id/"
)
```

**Environment Variables:**
```bash
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
TEAMS_BOT_ID=your-teams-bot-id
TEAMS_BOT_PASSWORD=your-teams-bot-password
```

**API Endpoints:**
- `POST /webhooks/register` - Register new webhook
- `POST /webhooks/{webhook_id}` - Handle incoming webhook
- `POST /slack/events` - Handle Slack events
- `POST /teams/events` - Handle Teams events
- `GET /integrations/status` - Get integration status

### Enhanced Analytics Dashboard

**Features:**
- **Real-time WebSocket Updates**: Live data streaming with automatic reconnection
- **Export Functionality**: CSV and PDF export with date range filtering
- **Date Range Picker**: Custom time period selection for data analysis
- **Drill-down Capabilities**: Interactive detailed breakdowns for metrics
- **Alert Thresholds**: Configurable alerts for key performance indicators
- **User Authentication**: Secure access with HTTP Basic authentication
- **Custom Branding**: Professional styling with company colors and responsive design

**Dashboard Capabilities:**
- **Key Metrics Cards**: Total conversations, success rate, response time, sentiment
- **Interactive Charts**: Conversation flows, sentiment trends, daily metrics
- **Data Tables**: Top conversation topics, recent activity breakdown
- **Real-time Updates**: WebSocket connection for live data streaming
- **Export Options**: Download data as CSV or generate professional PDF reports
- **Drill-down Analysis**: Click charts to explore detailed breakdowns
- **Alert System**: Visual alerts when metrics exceed thresholds
- **Date Filtering**: Analyze data for custom time periods
- **Responsive Design**: Works on desktop, tablet, and mobile devices

**Authentication:**
- Username: `admin`
- Password: `qwen2024`

**Dashboard Access:**
```bash
# Start the enhanced dashboard server
python3 simple_dashboard.py --port 8080

# Access dashboard at: http://127.0.0.1:8080
```

**API Endpoints:**
- `GET /` - Main dashboard (requires authentication)
- `GET /api/dashboard` - Complete dashboard data with date filtering
- `GET /api/export/csv` - Export data as CSV file
- `GET /api/export/pdf` - Generate PDF report
- `GET /api/drill-down/{metric}` - Get detailed metric breakdowns
- `GET /api/alerts` - Get current alert status
- `WebSocket /ws` - Real-time data updates
- `GET /health` - Health check endpoint

**Alert Thresholds:**
- Success Rate: Below 85% triggers warning
- Response Time: Above 5000ms triggers warning  
- Customer Sentiment: Below 0.3 triggers danger alert

**Export Features:**
- **CSV Export**: Raw data with all metrics and date ranges
- **PDF Export**: Professional reports with charts, metrics, and alerts
- **Date Range Support**: Export data for custom time periods
- **Custom Branding**: Company colors and professional styling in PDFs

### Knowledge Base Setup for Ticket Information

**Features:**
- **Multi-format Support**: Process JSON, CSV, and text files containing ticket data
- **Automated Processing**: Convert raw ticket data into searchable knowledge base
- **Sample Data Generation**: Create test data for development and testing
- **Search Integration**: Ready for integration with RAG system
- **Flexible Data Structure**: Handle pricing, policies, team info, and statistics

**Supported Data Types:**
- **Ticket Pricing**: Game prices, seat categories, dynamic pricing
- **Policies**: Refund, upgrade, exchange policies and timeframes
- **Venue Information**: Arena details, seating charts, capacity
- **Team Statistics**: Records, player stats, season information
- **Concessions**: Food and beverage pricing and availability
- **Parking**: Rates, locations, availability information

**Quick Start:**
```bash
# Create sample data for testing
python3 simple_knowledge_base.py --create-samples

# Test the knowledge base
python3 simple_knowledge_base.py --test

# Process your ticket data
python3 simple_knowledge_base.py --process-file your_ticket_data.json --output knowledge_base.json
```

**Data Processing:**
- **JSON Files**: Structured data like team info, pricing tiers, policies
- **CSV Files**: Tabular data like game schedules, pricing tables, statistics
- **Text Files**: Unstructured information like policies, descriptions, FAQs

**Integration with RAG:**
- Processed documents are ready for Vertex AI Vector Search
- Compatible with existing RAG system in `agent/rag.py`
- Supports semantic search and retrieval for accurate responses
- Automatic categorization and metadata extraction

**Files Created:**
- `simple_knowledge_base.py` - Main processing tool
- `knowledge_base_guide.md` - Complete setup guide
- `sample_ticket_data.*` - Example data files
- `knowledge_base.json` - Processed knowledge base

**Example Usage:**
```python
from simple_knowledge_base import SimpleKnowledgeBaseBuilder

# Process your ticket data
builder = SimpleKnowledgeBaseBuilder()
documents = builder.process_ticket_data("your_ticket_data.json")

# Search for relevant information
results = builder.search_documents(documents, "What are the ticket prices?", top_k=3)

# Save processed knowledge base
builder.save_documents_to_file(documents, "knowledge_base.json")
```

### RAG (Retrieval Augmented Generation)

**Features:**
- **Vector Search**: Uses Vertex AI Vector Search with text embeddings for document retrieval
- **Text Embeddings**: Leverages `textembedding-gecko@003` for query/document embeddings
- **Context Retrieval**: Searches and formats relevant documents for enhanced responses
- **RAG Agent**: Enhanced chat agent that uses retrieved context for better answers
- **Sample Documents**: Pre-built sports ticketing FAQ documents (venue, policies, parking)
- **Graceful Fallback**: Falls back to regular chat if RAG fails

**Setup:**
1. Create Vertex AI Vector Search index:
```bash
# Create index endpoint
gcloud ai index-endpoints create --display-name="qwen-rag-index" --region=us-central1

# Create index with sample documents
python -c "
from agent.rag import create_sample_documents
from google.cloud import aiplatform_v1
import json

# Upload sample documents to your vector index
documents = create_sample_documents()
# Implementation depends on your vector index setup
"
```

2. Use RAG in your agent:
```python
from agent.rag import RAGSystem, RAGAgent
from google.cloud import aiplatform

# Initialize RAG system
rag = RAGSystem(index_endpoint="your-index-endpoint-id")
rag_agent = RAGAgent(endpoint=your_vertex_endpoint, rag_system=rag)

# Enhanced chat with context
response = rag_agent.chat("Where do the Lakers play?")
```

### Vertex AI Pipeline (Automated Training)

**Complete Pipeline**: Data Prep → Train → Eval → Conditional Deploy

**Features:**
- **Data Preparation**: Validates and prepares training datasets with quality metrics
- **Model Training**: Complete LoRA fine-tuning with 4-bit quantization and GCS upload
- **Model Evaluation**: Automated evaluation with composite scoring (response rate + quality)
- **Conditional Deployment**: Only deploys if model meets quality threshold (default 0.7)
- **GCS Integration**: Automatic model artifact upload to Cloud Storage
- **Metrics Tracking**: Comprehensive metrics at each pipeline stage
- **Parameterized**: Configurable hyperparameters and thresholds

**Run Pipeline:**
```bash
# Compile pipeline
python pipeline.py compile

# Run complete pipeline
python pipeline.py run your-project-id us-central1 your-bucket-name
```

**Pipeline Parameters:**
- `dataset_name`: Training dataset (default: "OpenAssistant/oasst2")
- `model_name`: Base model (default: "Qwen/Qwen3-4B-Instruct-2507")
- `epochs`: Training epochs (default: 2)
- `batch_size`: Batch size (default: 4)
- `learning_rate`: Learning rate (default: 2e-4)
- `eval_threshold`: Deployment threshold (default: 0.7)

**Pipeline Outputs:**
- Trained model artifacts in GCS
- Evaluation metrics and scores
- Conditional endpoint deployment
- Comprehensive logging and monitoring

### Hyperparameter Tuning

**Features:**
- **Bayesian Optimization**: Uses Vertex AI's Bayesian optimization algorithm for efficient search
- **Comprehensive Search Space**: 7 hyperparameters including learning rate, batch size, LoRA parameters, dropout, warmup ratio, weight decay
- **Parallel Trials**: Configurable parallel trial execution (default 4 trials simultaneously)
- **Best Trial Retrieval**: Function to get the best performing trial after completion
- **W&B Integration**: Automatic experiment tracking for all trials
- **Cost Optimization**: Efficient search reduces total training time and costs

**Search Space:**
- `learning_rate`: 1e-5 to 5e-4 (log scale)
- `batch_size`: [2, 4, 8, 16]
- `lora_r`: [16, 32, 64, 128] (LoRA rank)
- `lora_alpha`: [16, 32, 64, 128] (LoRA alpha)
- `lora_dropout`: 0.01 to 0.2 (linear scale)
- `warmup_ratio`: 0.01 to 0.1 (linear scale)
- `weight_decay`: 0.001 to 0.1 (log scale)

**Run HPT:**
```bash
# Submit HPT job
python hyperparameter_tuning.py \
  --project_id your-project-id \
  --region us-central1 \
  --bucket_name your-bucket-name \
  --image_uri us-central1-docker.pkg.dev/your-project/ml-training/qwen-trainer:latest \
  --max_trials 20 \
  --parallel_trials 4

# Get best trial after completion
python hyperparameter_tuning.py \
  --get_best projects/your-project/locations/us-central1/hyperparameterTuningJobs/JOB_ID
```

### CI/CD Automation

**Automated Pipelines:**
- **Training Pipeline**: Builds containers, submits training, deploys inference automatically
- **API Deployment**: Builds and deploys API to Cloud Run with environment variables
- **HPT Pipeline**: Automated hyperparameter tuning with custom build configuration
- **File-based Triggers**: Only runs when relevant files change (efficient resource usage)

**Setup CI/CD:**
```bash
# Create all triggers
python setup_cicd.py \
  --project_id your-project-id \
  --repo_owner your-github-username \
  --repo_name messaging-agent \
  --create_training \
  --create_api \
  --create_hpt

# Or create individual triggers
python setup_cicd.py --project_id your-project-id --repo_owner your-username --repo_name messaging-agent --create_training
python setup_cicd.py --project_id your-project-id --repo_owner your-username --repo_name messaging-agent --create_api
python setup_cicd.py --project_id your-project-id --repo_owner your-username --repo_name messaging-agent --create_hpt
```

**Trigger Configuration:**
- **Training Trigger**: Runs on changes to `qwen-messaging-agent/`, `inference/`, `cloudbuild-train.yaml`
- **API Trigger**: Runs on changes to `api/`, `cloudbuild-api.yaml`
- **HPT Trigger**: Runs on `hpt-*` branches for hyperparameter tuning experiments

**Workflow:**
1. **Development**: Push changes to `main` branch
2. **Training**: Automatic training pipeline runs, deploys new model
3. **API**: Automatic API deployment with new model endpoint
4. **HPT**: Create `hpt-experiment` branch for hyperparameter tuning
5. **Monitoring**: All builds logged in Cloud Build console

**Manual Triggers:**
```bash
# Trigger training pipeline manually
gcloud builds submit --config cloudbuild-train.yaml

# Trigger API deployment manually  
gcloud builds submit --config cloudbuild-api.yaml

# List existing triggers
python setup_cicd.py --list
```

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

