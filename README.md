# Qwen Messaging Agent on Vertex AI

> **🚀 Production-Ready AI Messaging Agent with 99% Faster Responses**
> 
> Enterprise-grade conversational AI for ticketing and customer support, powered by Qwen3-4B on Google Cloud Vertex AI. Features automatic performance optimizations, multi-agent orchestration capabilities, and comprehensive monitoring.

## 🎯 What's New: Performance Optimizations Now Active

**Your messaging agent is now equipped with enterprise-grade optimizations that deliver:**
- **99% faster** responses for common queries (800ms → 10ms with caching)
- **30% faster** inference for long conversations (prompt compression)
- **30% faster** responses for known users (context prefetching)
- **Real-time metrics** tracking (cache hit rates, P95/P99 latencies)
- **Multi-agent orchestration** ready (coordinate multiple AI agents)

### Technical Overview
- Image registry: Build/push the training Docker image to Google Artifact Registry in your GCP project (not GitHub). GitHub stores code; Artifact Registry stores the container used by Vertex AI Custom Training.
- Training: Vertex AI runs a Custom Container Training Job on managed GPUs (T4/V100/A100/L4). Artifacts (LoRA and merged weights) are written to Cloud Storage under `gs://$BUCKET_NAME/qwen-messaging-agent/models`.
- Deployment: The merged model is uploaded to the Vertex AI Model Registry and deployed to a Vertex AI Endpoint. The provided FastAPI service calls this endpoint and can be deployed to Cloud Run.
- Data/Cost: See `monitoring.py`, `log_handler.py`, and `cost_calculator.py` for monitoring, logging, and cost estimates.
- **Optimizations**: Response caching, prompt compression, context prefetching, and performance metrics are now integrated and enabled by default.

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

### 🚀 Quick Deploy (Optimized API)

Deploy your optimized API with all performance enhancements in 3 steps:

```bash
# Step 1: Set environment variables
export PROJECT_ID=your-gcp-project-id
export REGION=us-central1
export ENDPOINT_ID=your-vertex-endpoint-id

# Step 2: Deploy with optimizations
./deploy.sh

# Step 3: Test the deployment
SERVICE_URL=https://your-service-url.run.app
curl $SERVICE_URL/health
curl $SERVICE_URL/metrics  # View performance stats
```

**What you get:**
- ✅ Response caching (99% faster for common queries)
- ✅ Prompt compression (30% faster for long conversations)
- ✅ Context prefetching (30% faster for known users)
- ✅ Real-time metrics at `/metrics` endpoint
- ✅ Auto-scaling from 0-10 instances
- ✅ Production-ready error handling

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment options and [DEPLOY_NOW.md](DEPLOY_NOW.md) for the quickest path to production.

### Jupyter Notebooks (Interactive Development)

For interactive development, analysis, and experimentation:

```bash
# Navigate to notebooks directory
cd notebooks

# Setup Jupyter environment
python setup_jupyter.py

# Copy environment template
cp .env.template .env
# Edit .env with your actual values

# Start Jupyter Lab
jupyter lab
```

**Available Notebooks:**
- `templates/01_Quick_Start.ipynb` - Introduction and basic usage
- `analysis/02_Data_Analysis.ipynb` - Performance and conversation analysis
- `experiments/03_Model_Experiments.ipynb` - A/B testing and model evaluation
- `visualization/04_Interactive_Dashboard.ipynb` - Real-time monitoring dashboards

See `notebooks/README.md` for detailed documentation.

### Agent Orchestration (Multi-Agent Systems)

For enterprise customers using multiple AI agents or complex multi-step workflows.

#### **When to Use Orchestration**

**Don't use orchestration (current state):**
- ✅ Single agent handles all use cases
- ✅ Simple linear workflows
- ✅ Performance is critical

**Use Simple Coordinator:**
- 📊 2-3 agents need coordination
- 🔄 Sequential or parallel workflows
- 🎯 Simple conditional routing

