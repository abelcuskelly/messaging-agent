# 🚀 Easy Setup Guide

## Overview

The messaging agent now supports **Easy Setup** using popular cloud APIs, in addition to the advanced Qwen + Google Vertex AI option.

---

## 🎯 Two Deployment Options

### **Option 1: Easy Setup** (Recommended for Quick Start)
✅ **Anthropic Claude** - Best reasoning and safety
✅ **OpenAI GPT** - Most compatible and widely used  
✅ **AWS Bedrock** - Multiple model support via AWS

**Pros**: Fast setup, no infrastructure, pay-as-you-go  
**Best for**: Quick prototypes, small teams, testing

### **Option 2: Advanced Setup** (Current)
✅ **Qwen + Vertex AI** - Full control, customization  
✅ **LoRA fine-tuning** - Train your own model  
✅ **Google Cloud infrastructure**

**Pros**: Full control, cost optimization at scale  
**Best for**: Enterprise deployments, custom training

---

## 🚀 Easy Setup - Quick Start

### **Choose Your Provider**

Pick one of these providers based on your needs:

| Provider | Best For | Models | Cost |
|----------|----------|--------|------|
| **Anthropic Claude** | Safety, reasoning, long context | claude-3-5-sonnet, claude-3-5-haiku | $3-$15 per 1M tokens |
| **OpenAI GPT** | Compatibility, ecosystem | gpt-4o, gpt-4-turbo, gpt-3.5-turbo | $5-$60 per 1M tokens |
| **AWS Bedrock** | Enterprise AWS, multiple models | Claude, Llama, Titan | $0.40-$15 per 1M tokens |

---

## 📋 Setup Instructions

### **1. Anthropic Claude Setup**

```bash
# Install Anthropic SDK
pip install anthropic

# Set environment variable
export ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

**Get Your API Key:**
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account
3. Copy your API key (starts with `sk-ant-`)

**Usage:**
```python
from llm_providers.manager import get_easy_setup_manager

# Initialize Claude
manager = get_easy_setup_manager(provider='anthropic')

# Chat with Claude
response = manager.create_chat(
    system_prompt="You are a helpful ticket assistant",
    messages=[
        {'role': 'user', 'content': 'What game tickets are available?'}
    ],
    model='claude-3-5-sonnet-20241022'
)

print(response)  # Claude's response
```

### **2. OpenAI GPT Setup**

```bash
# Install OpenAI SDK
pip install openai

# Set environment variable
export OPENAI_API_KEY=sk-your-api-key-here
```

**Get Your API Key:**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create an account
3. Copy your API key (starts with `sk-`)

**Usage:**
```python
from llm_providers.manager import get_easy_setup_manager

# Initialize GPT
manager = get_easy_setup_manager(provider='openai')

# Chat with GPT
response = manager.create_chat(
    system_prompt="You are a helpful ticket assistant",
    messages=[
        {'role': 'user', 'content': 'Find Lakers tickets'}
    ],
    model='gpt-4o'
)

print(response)  # GPT's response
```

### **3. AWS Bedrock Setup**

```bash
# Install boto3
pip install boto3

# Set AWS credentials
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1
```

**Get AWS Credentials:**
1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Create an AWS account
3. Enable Bedrock service
4. Create IAM user with Bedrock access
5. Download access keys

**Usage:**
```python
from llm_providers.manager import get_easy_setup_manager

# Initialize Bedrock
manager = get_easy_setup_manager(provider='bedrock')

# Chat with Bedrock (Claude)
response = manager.create_chat(
    system_prompt="You are a helpful ticket assistant",
    messages=[
        {'role': 'user', 'content': 'Show me seat upgrades'}
    ],
    model='anthropic.claude-3-5-sonnet-20241022-v2:0'
)

print(response)  # Claude's response via Bedrock
```

---

## 🔄 Switching Between Providers

```python
from llm_providers.manager import get_easy_setup_manager

# Initialize manager
manager = get_easy_setup_manager()

# Generate with Claude
response1 = manager.generate(
    messages=[{'role': 'user', 'content': 'Hello'}],
    provider='anthropic'
)

# Switch to OpenAI
manager.set_active_provider('openai')

# Generate with GPT
response2 = manager.generate(
    messages=[{'role': 'user', 'content': 'Hello'}],
    provider='openai'
)
```

---

## 🎨 Integration with Messaging Agent

### **Use Easy Setup in Your Agent**

```python
from llm_providers.manager import get_easy_setup_manager

# Initialize with Claude
llm_manager = get_easy_setup_manager(provider='anthropic')

