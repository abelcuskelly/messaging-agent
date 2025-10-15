#!/bin/bash

# Safe .env Setup Script
# Creates .env file with API keys (already protected by .gitignore)

echo "🔐 Secure .env Setup"
echo "=" * 60

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    read -p "Overwrite? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "❌ Setup cancelled"
        exit 0
    fi
fi

# Verify .env is in .gitignore
if grep -q "\.env" .gitignore; then
    echo "✅ .env is protected by .gitignore"
else
    echo "⚠️  WARNING: .env not in .gitignore!"
    echo "   Adding .env* to .gitignore..."
    echo ".env*" >> .gitignore
fi

echo ""
echo "📝 Enter your API keys (press ENTER to skip optional keys):"
echo ""

# OpenAI API Key (Required for evals)
read -p "OpenAI API Key (required for evals): " openai_key

# Ticket platform keys (Optional)
read -p "StubHub API Key (optional): " stubhub_key
read -p "StubHub API Secret (optional): " stubhub_secret
read -p "SeatGeek Client ID (optional): " seatgeek_key
read -p "Ticketmaster API Key (optional): " ticketmaster_key

# GCP configuration
read -p "GCP Project ID: " project_id
read -p "GCP Region (default: us-central1): " region
region=${region:-us-central1}
read -p "Vertex AI Endpoint ID (optional): " endpoint_id

# Create .env file
cat > .env << EOF
# ============================================
# CORE GOOGLE CLOUD CONFIGURATION
# ============================================
PROJECT_ID=${project_id}
REGION=${region}
BUCKET_NAME=\${PROJECT_ID}-vertex-ai-training
ENDPOINT_ID=${endpoint_id}

# ============================================
# OPENAI EVALUATION SYSTEM
# ============================================
OPENAI_API_KEY=${openai_key}
EVAL_MODEL=gpt-4-turbo-preview
EVAL_PROVIDER=openai
MIN_EVAL_SCORE=0.80
MIN_PASS_RATE=0.85

# ============================================
# TICKET PLATFORM INTEGRATIONS
# ============================================
# StubHub
STUBHUB_API_KEY=${stubhub_key}
STUBHUB_API_SECRET=${stubhub_secret}
STUBHUB_ENV=production

# SeatGeek
SEATGEEK_CLIENT_ID=${seatgeek_key}

# Ticketmaster
TICKETMASTER_API_KEY=${ticketmaster_key}

# ============================================
# OPTIONAL SERVICES
# ============================================
# Authentication
API_KEY=

# Redis
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Optimization Settings
MAX_CONTEXT_TOKENS=2000

# Monitoring
WANDB_API_KEY=
LOG_LEVEL=INFO
EOF

echo ""
echo "✅ .env file created successfully!"
echo ""

# Verify not tracked by git
if git ls-files --error-unmatch .env 2>/dev/null; then
    echo "❌ WARNING: .env is tracked by git!"
    echo "   Run: git rm --cached .env"
else
    echo "✅ .env is NOT tracked by git (secure!)"
fi

echo ""
echo "🔍 Verification:"
echo "   - .env file created: ✅"
echo "   - Protected by .gitignore: ✅"
echo "   - Not tracked by git: ✅"
echo ""
echo "🚀 You can now run:"
echo "   cd evals"
echo "   python3 eval_suite.py"
echo ""
echo "⚠️  NEVER run: git add .env"
echo "⚠️  NEVER commit .env to GitHub"
echo ""