**Use LangGraph (when ready):**
- 🏢 Enterprise multi-product workflows
- 🔁 Cyclic agent interactions
- ✋ Human-in-the-loop approval
- 📝 Complex state management
- ⚙️ **Upgrade available**: See [LangGraph Upgrade Guide](#langgraph-upgrade-path) below

#### **Quick Start**

**Single-Agent Optimization:**
```python
from orchestration import get_optimizer

optimizer = get_optimizer()

# Cache common queries (99% faster for cached responses)
cached = optimizer.get_common_query_response(query)

# Batch tool calls (60% latency reduction)
results = await optimizer.batch_tool_calls([call1, call2, call3])

# Compress prompts (30% faster inference)
compressed = optimizer.compress_prompt(messages, max_tokens=2000)
```

**Multi-Agent Sequential Workflow:**
```python
from orchestration import SimpleCoordinator, AgentTask

coordinator = SimpleCoordinator()

# Purchase tickets, then get expense approval
tasks = [
    AgentTask(
        agent_id="ticketing",
        input_data={"messages": [{"role": "user", "content": "Book 50 tickets"}]}
    ),
    AgentTask(
        agent_id="finance",
        input_data={"messages": [{"role": "user", "content": "Approve expense"}]},
        depends_on=["ticketing"]
    )
]

results = await coordinator.execute_sequential(tasks)
```

**Multi-Agent Parallel Workflow:**
```python
# Send notifications to multiple systems simultaneously
tasks = [
    AgentTask(agent_id="ticketing", input_data={"action": "send_sms"}),
    AgentTask(agent_id="sales", input_data={"action": "update_crm"}),
    AgentTask(agent_id="finance", input_data={"action": "log_expense"})
]

results = await coordinator.execute_parallel(tasks)
```

**Agent Registry and Routing:**
```python
from orchestration import get_registry, AgentCapability

registry = get_registry()

# Find agents by capability
agents = registry.find_agents_by_capability(
    AgentCapability.TICKET_PURCHASE
)

# Route to appropriate agent
agent = registry.route_to_agent("purchase_tickets")
```

#### **Components**

- **`agent_registry.py`**: Central registry for agent discovery and routing
- **`simple_coordinator.py`**: Lightweight multi-agent coordinator (no LangGraph)
- **`langgraph_placeholder.py`**: Placeholder for complex LangGraph workflows
- **`optimizations.py`**: Performance optimizations for single-agent systems

#### **🎯 Simple Multi-Agent Coordinator (Ready to Use)**

The Simple Coordinator (`orchestration/simple_coordinator.py`) is a lightweight multi-agent orchestration system that's already implemented and ready to use. **No LangGraph or heavy dependencies required!**

**Features:**
- ✅ **Sequential Execution**: Run agents one after another with context passing
- ✅ **Parallel Execution**: Run multiple agents simultaneously (63% faster)
- ✅ **Conditional Routing**: Route to agents based on conditions
- ✅ **Execution History**: Track all workflows and performance
- ✅ **Error Handling**: Graceful failure with detailed reporting
- ✅ **Zero Dependencies**: Uses only Python's built-in `asyncio`

**Coordination Strategies:**
```python
from orchestration import SimpleCoordinator, AgentTask, CoordinationStrategy

coordinator = SimpleCoordinator()

# Sequential: One agent after another
await coordinator.execute_sequential(tasks)

# Parallel: All agents at once (63% faster)
await coordinator.execute_parallel(tasks)

# Conditional: Route based on logic
await coordinator.execute_conditional(tasks, router_function)

# Generic with strategy
await coordinator.execute_workflow(
    tasks,
    strategy=CoordinationStrategy.PARALLEL
)
```

**Real Example - Ticket Purchase with Approval:**
```python
async def purchase_with_approval():
    coordinator = SimpleCoordinator()
    
    tasks = [
        # Step 1: Purchase tickets
        AgentTask(
            agent_id="ticketing",
            input_data={"messages": [{"role": "user", "content": "Book 100 tickets"}]}
        ),
        # Step 2: Get finance approval (only if > $5000)
        AgentTask(
            agent_id="finance",
            input_data={"messages": [{"role": "user", "content": "Approve expense"}]},
            depends_on=["ticketing"],
            condition=lambda: tasks[0].output.get("total_price", 0) > 5000
        ),
        # Step 3: Update CRM
        AgentTask(
            agent_id="sales",
            input_data={"messages": [{"role": "system", "content": "Update CRM"}]},
            depends_on=["ticketing"]
        )
    ]
    
    results = await coordinator.execute_sequential(tasks)
    return results
```

**Performance Comparison:**
| Execution Type | 3 Agents Time | Benefit |
|---------------|---------------|---------|
| Sequential | ~1500ms | Maintains order, context passing |
| Parallel | ~550ms | **63% faster**, independent tasks |
| Conditional | ~500ms | Only runs needed agent |

**When to Use:**
- ✅ 2-3 agents working together
- ✅ Simple workflows (sequential/parallel)
- ✅ Basic conditional routing
- ✅ Low latency requirements
- ✅ No external dependencies needed

**Monitoring:**
```python
# Get execution statistics
stats = coordinator.get_execution_stats()
print(f"Total executions: {stats['total_executions']}")
print(f"Average time: {stats['avg_time_ms']}ms")
print(f"Strategies used: {stats['strategies_used']}")
```

#### **Environment Variables**

```bash
# Current system (ticketing)
export TICKETING_ENDPOINT=projects/PROJECT/locations/REGION/endpoints/ENDPOINT

# Future agents (when deployed)
export SALES_ENDPOINT=...
export FINANCE_ENDPOINT=...
export HR_ENDPOINT=...
```

#### **Performance Impact**

**Single-Agent Optimizations:**
- Response caching: 5-10ms (cached) vs 500-1000ms (uncached) - **99% faster**
- Tool call batching: 250ms (batched) vs 600ms (sequential) - **60% faster**
- Prompt compression: **30% faster** inference
- Context prefetching: **30% latency reduction**

**Multi-Agent Coordination:**
- Sequential: ~1500ms for 2-3 agents
- Parallel: ~550ms for 2-3 agents - **63% faster**
- Conditional routing: Skip unnecessary agents

**LangGraph Overhead:**
- Adds 100-300ms latency
- Enables complex workflows worth the cost
- Use only when needed for enterprise requirements

#### **Migration Path**

**Phase 1: Current (Single Agent)**
```
User → API → Ticketing Agent → Response
```
Focus: Optimize single-agent performance with caching, batching, compression

**Phase 2: Simple Multi-Agent**
```
User → API → Router → Agent 1 → Agent 2 → Response
```
When: First customer needs 2+ products
Use: SimpleCoordinator for basic sequential/parallel workflows

**Phase 3: Complex Multi-Agent**
```
User → API → LangGraph → [Multiple Agents + Approval] → Response
```
When: Complex workflows or human approval needed
Install: `pip install langgraph langchain-google-vertexai`

#### **Example: Enterprise Workflow**

```python
# Current: Single ticketing purchase
response = chat({"message": "I need 100 tickets"})

# Future: Multi-agent with approval
coordinator = SimpleCoordinator()

tasks = [
    # Step 1: Purchase tickets
    AgentTask(
        agent_id="ticketing",
        input_data={"messages": [{"role": "user", "content": "Book 100 tickets"}]}
    ),
    # Step 2: Get finance approval if over $5K
    AgentTask(
        agent_id="finance",
        input_data={"messages": [{"role": "user", "content": "Approve expense"}]},
        condition=lambda: tasks[0].output.get("total_price", 0) > 5000
    ),
    # Step 3: Update CRM
    AgentTask(
        agent_id="sales",
        input_data={"messages": [{"role": "system", "content": "Update CRM"}]},
        depends_on=["ticketing"]
    )
]

results = await coordinator.execute_sequential(tasks)
```

#### **Monitoring**

```python
# Registry stats
registry = get_registry()
stats = registry.get_agent_stats()
print(f"Active agents: {stats['enabled_agents']}")

# Coordinator stats
coordinator = SimpleCoordinator()
stats = coordinator.get_execution_stats()
print(f"Avg execution time: {stats['avg_time_ms']}ms")

# Optimizer stats
optimizer = get_optimizer()
stats = optimizer.get_performance_stats()
print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
print(f"P95 latency: {stats['p95_response_time_ms']}ms")
```

See `orchestration/README.md` for detailed documentation, examples, and best practices.

#### **🚀 LangGraph Upgrade Path**

When your workflows become too complex for Simple Coordinator (4+ agents, human approval, cyclic flows), you can upgrade to LangGraph.

**Quick Assessment:**
```bash
# Run interactive assessment to see if you need LangGraph
python activate_langgraph.py
```

The script will:
1. ✅ Ask questions about your workflow complexity
2. 📊 Score your needs (0-15 points)
3. 💡 Recommend whether to upgrade
4. 🔧 Automatically install dependencies
5. ⚡ Activate LangGraph code (uncomment placeholder)
6. 📝 Create example workflow
7. 📚 Show import changes needed

**When to Upgrade to LangGraph:**
| Trigger | Simple Coordinator | LangGraph |
|---------|-------------------|-----------|
| Number of agents | 2-3 | **4+** ⚡ |
| Workflow type | Sequential/Parallel | **Cyclic/Complex** ⚡ |
| Human approval | ❌ | **✅ Required** ⚡ |
| State management | Stateless | **Persistent** ⚡ |
| Branching logic | Simple | **Multi-level** ⚡ |
| Error recovery | Basic | **With state** ⚡ |

**Upgrade Process:**
```bash
# Option 1: Automated (Recommended)
python activate_langgraph.py  # Interactive wizard

# Option 2: Manual
pip install langgraph==0.2.0 langchain-google-vertexai==1.0.0
# Then uncomment code in orchestration/langgraph_placeholder.py
```

**After Upgrade - Example Usage:**
```python
# Before (Simple Coordinator)
from orchestration import SimpleCoordinator
coordinator = SimpleCoordinator()
results = await coordinator.execute_sequential(tasks)

# After (LangGraph for complex workflows)
from orchestration.langgraph_orchestrator import EnterpriseOrchestrator
orchestrator = EnterpriseOrchestrator(project_id, region)

# Build complex state machine
graph = StateGraph(WorkflowState)
graph.add_node("check_inventory", check_fn)
graph.add_node("manager_approval", approval_fn)
graph.add_conditional_edges(
    "check_inventory",
    route_fn,
    {
        "needs_approval": "manager_approval",
        "auto_approve": "process_payment",
        "out_of_stock": "notify_customer"
    }
)
result = await graph.compile().ainvoke(initial_state)
```

**Performance Impact:**
- Setup overhead: +50-100ms
- Execution overhead: +90-290ms per request
- Memory: +40MB
- **Trade-off**: Worth it for complex workflows that need the features

**Rollback if Needed:**
```bash
# Switch back to Simple Coordinator anytime
mv orchestration/langgraph_orchestrator.py orchestration/langgraph_orchestrator.py.backup
# Update imports back to SimpleCoordinator
```

**Documentation:**
- 📖 **Complete Guide**: [LANGGRAPH_UPGRADE_GUIDE.md](LANGGRAPH_UPGRADE_GUIDE.md)
- 🔧 **Activation Script**: `activate_langgraph.py`
- 📝 **Placeholder Code**: `orchestration/langgraph_placeholder.py`

The upgrade is **fully reversible** and can be done in **5 minutes** with the activation script!

### 🎯 Performance Optimizations (Active by Default)

The API now includes automatic performance optimizations that are enabled by default:

#### **1. Response Caching**
- Common queries cached for 1 hour
- Cache hit: **5-10ms** vs uncached: **500-1000ms** (99% faster)
- Automatically detects and caches FAQ-style questions
- Example: "What time does the game start?" responds instantly after first ask

#### **2. Prompt Compression**
- Long conversations automatically compressed to fit context window
- Reduces tokens by 30-50% while preserving conversation quality
- **30% faster inference** with smaller context
- Configurable via `MAX_CONTEXT_TOKENS` (default: 2000)

#### **3. Context Prefetching**
- User context loaded in parallel when `user_id` provided
- Fetches preferences, history, recent orders simultaneously
- **30% latency reduction** by avoiding sequential lookups
- Automatic for requests with user identification

#### **4. Performance Metrics**
- Real-time tracking of all requests
- Available at `/metrics` and `/optimizer/stats` endpoints
- Tracks: cache hit rate, P50/P95/P99 latencies, tool calls, errors
- Use for monitoring and optimization decisions

#### **🎭 Product Demo - See It In Action**

Experience a complete text-to-buy ticket conversation:

```bash
# Run interactive product demo
python demo_conversation.py

# Choose from scenarios:
# 1. Simple Purchase (2-3 minutes)
# 2. Seat Upgrade (1-2 minutes)  
# 3. Purchase + Upgrade (complex workflow)
# 4. All scenarios
```

**Example Conversation:**
```
👤 Customer: I need tickets for tonight's game

🤖 Agent: Great! I found tonight's Lakers vs Warriors game at 7:00 PM.
          Available sections:
          🎫 Section A (Lower Bowl) - $250/seat
          🎫 Section B (Club Level) - $180/seat
          🎫 Section C (Upper Level) - $85/seat

👤 Customer: 2 tickets in Section B please

🤖 Agent: Perfect! I've placed a hold on 2 seats.
          💰 Total: $360 | ⏱️ Hold expires in 5 minutes

👤 Customer: Yes, let's proceed!

🤖 Agent: 🎉 Order Confirmed! Order #ORD_789456
          📱 Tickets sent to your mobile app!
```

**Full Documentation:**
- 📖 [DEMO_EXAMPLE.md](DEMO_EXAMPLE.md) - Complete conversation transcripts with metrics and business insights
- 🎬 [DEMO_SCRIPT.md](DEMO_SCRIPT.md) - Presentation script for customer/investor demos with talking points

#### **Testing Optimizations**
```bash
# Run optimization demo (no GCP required)
python3 test_optimizations_simple.py

# Expected output:
# ✅ Response Caching: 800ms → <1ms (99% faster)
# ✅ Prompt Compression: 41 → 24 messages (41% saved)
# ✅ Context Prefetching: 30% latency reduction
# ✅ Metrics Tracking: P95/P99 latencies, cache hit rates
```

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

### API Features & Endpoints

The optimized API (`api/main.py`) now includes:

#### **Core Endpoints**
- `POST /chat` - Main chat endpoint with caching and optimizations
- `GET /health` - Basic health check
- `GET /ready` - Readiness check with dependency validation
- `GET /live` - Liveness probe for container orchestration

#### **Metrics Endpoints**
- `GET /metrics` - Overall performance statistics and optimizer status
- `GET /optimizer/stats` - Detailed optimizer metrics (cache hit rate, latencies)

#### **Enhanced Request/Response**
```python
# Request (with new optional fields)
{
  "message": "What time does the game start?",
  "conversation_id": "optional-session-id",
  "user_id": "user123"  # NEW: enables context prefetching
}

# Response (with performance data)
{
  "response": "The game starts at 7:00 PM EST",
  "conversation_id": "abc-123",
  "cached": true,         # NEW: was response cached?
  "response_time_ms": 8.5  # NEW: actual response time
}
```

### Key Environment Variables
```bash
# Core Configuration (Required)
PROJECT_ID=your-project-id
REGION=us-central1
BUCKET_NAME=${PROJECT_ID}-vertex-ai-training
ENDPOINT_ID=your-endpoint-id

# Optimization Settings (Active by Default)
MAX_CONTEXT_TOKENS=2000      # Max tokens before prompt compression
ENABLE_CACHING=true          # Response caching (99% faster)
ENABLE_BATCHING=true         # Tool call batching (60% faster)

# Optional Services
API_KEY=your-api-key  # For authentication
REDIS_URL=redis://localhost:6379  # For distributed caching
RATE_LIMIT_PER_MINUTE=60  # API rate limiting
TRAINING_DATA_URI=gs://your-bucket/training-data  # For model monitoring

# Multi-Agent Registry (Future)
TICKETING_ENDPOINT=${ENDPOINT_ID}  # Current system
SALES_ENDPOINT=                    # Future sales agent
FINANCE_ENDPOINT=                  # Future finance agent
HR_ENDPOINT=                       # Future HR agent

# Evaluation System
OPENAI_API_KEY=your-openai-key     # For LLM-as-a-judge evaluation
EVAL_MODEL=gpt-4-turbo-preview     # GPT-4 model for evaluation
EVAL_PROVIDER=openai               # 'openai' or 'vertexai'
MIN_EVAL_SCORE=0.80                # Minimum score threshold
MIN_PASS_RATE=0.85                 # Minimum pass rate

# Ticket Platform Integrations
STUBHUB_API_KEY=your-stubhub-key
STUBHUB_API_SECRET=your-stubhub-secret
SEATGEEK_CLIENT_ID=your-seatgeek-client-id
TICKETMASTER_API_KEY=your-ticketmaster-key
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

### OAuth2/JWT Authentication System

**Features:**
- **JWT Token Authentication**: Access and refresh tokens with configurable expiration
- **User Management**: Registration, login, logout with secure password hashing (BCrypt)
- **Session Management**: Redis-based session tracking with multi-device support
- **API Key Authentication**: Service-to-service authentication for external integrations
- **Role-Based Access Control**: Fine-grained permissions with scopes
- **Token Revocation**: Immediate token blacklisting on logout
- **Rate Limiting**: Tier-based rate limits (50 req/min standard, 100 req/min premium)

**Authentication Endpoints:**
```
POST /auth/register         - Register new user
POST /auth/token           - Login (returns access & refresh tokens)
POST /auth/refresh         - Refresh access token
POST /auth/logout          - Logout and revoke tokens
GET  /auth/me              - Get current user information
GET  /auth/sessions        - List active sessions
POST /auth/sessions/revoke-all - Revoke all user sessions
POST /auth/api-key/create  - Create API key (admin only)
POST /auth/api-key/revoke  - Revoke API key
GET  /auth/api-key/validate - Validate API key
```

**Quick Start:**
```bash
# 1. Install dependencies
pip install -r api/requirements.txt

# 2. Start the secure API server
python3 api/main_secure.py

# 3. Register a user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@example.com","password":"SecurePass123!"}'

# 4. Login to get tokens
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john&password=SecurePass123!"

# 5. Use token for authenticated requests
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"What are the ticket prices?"}'
```

**Scopes & Permissions:**
- `chat` - Access chat functionality
- `view_dashboard` - View analytics dashboard
- `view_history` - View conversation history
- `delete_history` - Delete conversations
- `admin` - Administrative functions

**Security Configuration:**
```python
# Environment variables
JWT_SECRET_KEY=your-secret-key-here  # Generate with: secrets.token_urlsafe(32)
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
REDIS_HOST=localhost
REDIS_PORT=6379
```

**API Key Authentication (Service-to-Service):**
```python
# Create API key as admin
response = requests.post("/auth/api-key/create", 
    params={"service_name": "external_service", "scopes": ["chat"]},
    headers={"Authorization": f"Bearer {admin_token}"})
