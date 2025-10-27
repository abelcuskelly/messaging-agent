# Customer Service AI Messaging Agent System

> **🚀 Production-Ready AI Messaging Agent with 99% Faster Responses**
> 
> Enterprise-grade conversational AI for customer support and ticketing. Choose from easy cloud APIs (Anthropic, OpenAI, Bedrock) or advanced deployment with custom model training on Google Cloud Vertex AI.

## 🎯 Quick Links

- **[Easy Setup](EASY_SETUP.md)** - Get started in 5 minutes with cloud APIs
- **[Admin Panel](admin_panel/README.md)** - Comprehensive management dashboard
- **[Mobile App](admin_panel/mobile/README.md)** - Native iOS & Android apps
- **[Advanced Features](admin_panel/ADVANCED_FEATURES.md)** - Custom dashboards, webhooks, reports, integrations
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions

## 🌟 Key Features

### **Choose Your Setup**

**Easy Setup** (5 minutes):
- ✅ **Anthropic Claude** - Best reasoning and safety
- ✅ **OpenAI GPT** - Most compatible and widely used
- ✅ **AWS Bedrock** - Multiple models via AWS

**Advanced Setup** (Full Control):
- ✅ **Google Cloud Vertex AI** - Enterprise infrastructure
- ✅ **Custom Model Training** - LoRA fine-tuning
- ✅ **Qwen3-4B** - Full model control

### **Core Capabilities**
- 🤖 **Intelligent Conversations** - Natural language understanding
- ⚡ **Performance Optimized** - 99% faster with caching
- 🔧 **Tool Calling** - Real-world integrations
- 📊 **RAG System** - Knowledge base integration
- 📈 **Analytics** - Comprehensive monitoring
- 🌐 **Multi-Channel** - SMS, web widgets, social media
- 💳 **Payments** - Stripe integration
- 🎛️ **Admin Panel** - Complete management system

## 🚀 Quick Start

### Option 1: Easy Setup (Recommended for Most Users)

Get started with cloud APIs in 5 minutes:

```bash
# See detailed instructions
cat EASY_SETUP.md
```

### Option 2: Advanced Setup (Custom Training)

Train and deploy your own model:

```bash
# 1. Build and train
cd qwen-messaging-agent
export PROJECT_ID=your-project-id REGION=us-central1 BUCKET_NAME=${PROJECT_ID}-vertex-ai-training
python quick_start.py

# 2. Deploy model
python deploy_to_vertex.py

# 3. Configure and deploy API
cd ../api
export ENDPOINT_ID=your-endpoint-id
# Deploy to Cloud Run
```

## 📚 Documentation

### Setup & Deployment
- **[Easy Setup Guide](EASY_SETUP.md)** - Get started with cloud APIs
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment
- **[Deploy Now](DEPLOY_NOW.md)** - Quickest path to production

### Components

#### Core System
- **[API Server](api/README.md)** - Main API endpoints and features
- **[Agent System](qwen-messaging-agent/agent/README.md)** - Agent logic and tools
- **[Training](qwen-messaging-agent/trainer/README.md)** - Model training pipeline
- **[Orchestration](orchestration/README.md)** - Multi-agent coordination

#### Integrations
- **[Ticket Platforms](integrations/ticket_platforms/README.md)** - StubHub, SeatGeek, Ticketmaster
- **[Twilio SMS](TWILIO_SETUP.md)** - SMS messaging
- **[Social Media](integrations/social/README.md)** - Twitter, LinkedIn, Facebook
- **[Stripe Payments](integrations/payments/README.md)** - Payment processing
- **[Qdrant Vector DB](vector_db/SETUP_GUIDE.md)** - Vector database setup

#### Admin & Monitoring
- **[Admin Panel](admin_panel/README.md)** - Complete management dashboard
- **[Mobile App](admin_panel/mobile/README.md)** - iOS & Android apps
- **[Advanced Features](admin_panel/ADVANCED_FEATURES.md)** - Custom dashboards, webhooks, reports
- **[SMS Portal](sms_portal/README.md)** - SMS testing and monitoring

