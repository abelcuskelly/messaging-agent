# Messaging Agent API

FastAPI-based API server for the Customer Service AI Messaging Agent.

## Quick Start

```bash
cd api
pip install -r requirements.txt

# Configure environment
cp ../env.example .env
# Edit .env with your values

# Run locally
uvicorn main:app --reload

# Access API docs
open http://localhost:8000/docs
```

## Core Endpoints

### Chat Endpoint
```bash
POST /chat
```

**Request:**
```json
{
  "message": "Hello, I'd like to buy tickets for the Lakers game",
  "user_id": "user123",
  "context": {
    "previous_messages": []
  }
}
```

**Response:**
```json
{
  "response": "I can help you with Lakers tickets!...",
  "cached": false,
  "response_time_ms": 850
}
```

### Health Checks
```bash
GET /health     # Basic health check
GET /ready      # Readiness probe
GET /live       # Liveness probe
```

### Metrics
```bash
GET /metrics              # Prometheus metrics
GET /optimizer/stats      # Performance stats
```

## Features

### Performance Optimizations
- **Response Caching** - 99% faster for common queries
- **Prompt Compression** - 30% faster inference
- **Context Prefetching** - 30% faster for known users
- **Request Batching** - Cost optimization

### Security
- API key authentication
- Rate limiting (Redis-based)
- Input sanitization (XSS prevention)
- Security headers middleware

### Monitoring
- Structured logging
- BigQuery integration
- Error tracking
- Performance metrics

## Environment Variables

```bash
# Core
ENDPOINT_ID=your-vertex-endpoint-id
PROJECT_ID=your-gcp-project
REGION=us-central1

# LLM Provider
LLM_PROVIDER=anthropic  # anthropic, openai, bedrock, qwen
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key

# Redis
REDIS_URL=redis://localhost:6379

# Security
API_KEY=your-api-key
ALLOWED_ORIGINS=https://yourdomain.com

# Optional
ENABLE_CACHING=true
ENABLE_BATCHING=true
MAX_CONTEXT_TOKENS=4000
```

## Deployment

### Cloud Run
```bash
# Build and deploy
gcloud run deploy messaging-agent-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

### Docker
```bash
docker build -t messaging-agent-api .
docker run -p 8000:8000 \
  -e ENDPOINT_ID=your-id \
  -e PROJECT_ID=your-project \
  messaging-agent-api
```

## Development

### Testing
```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=api tests/
```

### Linting
```bash
flake8 api/
black api/
isort api/
```

## Documentation

- **[Full API Documentation](https://your-api.run.app/docs)** - Interactive API docs
- **[Security Guide](../SECURITY.md)** - Security best practices
- **[Deployment Guide](../DEPLOYMENT.md)** - Production deployment