api_key = response.json()["api_key"]

# Use API key in requests
response = requests.post("/chat",
    json={"message": "Hello"},
    headers={"X-API-Key": api_key})
```

**Testing:**
```bash
# Run the authentication test suite
python3 test_auth.py
```

### Redis Caching Layer

**Features:**
- **Multi-tier Caching**: Different TTL strategies for various data types
- **Connection Pooling**: Up to 50 concurrent connections with health checks
- **Cache Warming**: Pre-populate cache with common queries on startup
- **Smart Key Generation**: MD5-based cache keys for consistent hashing
- **Cache Invalidation**: Pattern-based and user-specific cache clearing
- **Decorator Support**: Easy function caching with `@cached` decorator
- **Statistics Tracking**: Real-time hit rate, miss rate, and error monitoring
- **High Availability**: Support for Redis Sentinel failover

**Performance Improvements:**
- **Chat Responses**: 10-50x faster for cached queries
- **Knowledge Base**: 20-100x speedup for repeated searches
- **Embeddings**: 7-day cache reduces computation by 99%
- **API Calls**: 10-minute cache for external service responses

**Cache Configuration:**
```python
# Cache TTL Settings (in seconds)
TTL_SETTINGS = {
    "chat_response": 3600,        # 1 hour for chat responses
    "knowledge_base": 86400,      # 24 hours for KB queries
    "embeddings": 604800,         # 7 days for embeddings
    "model_prediction": 7200,     # 2 hours for model predictions
    "api_response": 600,          # 10 minutes for API responses
    "user_session": 1800,         # 30 minutes for session data
    "search_results": 3600,       # 1 hour for search results
    "conversation_summary": 7200  # 2 hours for summaries
}
```

**Cache Endpoints:**
```
POST /chat                    - Chat with intelligent caching
GET  /knowledge-base/search   - Cached knowledge base search
POST /embeddings             - Cached embedding generation
GET  /compute                - Cached expensive computations
POST /cache/warm             - Pre-populate cache (admin)
DELETE /cache/user/{id}      - Invalidate user cache (admin)
GET  /cache/stats            - Cache statistics and metrics
DELETE /cache/pattern        - Clear by pattern (admin)
POST /cache/flush            - Flush entire cache (admin)
```

**Usage Example:**
```python
from cache.redis_cache import get_cache_manager

# Get cache manager instance
cache_manager = get_cache_manager()

# Cache a chat response
cache_manager.cache_chat_response(
    message="What are ticket prices?",
    response="Lakers tickets range from $50-$2000",
    conversation_id="conv_123"
)

# Get cached response
cached = cache_manager.get_chat_response("What are ticket prices?")

# Use decorator for automatic caching
@cache_manager.cached(prefix="expensive:", ttl=7200)
def expensive_computation(x, y):
    # This will be cached for 2 hours
    return complex_calculation(x, y)

# Cache warming on startup
common_queries = ["prices", "refund policy", "parking"]
cache_manager.warm_cache(common_queries, fetch_func)
```

**Performance Testing:**
```bash
# Run cache performance tests
python3 test_cache_performance.py

# Expected results:
# Without Cache: 500-2000ms per request
# With Cache: 5-20ms per request
# Average Speedup: 10-100x faster
```

**Redis Setup:**
```bash
# Install Redis
brew install redis  # macOS
apt-get install redis-server  # Ubuntu

# Start Redis
redis-server

# Configure Redis (redis.conf)
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1  # Persistence
```

**Environment Variables:**
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50
USE_REDIS_SENTINEL=false
```

### OpenTelemetry Distributed Tracing

**Features:**
- **Full Distributed Tracing**: Complete request lifecycle tracking across all services
- **Auto-instrumentation**: Automatic tracing for FastAPI, Redis, Requests, Logging
- **Trace Propagation**: Context flows seamlessly across service boundaries
- **Multiple Exporters**: Jaeger, OTLP, Prometheus, Console output
- **Metrics Collection**: Request counts, latency, errors, cache performance
- **Baggage Support**: Contextual data propagation across services
- **Exception Recording**: Automatic error capture with stack traces
- **Performance Analysis**: Identify bottlenecks and optimize latency

**Observability Stack:**
```
Jaeger UI:     http://localhost:16686  (Trace visualization)
Prometheus:    http://localhost:9090   (Metrics collection)
OTLP Endpoint: localhost:4317          (OpenTelemetry Protocol)
```

**Metrics Tracked:**
```python
# Request Metrics
http_requests_total              # Total HTTP requests
http_request_duration_seconds    # Request latency histogram
http_requests_active             # Active concurrent requests

# Error Metrics
errors_total                     # Total errors by type

# Cache Metrics
cache_hits_total                 # Cache hit counter
cache_misses_total               # Cache miss counter
```

**Trace Visualization Example:**
```
chat.request (150ms)
├── chat.process (145ms)
│   ├── chat.cache_lookup (5ms) ✓
│   ├── chat.generate_response (135ms)
│   │   ├── model.inference (100ms)
│   │   └── chat.cache_store (3ms)
│   └── response.format (5ms)
```

**Setup:**
```bash
# 1. Start Jaeger (for trace visualization)
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 14250:14250 \
  jaegertracing/all-in-one

# 2. Start the traced API
python3 api/main_traced.py

# 3. View traces in Jaeger UI
open http://localhost:16686
```

**Environment Configuration:**
```bash
SERVICE_NAME=qwen-messaging-agent
SERVICE_VERSION=1.0.0
ENVIRONMENT=production
OTLP_ENDPOINT=localhost:4317
JAEGER_ENDPOINT=localhost:14250
PROMETHEUS_PORT=9090
SAMPLING_RATE=1.0  # 100% sampling (adjust for production)
ENABLE_JAEGER=true
ENABLE_OTLP=false
ENABLE_PROMETHEUS=true
```