#### Development Tools
- **[Jupyter Notebooks](notebooks/README.md)** - Interactive development
- **[Evaluation System](evals/README.md)** - Model evaluation and grading
- **[Widget & SDK](widget/README.md)** - Embeddable chat widget

### Support
- **[Security Guide](SECURITY.md)** - Security best practices
- **[API Key Setup](API_KEY_SETUP.md)** - Secure API key management
- **[Evaluation Setup](EVAL_SETUP.md)** - Model evaluation configuration

## 🎯 Getting Started

### Prerequisites

**For Easy Setup:**
- API keys for your chosen provider (Anthropic, OpenAI, or AWS)
- Basic environment configuration

**For Advanced Setup:**
- Google Cloud project with Vertex AI enabled
- GCS bucket for model artifacts
- Docker for containerization
- Python 3.8+

### Installation

```bash
# Clone repository
git clone https://github.com/your-username/messaging-agent.git
cd messaging-agent

# Choose your setup path
cat EASY_SETUP.md        # For cloud APIs
cat DEPLOYMENT.md        # For custom training
```

### Environment Variables

```bash
# Core configuration
PROJECT_ID=your-gcp-project-id    # For advanced setup
REGION=us-central1                 # GCP region
ENDPOINT_ID=your-endpoint-id       # Vertex endpoint

# LLM Provider (choose one)
LLM_PROVIDER=anthropic             # or openai, bedrock, qwen
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
AWS_ACCESS_KEY_ID=your-key

# Redis (for caching and rate limiting)
REDIS_URL=redis://localhost:6379

# Twilio (for SMS)
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token

# Stripe (for payments)
STRIPE_SECRET_KEY=your-key
```

## 🏗️ Architecture

### Component Overview

```
├── api/                    # FastAPI application
├── qwen-messaging-agent/   # Model training & agent logic
├── admin_panel/            # Management dashboard
├── integrations/           # External service integrations
├── notebooks/              # Interactive development
├── evals/                  # Model evaluation
└── widgets/                # Web integrations
```

### Data Flow

1. **User Input** → API receives request
2. **Processing** → Agent processes with tool calling
3. **RAG Enhancement** → Retrieves relevant context
4. **LLM Generation** → Produces response
5. **Cache Storage** → Stores for faster future responses
6. **Response Delivery** → Returns to user

## 🎯 Use Cases

### Customer Support
- **24/7 Availability** - Always-on customer service
- **Multilingual Support** - Natural language understanding
- **Context Awareness** - Remembers conversation history
- **Fast Resolution** - Average <2s response time

### Ticketing & Sales
- **Ticket Information** - Real-time inventory checks
- **Price Comparison** - Multi-platform pricing
- **Seat Upgrades** - Automated upgrade suggestions
- **Order Processing** - End-to-end purchase flow

### Enterprise Integration
- **Multi-Channel** - SMS, web, social media
- **Payment Processing** - Stripe integration
- **Analytics** - Comprehensive reporting
- **Admin Control** - Full system management

## 📊 Performance

### Benchmarks
- ⚡ **99% faster** - Cached responses (<10ms)
- 🚀 **30% faster** - Prompt compression
- 📈 **30% faster** - Context prefetching
- 🎯 **99.9% uptime** - Production reliability
- 💰 **85% cost savings** - Optimized infrastructure

### Scaling
- **Auto-scaling** - 0 to 100+ instances
- **Rate Limiting** - 100+ requests/minute
- **Global CDN** - Low-latency responses
- **Monitoring** - Real-time health checks

## 🔒 Security

- ✅ **HTTPS Only** - All endpoints encrypted
- ✅ **API Key Authentication** - Bearer token security
- ✅ **Rate Limiting** - DDoS protection
- ✅ **Input Sanitization** - XSS prevention
- ✅ **Audit Logging** - Complete activity tracking
- ✅ **Role-Based Access** - Granular permissions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
- Deployed on [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai)
- Integrated with [Twilio](https://www.twilio.com/), [Stripe](https://stripe.com/), [Slack](https://slack.com/)

---

**Need Help?** Check the [documentation](./README.md) or [open an issue](https://github.com/your-username/messaging-agent/issues)