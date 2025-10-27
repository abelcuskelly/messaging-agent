# Monitoring & Logging

Comprehensive monitoring and logging system for the messaging agent.

## Quick Start

```bash
# Enable Vertex Model Monitoring
python monitoring.py \
  --endpoint_id=your-endpoint-id \
  --project=your-project-id \
  --region=us-central1
```

## Components

### Vertex Model Monitoring
- Drift detection
- Sampling configuration
- Alert setup
- Automatic dashboards

### BigQuery Logging
- Structured conversation logs
- Auto table creation
- Performance metrics
- Error tracking

### Cloud Monitoring
- Custom dashboards
- Alert policies
- Service-level indicators

## Usage

```python
from log_handler import ConversationLogger

logger = ConversationLogger(
    project_id="your-project",
    dataset_id="conversations",
    table_id="messages"
)

# Log conversation
logger.log_conversation(
    user_id="user123",
    messages=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ],
    success=True,
    response_time_ms=850,
    intent="greeting"
)

# Query statistics
stats = logger.get_conversation_stats(days=7)
print(f"Total conversations: {stats['total']}")
print(f"Success rate: {stats['success_rate']}%")
print(f"Avg response time: {stats['avg_response_time']}ms")
```

## Cost Calculator

```bash
python cost_calculator.py
```

Estimates costs for:
- Training jobs
- Inference API calls
- Model storage
- Network egress

## Documentation

- **[monitoring.py](../monitoring.py)** - Vertex monitoring setup
- **[log_handler.py](../log_handler.py)** - BigQuery logging
- **[cost_calculator.py](../cost_calculator.py)** - Cost estimation