**Usage in Code:**
```python
from tracing.telemetry import get_telemetry

telemetry = get_telemetry()

# Decorator-based tracing
@telemetry.traced("my_function")
def my_function(x, y):
    return x + y

# Context manager tracing
with telemetry.span("custom_operation") as span:
    span.set_attribute("user_id", user_id)
    result = perform_operation()
    span.set_attribute("result_size", len(result))

# Trace propagation across services
headers = {}
telemetry.inject_context(headers)
response = requests.post(downstream_service, headers=headers)
```

**Testing:**
```bash
# Run tracing tests
python3 test_tracing.py

# View traces in Jaeger
# 1. Open http://localhost:16686
# 2. Select service: 'qwen-messaging-agent'
# 3. Click 'Find Traces'
# 4. Explore span details and performance metrics
```

**Production Best Practices:**
- Set sampling rate to 0.1-0.5 (10-50%) for high-traffic services
- Use OTLP exporter for centralized trace collection
- Configure retention policies in Jaeger/Tempo
- Set up alerts on high latency traces
- Monitor trace sampling and storage costs

### Circuit Breakers for Error Handling

**Features:**
- **Three-State Pattern**: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)
- **Automatic Failure Detection**: Opens circuit after configurable failure threshold
- **Self-Healing**: Automatic recovery attempts after timeout period
- **Graceful Degradation**: Fallback responses when services unavailable
- **Manual Control**: Admin endpoints to reset circuits
- **Comprehensive Statistics**: Real-time monitoring of all circuit breakers
- **Thread-Safe**: Concurrent request handling with proper locking
- **Timeout Protection**: Configurable request timeouts

**Circuit Breaker Configuration:**
```python
# Registered Circuit Breakers
"model_inference":    failure_threshold=3, recovery_timeout=30s, timeout=5s
"cache_operations":   failure_threshold=5, recovery_timeout=15s
"external_api":       failure_threshold=3, recovery_timeout=60s, timeout=10s
```

**State Transitions:**
```
CLOSED (Normal Operation)
   ↓ (failures >= threshold)
OPEN (Rejecting Requests)
   ↓ (after recovery_timeout)
HALF_OPEN (Testing Recovery)
   ↓ (success_threshold met)
CLOSED (Recovered)
```

**Usage:**
```python
from resilience.circuit_breaker import circuit_breaker, CircuitBreakerError

# Decorator usage
@circuit_breaker("external_api", failure_threshold=3, recovery_timeout=60)
def call_external_api():
    return requests.get("https://api.example.com/tickets")

# Try-catch usage
try:
    result = call_external_api()
except CircuitBreakerError:
    # Circuit is open, use fallback
    result = get_fallback_response()

# Manual circuit breaker
from resilience.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker("my_service", failure_threshold=5)
try:
    result = breaker.call(risky_function, arg1, arg2)
except CircuitBreakerError:
    result = fallback_value
```

**API Endpoints:**
```
GET  /circuit-breakers              - View all circuit breaker states
POST /circuit-breakers/{name}/reset - Reset specific circuit breaker (admin)
POST /circuit-breakers/reset-all    - Reset all circuit breakers (admin)
GET  /ready                         - Readiness check with circuit status
```

**Monitoring:**
```bash
# Check circuit breaker status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/circuit-breakers

# Response includes:
# - Current state (closed/open/half_open)
# - Total requests, successes, failures
# - Success rate and rejection count
# - Recent failure details
# - Last failure timestamp
```

**Testing:**
```bash
# Run circuit breaker tests
python3 test_circuit_breakers.py

# Test scenarios:
# - Normal operation (CLOSED state)
# - Failure threshold triggering (OPEN state)
# - Recovery testing (HALF_OPEN state)
# - Fallback mechanisms
# - Manual reset
# - Performance impact
```

**Fallback Strategies:**
```python
def _get_fallback_response(message: str) -> str:
    """Intelligent fallback based on message content."""
    if "price" in message.lower():
        return "Please visit our website for current pricing"
    elif "refund" in message.lower():
        return "Contact support@example.com for refunds"
    else:
        return "Service temporarily unavailable. Please try again shortly."
```

**Production Configuration:**
```python
# Environment variables
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
CIRCUIT_BREAKER_SUCCESS_THRESHOLD=2
CIRCUIT_BREAKER_REQUEST_TIMEOUT=10.0
```

### Model A/B Testing Framework

**Features:**
- **Variant Management**: Create and manage multiple model variants for comparison
- **Traffic Splitting**: Configurable weight-based traffic allocation
- **Consistent Hashing**: Same user always gets same variant for consistency
- **Comprehensive Metrics**: Track success rate, latency, satisfaction, conversion
- **Statistical Analysis**: Automatic winner determination with significance testing
- **Redis Persistence**: Store experiment data and user assignments
- **Admin API**: Full experiment lifecycle management

**Creating an A/B Test:**
```python
from ml.ab_testing import get_ab_test_manager, ModelVariant

manager = get_ab_test_manager()

# Define variants
variants = [
    ModelVariant(
        name="baseline",
        model_id="Qwen/Qwen3-4B-Instruct-2507",
        endpoint_id="baseline-endpoint-id",
        weight=0.5,  # 50% traffic
        description="Baseline model"
    ),
    ModelVariant(
        name="finetuned",
        model_id="Qwen/Qwen3-4B-Instruct-2507-finetuned",
        endpoint_id="finetuned-endpoint-id",
        weight=0.5,  # 50% traffic
        description="Fine-tuned model"
    )
]

# Create experiment
experiment = manager.create_experiment(
    name="baseline-vs-finetuned",
    variants=variants,
    duration_days=7,
    min_sample_size=100
)

# Start experiment
experiment.start()

# Get variant for user
variant = manager.get_variant_for_user("baseline-vs-finetuned", user_id)

# Record metrics
experiment.record_request(
    variant_name="baseline",
    success=True,
    latency_ms=150,
    satisfaction=0.85
)

# Get results
results = experiment.get_results()
print(f"Winner: {results['winner']}")
```

**API Endpoints:**
```
POST /ab-tests/experiments              - Create experiment (admin)
POST /ab-tests/experiments/{name}/start - Start experiment
POST /ab-tests/experiments/{name}/pause - Pause experiment
GET  /ab-tests/experiments              - List all experiments
GET  /ab-tests/experiments/{name}       - Get experiment details
GET  /ab-tests/experiments/{name}/results - Get results with winner
GET  /ab-tests/experiments/{name}/comparison - Side-by-side comparison
POST /ab-tests/experiments/{name}/record - Record metrics
GET  /ab-tests/experiments/{name}/variant - Get user's variant
```

**Metrics Tracked:**
- Total requests per variant
- Success rate and failure rate
- Average latency (ms)
- User satisfaction score
- Conversion rate
- Statistical significance

**Winner Determination:**
```python
# Composite score calculation
score = (
    success_rate * 0.4 +
    user_satisfaction * 0.3 +
    (1 - normalized_latency) * 0.3
)
```

### Conversation State Management

**Features:**
- **12 Conversation States**: Complete dialogue flow management
- **Intent Classification**: 9 intent types with keyword matching
- **Automatic Transitions**: State changes based on user actions
- **Context Tracking**: Tickets, orders, payments, support issues
- **Redis Persistence**: State saved across sessions
- **Multi-turn Support**: Handle complex conversation flows
- **Available Actions**: Dynamic action suggestions per state

**Conversation States:**
```
GREETING → BROWSING → SELECTING → PURCHASING → PAYMENT → CONFIRMATION → CLOSING → ENDED

Support Flows (from any state):
→ SUPPORT / UPGRADE / REFUND → CLOSING
```

**Intent Types:**
- `GREETING` - Hello, hi, good morning
- `BROWSE_TICKETS` - Show, browse, available games
- `CHECK_PRICE` - Price, cost, how much
- `BUY_TICKET` - Buy, purchase, book
- `UPGRADE_SEAT` - Upgrade, better seat
- `REQUEST_REFUND` - Refund, cancel, money back
- `ASK_QUESTION` - What, when, where, how
- `COMPLAINT` - Problem, issue, unhappy
- `GOODBYE` - Bye, thanks, goodbye

**Usage:**
```python
from conversation.state_machine import get_conversation_manager, ConversationFlowManager, IntentClassifier

# Initialize
manager = get_conversation_manager()
intent_classifier = IntentClassifier()
flow_manager = ConversationFlowManager(manager, intent_classifier)

# Process user message
result = flow_manager.process_message(
    conversation_id="conv_123",
    user_id="user_456",
    message="I want to buy Lakers tickets"
)

# Result includes:
# - current_state: "browsing"
# - intent: "buy_ticket"
# - available_actions: ["select_tickets", "ask_question"]
# - suggested_prompt: "What game or event are you interested in?"
# - context: Full conversation context

# Manual state transition
manager.update_conversation(
    conversation_id="conv_123",
    trigger="select_tickets",
    selected_game="Lakers vs Warriors",
    selected_section="101"
)
```

**Context Data Tracked:**
- Selected game, section, seats
- Ticket price and order ID
- Payment method and confirmation code
- Support issue type and resolution status
- Message count and timestamps

### Automated Quality Checks

**Features:**
- **Multi-dimensional Quality Assessment**: 6 quality dimensions
- **Coherence Checking**: Length, completeness, repetition, capitalization
- **Relevance Checking**: Term overlap, generic response detection
- **Safety Checking**: Inappropriate content, PII detection, financial advice
- **Sentiment Analysis**: Positive/negative tone with Google NL API
- **Grammar Checking**: Punctuation, spacing, formatting
- **Batch Processing**: Check multiple responses efficiently
- **Quality Reporting**: Aggregate statistics and issue tracking
- **Regression Testing**: Compare model versions for quality degradation