# In your chat endpoint
def process_chat(message: str):
    response = llm_manager.generate(
        messages=[
            {'role': 'user', 'content': message}
        ],
        model='claude-3-5-sonnet-20241022',
        max_tokens=500
    )
    
    return response.content
```

### **Environment Configuration**

Add to your `.env` file:

```bash
# Easy Setup Provider
LLM_PROVIDER=anthropic  # or 'openai' or 'bedrock'

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key

# OpenAI
OPENAI_API_KEY=sk-your-key

# AWS Bedrock
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
```

---

## 💰 Cost Comparison

### **Per 1M Tokens (Input + Output)**

| Model | Input Cost | Output Cost | Use Case |
|-------|-----------|-------------|----------|
| **Claude 3.5 Sonnet** | $3 | $15 | High-quality responses |
| **Claude 3.5 Haiku** | $0.25 | $1.25 | Fast and cheap |
| **GPT-4o** | $5 | $15 | Most capable |
| **GPT-4o Mini** | $0.15 | $0.60 | Very affordable |
| **GPT-3.5 Turbo** | $0.50 | $1.50 | Fast |
| **Bedrock Claude** | $3 | $15 | Enterprise AWS |

---

## 🆚 Easy Setup vs Advanced Setup

| Feature | Easy Setup | Advanced Setup (Qwen + Vertex) |
|---------|------------|--------------------------------|
| **Setup Time** | 5 minutes | 30+ minutes |
| **Infrastructure** | You choose ONE: OpenAI API, Anthropic API, or AWS Bedrock | Google Cloud Vertex AI |
| **Model Training** | No | Yes (LoRA) |
| **Customization** | Limited | Full control |
| **Cost at Scale** | $0.50-15/M tokens | $0.01-0.50/M tokens |
| **Best For** | Quick start | Production at scale |
| **Providers** | Choose one: Anthropic OR OpenAI OR Bedrock | Qwen (custom) |

**Important**: You select ONE provider at a time:
- **Anthropic** = Uses Anthropic's managed API (their infrastructure)
- **OpenAI** = Uses OpenAI's managed API (their infrastructure)
- **Bedrock** = Uses AWS's managed Bedrock service (AWS infrastructure)

**Easy Setup means**:
- ✅ No custom model training required
- ✅ Uses pre-trained models from chosen provider
- ✅ Provider manages the infrastructure for you
- ✅ Simple API access via credentials
- ✅ Switch providers anytime if needed

---

## 🧪 Testing Your Setup

```python
# Test with each provider
managers = {
    'anthropic': get_easy_setup_manager('anthropic'),
    'openai': get_easy_setup_manager('openai'),
    'bedrock': get_easy_setup_manager('bedrock')
}

test_message = "What are the ticket prices?"

for name, manager in managers.items():
    response = manager.generate(
        messages=[{'role': 'user', 'content': test_message}]
    )
    print(f"{name}: {response.content[:100]}")
```

---

## 📚 Provider Details

### **Anthropic Claude**

**Models Available:**
- `claude-3-5-sonnet-20241022` - Most capable (recommended)
- `claude-3-5-haiku-20241022` - Fast and cheap
- `claude-3-opus-20240229` - Previous gen

**Strengths:**
- Best for safety and ethics
- Long context (200K tokens)
- Excellent reasoning
- Less likely to hallucinate

### **OpenAI GPT**

**Models Available:**
- `gpt-4o` - Latest, most capable
- `gpt-4-turbo` - Fast GPT-4
- `gpt-4` - Standard GPT-4
- `gpt-3.5-turbo` - Cheap and fast

**Strengths:**
- Widest ecosystem
- Most compatible
- Great documentation
- Function calling support

### **AWS Bedrock**

**Models Available:**
- Claude (Anthropic)
- Llama 3 (Meta)
- Titan (Amazon)
- Jurassic (AI21)

**Strengths:**
- Enterprise AWS integration
- Multiple models in one API
- AWS-native security
- Compliance ready

---

## ✅ Success Checklist

- [ ] Chosen provider (Anthropic/OpenAI/Bedrock)
- [ ] API key obtained
- [ ] Environment variable set
- [ ] Provider installed (`pip install`)
- [ ] Tested provider connection
- [ ] Integrated with messaging agent
- [ ] Cost monitoring configured

---

## 🎉 Ready to Use!

Your messaging agent now supports **Easy Setup**!

**Next Steps:**
1. Choose your provider (Claude/GPT/Bedrock)
2. Set up API key
3. Test the connection
4. Start chatting!

**Need Help?**
- See [README.md](README.md) for full documentation
- Provider docs: [llm_providers/](llm_providers/)
- Integration examples above

**Happy Chatting! 🚀✨**