**Quality Dimensions:**
```python
# Scoring weights
coherence_score * 0.25    # Well-formed, complete responses
relevance_score * 0.25    # Relevant to user query
safety_score * 0.20       # No inappropriate content
sentiment_score * 0.15    # Positive, helpful tone
grammar_score * 0.10      # Proper grammar and formatting
length_score * 0.05       # Appropriate response length
```

**Usage:**
```python
from quality.quality_checks import get_qa_system, QualityScore

qa_system = get_qa_system()

# Check single response
score = qa_system.check_response(
    user_message="What are the ticket prices?",
    agent_response="Lakers tickets range from $50 to $2000 depending on seats.",
    context=""
)

print(f"Overall Score: {score.overall_score:.2f}")
print(f"Passed: {score.passed}")
print(f"Issues: {score.issues}")

# Batch check
conversations = [
    {"user_message": "Hello", "agent_response": "Hi! How can I help?"},
    {"user_message": "Prices?", "agent_response": "Tickets are $50-2000"}
]

scores = qa_system.batch_check(conversations)
report = qa_system.get_quality_report(scores)

print(f"Pass Rate: {report['summary']['pass_rate']:.1%}")
print(f"Avg Score: {report['average_scores']['overall']:.2f}")
```

**Quality Thresholds:**
```python
min_overall_score = 0.7   # 70% minimum overall quality
min_coherence = 0.6       # 60% minimum coherence
min_relevance = 0.5       # 50% minimum relevance
min_safety = 0.9          # 90% minimum safety (strict)
```

**Safety Checks:**
- Inappropriate language detection
- PII leakage prevention (SSN, credit cards, phone numbers)
- Financial advice detection
- Harmful content filtering

**Regression Testing:**
```python
from quality.quality_checks import RegressionTester

tester = RegressionTester(qa_system)

# Set baseline
tester.set_baseline("v1.0", test_cases)

# Test new version
result = tester.test_regression("v2.0", test_cases, "v1.0")

if result["regression_detected"]:
    print(f"⚠️ Quality regression: {result['difference']:.2%}")
else:
    print(f"✅ No regression. Improvement: {result['difference']:.2%}")
```

### Request Batching for Cost Optimization

**Features:**
- **Intelligent Batching**: Group requests for efficient processing
- **Configurable Parameters**: Batch size, wait time, priority
- **Adaptive Batching**: Auto-adjust based on load
- **Priority Queue**: High-priority requests processed first
- **Cost Tracking**: Calculate savings from batching
- **Async Processing**: Non-blocking batch operations
- **Statistics**: Real-time batching metrics

**Cost Savings:**
```
Single Requests: 10 requests × 100ms = 1000ms total
Batched Requests: 10 requests in 1 batch = 150ms total
Cost Savings: 85% reduction in processing time
API Call Reduction: 10 calls → 1 call = 90% fewer API calls
```

**Configuration:**
```python
from optimization.request_batching import RequestBatcher

batcher = RequestBatcher(
    max_batch_size=10,        # Maximum requests per batch
    max_wait_time_ms=100,     # Maximum wait time to fill batch
    min_batch_size=2,         # Minimum requests before processing
    enable_priority=True      # Enable priority-based ordering
)

await batcher.start()
```

**Usage:**
```python
# Add request to batch
response = await batcher.add_request(
    user_id="user_123",
    message="What are the ticket prices?",
    conversation_id="conv_456",
    priority=5  # Higher = more priority
)

# Adaptive batching (auto-adjusts to load)
from optimization.request_batching import get_adaptive_batcher

adaptive_batcher = await get_adaptive_batcher()
response = await adaptive_batcher.add_request(
    user_id="user_123",
    message="Show me Lakers games",
    conversation_id="conv_456"
)

# Get batching statistics
stats = batcher.get_stats()
print(f"Total Requests: {stats['total_requests']}")
print(f"Total Batches: {stats['total_batches']}")
print(f"Avg Batch Size: {stats['avg_batch_size']:.1f}")
print(f"Avg Cost Saved: {stats['avg_cost_saved_pct']:.1f}%")
```

**Adaptive Batching:**
- **High Load** (>20 pending): Increase batch size, increase wait time
- **Low Load** (<5 pending): Decrease batch size, decrease wait time
- **Automatic Tuning**: Optimizes for both latency and cost

**Performance Impact:**
```
Without Batching:
- 100 requests × 100ms = 10,000ms
- 100 API calls
- Cost: $X

With Batching (10 per batch):
- 10 batches × 150ms = 1,500ms
- 10 API calls
- Cost: $X/10
- Savings: 85% time, 90% cost
```

### 🌐 Embeddable Chat Widget

**Complete Web Integration**: Add AI chat to any website with one line of code!

**Features:**
- **One-Line Integration**: Add widget to any website in seconds
- **Fully Customizable**: Brand colors, position, messages, and styling
- **Real-time Messaging**: Live chat with AI agent
- **Mobile Responsive**: Perfect experience on all devices
- **Professional UI**: Beautiful gradient design with smooth animations
- **No Dependencies**: Lightweight and framework-agnostic
- **Easy Configuration**: Simple JavaScript config object

**Quick Start:**
```html
<!-- Add to your website's <head> section -->
<script>
  window.qwenConfig = {
    apiUrl: 'https://your-api.com',
    apiKey: 'your-api-key',
    position: 'bottom-right',
    title: 'Chat with us',
    subtitle: 'AI-powered support'
  };
</script>
<script src="https://cdn.yoursite.com/widget/qwen-plugin.js"></script>
```

**Customization:**
- **Position**: `'bottom-right'`, `'bottom-left'`, `'top-right'`, `'top-left'`
- **Colors**: Primary and secondary brand colors (gradient)
- **Messages**: Title, subtitle, greeting, placeholder text
- **Behavior**: Auto-open, show/hide footer

**Complete Documentation**: See [widget/README.md](widget/README.md)

**Demo Portal**: Test and configure at `widget-demo/index.html`

### Mobile SDKs (iOS & Android)

**Features:**
- **Complete Native SDKs**: Swift (iOS) and Kotlin (Android) implementations
- **Authentication**: OAuth2/JWT and API key support
- **Response Caching**: LRU cache with configurable size
- **Error Handling**: Comprehensive error types and retry logic
- **Reactive Updates**: Combine (iOS) / Flow (Android) for real-time updates
- **Conversation Management**: Multi-conversation support with history
- **UI Integration**: SwiftUI and Jetpack Compose ready
- **Production Ready**: Thread-safe, memory-efficient, fully tested

**iOS SDK (Swift):**
```swift
import QwenMessagingSDK

// Configure SDK
let config = QwenSDKConfig(
    baseURL: "https://your-api.com",
    apiKey: "your-api-key",
    enableCaching: true,
    enableLogging: true
)

let sdk = QwenMessagingSDK(config: config)

// Login
try await sdk.login(username: "user", password: "pass")

// Send message
let response = try await sdk.sendMessage("What are the ticket prices?")
print(response.response)

// SwiftUI Integration
struct ChatView: View {
    @StateObject var viewModel: QwenChatViewModel
    
    var body: some View {
        VStack {
            ScrollView {
                ForEach(viewModel.messages, id: \.timestamp) { message in
                    MessageBubble(message: message)
                }
            }
            
            HStack {
                TextField("Message", text: $messageText)
                Button("Send") { viewModel.sendMessage(messageText) }
            }
        }
    }
}
```

**Android SDK (Kotlin):**
```kotlin
import com.qwen.messaging.sdk.*

// Configure SDK
val config = QwenSDKConfig(
    baseURL = "https://your-api.com",
    apiKey = "your-api-key",
    enableCaching = true,
    enableLogging = true,
    cacheSize = 50
)

val sdk = QwenMessagingSDK(config, context)

// Login
lifecycleScope.launch {
    sdk.login("user", "pass")
    
    // Send message
    val response = sdk.sendMessage("What are the ticket prices?")
    println(response.response)
}

// Jetpack Compose Integration
@Composable
fun ChatScreen() {
    val sdk = rememberQwenSDK(config)
    var messages by remember { mutableStateOf(listOf<ChatMessage>()) }
    
    LaunchedEffect(sdk) {
        sdk.messageFlow.collect { message ->
            message?.let { messages = messages + it }
        }
    }
    
    Column {
        LazyColumn { items(messages) { MessageBubble(it) } }
        Row {
            TextField(value = text, onValueChange = { text = it })
            Button(onClick = { sdk.sendMessage(text) }) { Text("Send") }
        }
    }
}
```

**Installation:**
```bash
# iOS - Swift Package Manager
dependencies: [
    .package(url: "https://github.com/your-org/qwen-sdk-ios.git", from: "1.0.0")
]

# Android - Gradle
dependencies {
    implementation 'com.qwen.messaging:sdk:1.0.0'
    implementation 'com.squareup.okhttp3:okhttp:4.12.0'
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3'
}
```

### GraphQL API

**Features:**
- **Flexible Queries**: Request exactly the data you need
- **Type-Safe Schema**: Strongly typed with Strawberry GraphQL
- **Real-time Subscriptions**: WebSocket-based live updates
- **Nested Queries**: Fetch related data in single request
- **Mutations**: Create, update, delete operations
- **GraphQL Playground**: Interactive API explorer
- **Efficient**: Reduce over-fetching and under-fetching

**GraphQL Schema:**
```graphql
type Query {
  me: User
  conversation(id: String!): Conversation
  conversations(userId: String, limit: Int): [Conversation!]!
  experiments: [Experiment!]!
  experimentResults(name: String!): ExperimentResults
  circuitBreakers: [CircuitBreakerStatus!]!
  cacheStats: CacheStats!
  systemHealth: SystemHealth!
}

type Mutation {
  sendMessage(input: ChatInput!): ChatResponse!
  login(input: LoginInput!): String!
  clearConversation(conversationId: String!): Boolean!
  resetCircuitBreaker(name: String!): Boolean!
}

type Subscription {
  messageUpdates(conversationId: String!): Message!
  systemMetrics: CacheStats!
}
```

**Example Queries:**
```graphql
# Get conversations with nested messages
query {
  conversations(limit: 5) {
    id
    state
    messages {
      role
      content
      timestamp
    }
    messageCount
  }
}

# Send message mutation
mutation {
  sendMessage(input: {
    message: "What are the ticket prices?",
    conversationId: "conv_123"
  }) {
    response
    conversationId
    cached
    durationMs
  }
}

# Subscribe to real-time updates
subscription {
  messageUpdates(conversationId: "conv_123") {
    content
    timestamp
  }
}
```

**Server Setup:**
```bash
# Start GraphQL server
python3 graphql_api/server.py

# Access GraphQL Playground
open http://localhost:8001/graphql
```

**Client Usage (Python):**
```python
import requests

query = """
query {
  conversations(limit: 5) {
    id
    state
    messageCount
  }
}
"""

response = requests.post(
    "http://localhost:8001/graphql",
    json={"query": query}
)

data = response.json()["data"]
```

### Model Ensemble

**Features:**
- **5 Aggregation Strategies**: Voting, weighted, confidence, fallback, best-of-N
- **Parallel Execution**: Run multiple models simultaneously for speed
- **Adaptive Weights**: Auto-adjust based on model performance
- **Fault Tolerance**: Fallback chain ensures reliability
- **Confidence Scoring**: Select most confident predictions
- **Performance Tracking**: Per-model statistics and monitoring
- **Dynamic Enable/Disable**: Control which models are active

**Ensemble Strategies:**
```python
# 1. VOTING - Majority vote from all models
# 2. WEIGHTED - Weighted average by model weight and confidence
# 3. CONFIDENCE - Use prediction with highest confidence
# 4. FALLBACK - Try models in priority order until success
# 5. BEST_OF_N - Select best based on composite score
```

**Usage:**
```python
from ml.model_ensemble import ModelEnsemble, ModelConfig, EnsembleStrategy

# Define models
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

# Create ensemble
ensemble = ModelEnsemble(
    models=models,
    strategy=EnsembleStrategy.WEIGHTED,
    min_models=2,
    max_latency_ms=5000
)

# Make prediction
messages = [{"role": "user", "content": "What are ticket prices?"}]
response = await ensemble.predict(messages)

# Get statistics
stats = ensemble.get_stats()
print(f"Total Predictions: {stats['total_predictions']}")
print(f"Model Stats: {stats['models']}")
```

**Adaptive Ensemble:**
```python
from ml.model_ensemble import create_adaptive_ensemble

# Creates ensemble that auto-adjusts weights
adaptive = create_adaptive_ensemble()

# Automatically improves over time based on performance
response = await adaptive.predict(messages)
```

**Benefits:**
- **Improved Accuracy**: Combine strengths of multiple models
- **Higher Reliability**: Fallback if primary model fails
- **Better Coverage**: Different models excel at different tasks
- **Performance Optimization**: Select fastest model for simple queries
- **Risk Mitigation**: Don't depend on single model

### Advanced Analytics Dashboards

**Features:**
- **4 Dashboard Types**: Executive, Technical, Business, Real-time
- **Interactive Visualizations**: Plotly-based with zoom, hover, drill-down
- **Multi-metric Views**: 6+ charts per dashboard
- **Real-time Updates**: Auto-refresh capabilities
- **Export Ready**: HTML files for sharing and embedding
- **Responsive Design**: Works on all screen sizes

**Dashboard Types:**

**1. Executive Dashboard:**
- Conversation volume trends
- Success rate over time
- Response time distribution
- User satisfaction gauge
- Top issues breakdown
- Revenue impact tracking

**2. Technical Dashboard:**
- API latency percentiles (P50, P95, P99)
- Cache hit rates by type
- Circuit breaker states
- Error rate by category

**3. Business Dashboard:**
- Conversion funnel visualization
- Revenue by channel (pie chart)
- Customer lifetime value trends
- Churn risk indicator

**4. Real-time Dashboard:**
- Live request rate
- Active users count
- Model performance metrics
- System resource usage

**Creating Dashboards:**
```python
from dashboards.advanced_dashboard import AdvancedDashboard

# Create dashboard instance
dashboard = AdvancedDashboard()

# Create all dashboards
paths = dashboard.create_all_dashboards()

# Individual dashboards
executive_path = dashboard.create_executive_dashboard(days=30)
technical_path = dashboard.create_technical_dashboard()
business_path = dashboard.create_business_dashboard()
realtime_path = dashboard.create_realtime_dashboard()

# Open in browser
import webbrowser
webbrowser.open(executive_path)
```

**Generated Files:**
- `executive_dashboard.html` - Executive summary
- `technical_dashboard.html` - Technical performance
- `business_dashboard.html` - Business metrics
- `realtime_dashboard.html` - Live monitoring

**Quick Start:**
```bash
# Generate all dashboards
python3 dashboards/advanced_dashboard.py

# Open dashboards
open executive_dashboard.html
open technical_dashboard.html
open business_dashboard.html
open realtime_dashboard.html
```

### Qdrant Vector Database

**Why Qdrant?**
- ✅ **Open-source** and self-hostable
- ✅ **High performance** with HNSW indexing (millisecond search)
- ✅ **Easy Python SDK** with async support
- ✅ **Metadata filtering** for complex queries (category, date, price range)
- ✅ **Production-ready** with clustering and replication
- ✅ **Docker deployment** for easy setup
- ✅ **Cloud option** available (Qdrant Cloud)

**Features:**
- **Semantic Search**: Find relevant knowledge using natural language
- **Metadata Filtering**: Filter by category, date, venue, price range
- **Batch Operations**: Efficient bulk document management
- **High-Level Interface**: TicketKnowledgeBase for easy integration
- **Automatic Embeddings**: Sentence transformers for vector generation
- **Fast Retrieval**: Millisecond search with HNSW indexing
- **Scalable**: Handle millions of documents

**Quick Start:**
```bash
# 1. Start Qdrant with Docker
docker compose -f docker-compose.qdrant.yml up -d

# 2. Verify it's running
curl http://localhost:6333/health

# 3. Load sample knowledge
python3 vector_db/qdrant_manager.py
```

**Usage:**
```python
from vector_db.qdrant_manager import get_vector_db, get_ticket_knowledge_base

# Initialize
vector_db = get_vector_db()
kb = get_ticket_knowledge_base()

# Add ticket pricing
kb.add_ticket_pricing(
    game="Lakers vs Warriors",
    date="2024-03-15",
    venue="Crypto.com Arena",
    pricing={
        "lower_bowl": "150-300",
        "upper_bowl": "50-120",
        "courtside": "800-2000"
    }
)

# Add policy
kb.add_policy(
    policy_type="refund",
    title="Refund Policy",
    description="Full refunds up to 48 hours before game",
    rules={
        "full_refund_hours": 48,
        "partial_refund_hours": 24,
        "exchange_fee": 15
    }
)

# Add venue info
kb.add_venue_info(
    venue_name="Crypto.com Arena",
    address="1111 S Figueroa St, Los Angeles, CA",
    capacity=19068,
    sections=["101-130", "301-330", "200s"],
    amenities=["Premium dining", "VIP lounges"]
)

# Semantic search
results = vector_db.search("What are ticket prices?", top_k=3)
for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Content: {result['content']}")

# Filtered search
pricing = kb.search_pricing(
    query="Lakers tickets",
    game="Lakers vs Warriors"
)

# Policy search
refund_info = kb.search_policies("refund", policy_type="refund")

# Load from file
kb.load_from_knowledge_base("knowledge_base.json")
```

**Docker Setup:**
```yaml
# docker-compose.qdrant.yml includes:
services:
  qdrant:    # Vector database (port 6333)
  redis:     # Caching layer (port 6379)
  jaeger:    # Distributed tracing (port 16686)
```

**Integration with RAG:**
```python
from vector_db.qdrant_manager import get_vector_db

class QdrantRAGAgent:
    def __init__(self, endpoint, vector_db):
        self.endpoint = endpoint
        self.vector_db = vector_db
    
    def chat(self, user_message: str) -> str:
        # Search knowledge base
        docs = self.vector_db.search(user_message, top_k=3)
        
        # Build context from results
        context = "\n".join([doc['content'] for doc in docs])
        
        # Create prompt with context
        messages = [
            {"role": "system", "content": f"Context: {context}"},
            {"role": "user", "content": user_message}
        ]
        
        return self.endpoint.predict(instances=[{"messages": messages}])
```

**Environment Variables:**
```bash
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=optional-for-cloud
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Fast, 384 dimensions
VECTOR_SIZE=384
```

**Performance:**
```
Search Speed: 1-5ms for 10K documents
Embedding Generation: 10-50ms per document
Batch Insert: 100 documents/second
Memory Usage: ~1GB for 100K documents
```

**Production Best Practices:**
- Use Qdrant Cloud for managed hosting
- Enable clustering for high availability
- Schedule regular backups
- Monitor collection size and performance
- Cache frequently accessed embeddings
- Use batch operations for bulk updates
- Set up replication for disaster recovery

### 🎫 Real Ticket Platform Integrations

Integrate with real ticket marketplaces for live inventory and pricing:

#### **Supported Platforms**
- ✅ **StubHub** - Secondary market, resale tickets
- ✅ **SeatGeek** - Primary + secondary market, recommendations
- ✅ **Ticketmaster** - Official primary market tickets

#### **Quick Setup**
```bash
# Get API credentials from each platform
# StubHub: https://developer.stubhub.com/
# SeatGeek: https://platform.seatgeek.com/
# Ticketmaster: https://developer.ticketmaster.com/

# Set environment variables
export STUBHUB_API_KEY=your-key
export STUBHUB_API_SECRET=your-secret
export SEATGEEK_CLIENT_ID=your-client-id
export TICKETMASTER_API_KEY=your-api-key
```

#### **Features**
- 🔍 **Multi-Platform Search**: Query all 3 platforms in parallel (3x faster)
- 💰 **Price Comparison**: Find cheapest tickets across platforms
- 🎯 **Best Deals**: Automatic deal finder with value scoring
- 📊 **Inventory Aggregation**: Combine availability from all sources
- ⚡ **Real-Time Data**: Live pricing and availability

#### **Usage Example**
```python
from integrations.ticket_platforms import UnifiedInventoryAggregator

# Initialize aggregator
aggregator = UnifiedInventoryAggregator()

# Search across all platforms
results = await aggregator.search_events(
    query="Lakers",
    city="Los Angeles"
)

# Results include:
# - Events from all 3 platforms
# - Price comparison (best_min_price)
# - Total listings across platforms
# - Platform-specific URLs

print(f"Found {results['total_events']} events")
print(f"Best price: ${results['events'][0]['best_min_price']}")
print(f"Available on: {results['events'][0]['platforms_available']} platforms")

# Find best deals under $150
deals = aggregator.find_best_deals(
    results['events'],
    max_price=150,
    min_tickets=2
)

# Compare prices for specific event
comparison = aggregator.compare_prices(
    event_name="Lakers vs Warriors",
    venue="Crypto.com Arena",
    date="2025-10-20"
)

print(f"Cheapest: ${comparison['price_comparison']['cheapest_price']}")
print(f"Savings: ${comparison['price_comparison']['potential_savings']}")
print(f"Buy from: {comparison['price_comparison']['best_platform']}")
```

#### **Agent Integration**
```python
# Updated agent tools with real inventory
from agent.tools_with_platforms import search_tickets, compare_prices

# Agent can now:
# 1. Search real inventory: search_tickets("Lakers")
# 2. Compare prices: compare_prices("Lakers vs Warriors", ...)
# 3. Find best deals: find_best_deals("Lakers", max_price=150)
```

#### **Performance**
- **Parallel querying**: 500ms (vs 1500ms sequential) - **3x faster**
- **Deduplication**: Automatic across platforms
- **Caching**: 5-minute cache for searches
- **Rate limiting**: Respects platform limits

#### **Business Value**
- 💰 **Save customers money**: Show best prices across platforms
- 📈 **Increase inventory**: 3x more tickets available
- 🎯 **Higher conversion**: More options = more sales
- 🔍 **Transparency**: Build trust with price comparison

#### **Documentation**
- 📖 **Complete Guide**: [integrations/ticket_platforms/README.md](integrations/ticket_platforms/README.md)
- 🧪 **Test Suite**: `integrations/ticket_platforms/test_platforms.py`
- 🔧 **Individual APIs**: `stubhub_api.py`, `seatgeek_api.py`, `ticketmaster_api.py`

#### **Testing**
```bash
# Test individual platforms
python integrations/ticket_platforms/stubhub_api.py
python integrations/ticket_platforms/seatgeek_api.py
python integrations/ticket_platforms/ticketmaster_api.py

# Test unified aggregator
python integrations/ticket_platforms/unified_inventory.py

# Run test suite
pytest integrations/ticket_platforms/test_platforms.py
```

###  🔬 Model Evaluation & Grading System

Comprehensive evaluation using OpenAI LLM-as-a-judge combined with domain-specific checks.

#### **Two-Layer Evaluation**

**Layer 1: LLM-as-a-Judge** (OpenAI GPT-4)
- Evaluates 6 dimensions: helpfulness, accuracy, appropriateness, tool usage, conversation flow, domain expertise
- Natural language grading with detailed feedback
- ~500ms per evaluation, ~$0.01 cost per test

**Layer 2: Domain-Specific Checks** (Rule-based)
- Price accuracy validation (math, formatting)
- Inventory validation (availability claims)
- Order flow correctness
- Policy compliance
- Tool usage appropriateness
- ~5ms per evaluation, $0.00 cost

#### **Quick Start**
```bash
# Install OpenAI
pip install openai>=1.0.0

# Set your API key
export OPENAI_API_KEY=your-openai-api-key

# Run evaluation suite
cd evals
python eval_suite.py
```

#### **Usage Examples**

**Evaluate Agent Response:**
```python
from evals import LLMJudge, DomainEvaluator

# LLM-as-a-judge evaluation
judge = LLMJudge()
result = judge.evaluate_response(
    user_message="I need 2 tickets",
    agent_response="Great! I found Section B for $180/seat. Total: $360",
    tools_used=["check_inventory"]
)

print(f"Score: {result.overall_score:.2f}")
print(f"Helpfulness: {result.helpfulness:.2f}")
print(f"Feedback: {result.feedback}")

# Domain-specific validation
domain_eval = DomainEvaluator()
domain_result = domain_eval.evaluate(
    user_message="2 tickets in Section B",
    agent_response="$180 × 2 = $360 total",
    expected_prices={"Section B": 180.00}
)

print(f"Price check passed: {domain_result['passed']}")
print(f"Issues: {domain_result['issues']}")
```

**Comprehensive Evaluation Suite:**
```python
from evals import EvaluationSuite

suite = EvaluationSuite(
    use_llm_judge=True,
    use_domain_checks=True
)

# Evaluate batch of test cases
results = suite.evaluate_batch(test_cases)
report = suite.generate_report(results)

print(f"Pass rate: {report['summary']['pass_rate']:.1%}")
print(f"Avg score: {report['summary']['avg_overall_score']:.2f}")
print(f"Recommendation: {report['recommendation']}")
```

**Pipeline Integration (Pre-Deployment):**
```python
from evals import PipelineEvaluator

evaluator = PipelineEvaluator(project_id, region, bucket_name)

# Evaluate endpoint before deploying
report = evaluator.evaluate_endpoint(
    endpoint_id="new-model",
    test_cases=standard_test_cases,
    min_score_threshold=0.85,
    min_pass_rate=0.90
)

if report['deployment_decision']['should_deploy']:
    print("✅ Model approved for deployment")
else:
    print(f"❌ {report['deployment_decision']['reason']}")
```

**A/B Testing:**
```python
# Compare two model versions
comparison = evaluator.compare_endpoints(
    endpoint_a_id="current-production-model",
    endpoint_b_id="new-candidate-model",
    test_cases=test_cases
)

print(f"Winner: {comparison['winner']}")
print(f"Score difference: {comparison['score_diff']:.2f}")
```

#### **Evaluation Dimensions**

| Dimension | Evaluator | What It Checks |
|-----------|-----------|----------------|
| Helpfulness | LLM Judge | Does it help achieve goal? |
| Accuracy | LLM Judge | Is information correct? |
| Appropriateness | LLM Judge | Professional tone? |
| Tool Usage | LLM Judge | Right tools used? |
| Conversation Flow | LLM Judge | Natural progression? |
| Domain Expertise | LLM Judge | Ticketing knowledge? |
| Price Accuracy | Domain | Math, formatting correct? |
| Inventory | Domain | Valid availability claims? |
| Order Flow | Domain | Correct step sequence? |
| Policy Compliance | Domain | Follows policies? |

#### **Performance & Cost**

| Metric | Value |
|--------|-------|
| LLM eval time | ~500ms |
| LLM cost | ~$0.01 per test |
| Domain eval time | ~5ms |
| Domain cost | $0.00 |
| Combined | ~505ms, ~$0.01 |
| Batch (100 tests) | ~50s, ~$1.00 |

**Cost Optimization**: Run domain checks first (free), use LLM for final validation.

#### **Deployment Thresholds**

| Environment | Min Score | Min Pass Rate |
|-------------|-----------|---------------|
| Production | 0.90 | 0.95 |
| Staging | 0.80 | 0.85 |
| Development | 0.70 | 0.75 |

#### **Documentation**
- 📖 **Complete Guide**: [evals/README.md](evals/README.md)
- 🤖 **LLM Judge**: `evals/llm_judge.py`
- 🎯 **Domain Checks**: `evals/domain_specific.py`
- 📊 **Eval Suite**: `evals/eval_suite.py`
- 🔧 **Pipeline Integration**: `evals/pipeline_integration.py`

### Twilio SMS Integration

**Features:**
- **Automated Confirmations**: Ticket purchase confirmations with order details
- **Game Reminders**: Scheduled reminders 24h and 2h before games
- **Upgrade Notifications**: Seat upgrade confirmations and offers
- **Refund Confirmations**: Automated refund processing notifications
- **Event Alerts**: Cancellations, rescheduling, time changes
- **Promotional SMS**: Marketing campaigns with promo codes
- **Bulk Messaging**: Send to multiple recipients efficiently
- **Incoming SMS**: Handle customer replies with auto-responses
- **Status Tracking**: Real-time delivery status updates
- **Message History**: Track all sent messages per user

**Quick Start:**
```bash
# 1. Install Twilio SDK
pip install twilio

# 2. Set environment variables
export TWILIO_ACCOUNT_SID=your_account_sid
export TWILIO_AUTH_TOKEN=your_auth_token
export TWILIO_PHONE_NUMBER=+1234567890

# 3. Test SMS integration
python3 integrations/twilio_integration.py
```

**Usage:**
```python
from integrations.twilio_integration import get_sms_manager

sms_manager = get_sms_manager()

# Send ticket confirmation
sms_manager.send_ticket_confirmation(
    to="+1234567890",
    order_id="ORD123456",
    game="Lakers vs Warriors",
    date="March 15, 2024 at 7:30 PM",
    seats="Section 101, Row A, Seats 1-2",
    total=450.00,
    confirmation_code="CONF-ABC123"
)

# Send game reminder
sms_manager.send_game_reminder(
    to="+1234567890",
    game="Lakers vs Warriors",
    date="March 15, 2024",
    time="7:30 PM",
    venue="Crypto.com Arena",
    seats="Section 101, Row A"
)

# Send upgrade notification
sms_manager.send_upgrade_notification(
    to="+1234567890",
    game="Lakers vs Warriors",
    old_seats="Section 301, Row K",
    new_seats="Section 101, Row A",
    price_difference=200.00
)

# Send refund confirmation
sms_manager.send_refund_confirmation(
    to="+1234567890",
    order_id="ORD123456",
    game="Lakers vs Warriors",
    refund_amount=450.00,
    processing_days=5
)

# Bulk SMS
results = sms_manager.send_bulk_sms(
    recipients=["+1234567890", "+0987654321"],
    body="Special offer: 20% off all Lakers tickets!",
    batch_size=100
)

**SMS Testing & Monitoring Portal:**
- **Web-based Dashboard**: Test SMS functionality without writing code
- **Real-time Statistics**: Monitor SMS sent, failed, success rate
- **Customer Observation**: View message history and customer patterns
- **Quick Tests**: Send test SMS, confirmations, reminders with one click
- **Message History**: Browse and filter all sent messages
- **Customer Analytics**: Track communication patterns per customer

**Access the Portal:**
```bash
# Start SMS Portal server
cd sms_portal
python server.py

# Access dashboard at http://localhost:8080
```

**Complete Documentation**: See [sms_portal/README.md](sms_portal/README.md)

### 📱 Social Media Integration

**Multi-Platform Customer Engagement**: Connect with customers across Twitter, LinkedIn, and Facebook (including Instagram)!

**Platforms Supported:**
- ✅ **Twitter/X**: Mentions, DMs, tweets, hashtag monitoring
- ✅ **LinkedIn**: Professional messaging, posts, connection requests
- ✅ **Facebook & Instagram**: Messenger, DMs, page comments

**Key Features:**
- **Unified Interface**: Single manager for all platforms
- **Auto-Respond**: AI-powered automatic responses
- **Brand Monitoring**: Track mentions across all platforms
- **Multi-Platform Campaigns**: Post to multiple platforms at once
- **Welcome Messages**: Automated onboarding
- **Statistics & Analytics**: Platform-specific and unified stats

**Quick Start:**
```python
from integrations.social.manager import SocialMediaManager

# Initialize all platforms
manager = SocialMediaManager()

# Get messages from all platforms
messages = manager.get_all_messages()

# Auto-respond with AI
response = manager.auto_respond_to_message('twitter', message_id, user_id)

# Monitor brand mentions
mentions = manager.monitor_brand_mentions('yourbrand')

# Create social media campaign
results = manager.create_social_campaign("New tickets available!", ['twitter', 'facebook'])
```

**API Endpoints:**
- `GET /social/platforms` - List available platforms
- `GET /social/messages` - Get messages from all platforms
- `POST /social/send` - Send message to platform
- `POST /social/reply/{platform}/{message_id}` - Reply to message
- `POST /social/auto-respond/{platform}` - AI auto-response
- `GET /social/mentions/{keyword}` - Monitor brand mentions
- `POST /social/campaign` - Create multi-platform campaign
- `GET /social/stats` - Unified statistics

**Configuration:**
```bash
# Twitter
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_TOKEN_SECRET=your_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# LinkedIn
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token

# Facebook
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_account_id
```

**Complete Documentation**: See [integrations/social/README.md](integrations/social/README.md)

### 💳 Stripe Payment Integration

**Secure Payment Processing**: Process payments directly through the messaging agent!

**Features:**
- ✅ **Payment Intents**: Direct payment processing
- ✅ **Checkout Sessions**: Hosted Stripe checkout pages
- ✅ **Customer Management**: Create and manage Stripe customers
- ✅ **Refunds**: Full and partial refund support
- ✅ **Webhook Integration**: Automatic payment status updates
- ✅ **Metadata Support**: Attach order/ticket info to payments
- ✅ **Security**: PCI-compliant payment processing

**Quick Start:**
```python
from integrations.payments.stripe_client import StripePaymentManager

# Initialize payment manager
payment_manager = StripePaymentManager()

# Create checkout session for tickets
session = payment_manager.create_checkout_session(
    items=[
        PaymentItem(
            name='Lakers vs Warriors',
            description='Section 101, Row 5',
            amount=150.00,
            quantity=2
        )
    ],
    success_url='https://yoursite.com/success',
    cancel_url='https://yoursite.com/cancel',
    customer_email='customer@example.com'
)

# Send checkout link to customer
print(f"Checkout URL: {session.url}")
```

**API Endpoints:**
- `POST /payments/intent/create` - Create payment intent
- `POST /payments/checkout/create` - Create checkout session
- `GET /payments/intent/{id}/status` - Get payment status
- `POST /payments/intent/{id}/cancel` - Cancel payment
- `POST /payments/refund` - Refund payment
- `POST /payments/customer/create` - Create customer
- `GET /payments/customer/{id}` - Get customer
- `POST /payments/webhook` - Stripe webhook handler

**Configuration:**
```bash
# Stripe Keys
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

**Get Your Keys:**
1. Go to [dashboard.stripe.com](https://dashboard.stripe.com)
2. Developers → API Keys
3. Copy Secret key (`sk_...`)
4. Copy Publishable key (`pk_...`)
5. Set up webhook and copy signing secret

**Complete Documentation**: See [integrations/payments/README.md](integrations/payments/README.md)

**SMS Templates:**
```python
from integrations.twilio_integration import SMSTemplates

# Ticket confirmation
body = SMSTemplates.ticket_confirmation(
    order_id="ORD123",
    game="Lakers vs Warriors",
    date="March 15, 2024",
    seats="Section 101",
    total=450.00,
    confirmation_code="CONF-ABC"
)

# Game reminders
reminder_24h = SMSTemplates.game_reminder_24h(...)
reminder_2h = SMSTemplates.game_reminder_2h(...)

# Event alerts
cancellation = SMSTemplates.event_cancelled(...)
rescheduled = SMSTemplates.event_rescheduled(...)
```

**API Endpoints:**
```
POST /sms/send                  - Send SMS (admin)
POST /sms/confirmation          - Send ticket confirmation
POST /sms/reminder              - Send game reminder
POST /sms/bulk                  - Send bulk SMS (admin)
GET  /sms/status/{sid}          - Get message status
GET  /sms/history/{phone}       - Get message history
GET  /sms/stats                 - Get SMS statistics
POST /sms/webhook/incoming      - Handle incoming SMS (Twilio webhook)
POST /sms/webhook/status        - Handle status updates (Twilio webhook)
```

**Webhook Configuration:**
```bash
# Configure in Twilio Console:
# 1. Go to Phone Numbers → Active Numbers
# 2. Select your number
# 3. Set webhook URLs:

Incoming Messages:
https://your-api.com/sms/webhook/incoming

Status Callbacks:
https://your-api.com/sms/webhook/status
```

**Auto-Reply Keywords:**
- `HELP` - Customer support information
- `STOP` - Unsubscribe from SMS
- `START` - Re-subscribe to SMS
- `PARKING` - Parking information
- `DETAILS` - Ticket details link

**Scheduled Reminders:**
```python
from integrations.twilio_integration import SMSScheduler
from datetime import datetime

scheduler = SMSScheduler(sms_manager)

# Schedule reminders for a game
game_time = datetime(2024, 3, 15, 19, 30)  # 7:30 PM

scheduler.schedule_game_reminders(
    phone="+1234567890",
    game="Lakers vs Warriors",
    game_datetime=game_time,
    venue="Crypto.com Arena",
    seats="Section 101, Row A"
)
# Automatically sends reminders 24h and 2h before game
```

**Integration with Purchase Flow:**
```python
# In your ticket purchase endpoint
@app.post("/tickets/purchase")
async def purchase_tickets(order: OrderRequest):
    # Process payment
    order_id = process_payment(order)
    
    # Send SMS confirmation
    sms_manager = get_sms_manager()
    sms_manager.send_ticket_confirmation(
        to=order.phone,
        order_id=order_id,
        game=order.game,
        date=order.date,
        seats=order.seats,
        total=order.total,
        confirmation_code=generate_confirmation_code()
    )
    
    # Schedule reminders
    scheduler = SMSScheduler(sms_manager)
    scheduler.schedule_game_reminders(
        phone=order.phone,
        game=order.game,
        game_datetime=order.game_datetime,
        venue=order.venue,
        seats=order.seats
    )
    
    return {"order_id": order_id, "confirmation_sent": True}
```

**Environment Variables:**
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TEST_PHONE_NUMBER=+1234567890  # For testing
```

**Cost Optimization:**
- Use message batching for bulk sends
- Track and prevent duplicate messages
- Implement rate limiting per user
- Use short links to reduce character count
- Monitor delivery rates and optimize timing

**Compliance:**
- Include opt-out instructions (STOP)
- Honor unsubscribe requests immediately
- Only send to opted-in customers
- Include business identification
- Follow TCPA regulations

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

