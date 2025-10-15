# 🔐 API Key Setup - Secure Configuration

**IMPORTANT**: This guide shows you how to safely add API keys without committing them to GitHub.

---

## ✅ Security Status

Your repository is already configured to protect secrets:
- ✅ `.gitignore` includes `.env*` (line 4)
- ✅ ALL `.env` files are automatically excluded from git
- ✅ Your keys will NEVER be committed to GitHub

---

## 🔑 Where to Add Your OpenAI API Key

### **Option 1: Create `.env` File** (Recommended)

```bash
# Navigate to project root
cd "/Users/abel/Desktop/Work/messaging agent"

# Create .env file (this file is already in .gitignore!)
cat > .env << 'EOF'
# OpenAI API Key for Evaluation System
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Optional: Override default model
EVAL_MODEL=gpt-4-turbo-preview

# Optional: Use Vertex AI instead
# EVAL_PROVIDER=vertexai
EOF

# Verify it's not tracked by git
git status .env
# Should show: "Untracked files" or not appear at all
```

### **Option 2: Add to Existing `.env`** (If you have one)

```bash
# Append to existing .env file
echo "OPENAI_API_KEY=sk-your-actual-openai-api-key-here" >> .env
```

### **Option 3: Export in Terminal** (Temporary)

```bash
# Set for current session only (lost when terminal closes)
export OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Verify it's set
echo $OPENAI_API_KEY
```

---

## 🔒 Security Verification

### **1. Check .gitignore**
```bash
# Verify .env is in .gitignore
grep "\.env" .gitignore
# Should show: .env*
```

### **2. Verify Not Tracked**
```bash
# Check git status
git status

# Your .env should NOT appear in:
# - "Changes to be committed"
# - "Changes not staged"
# It may appear under "Untracked files" - that's OK, it won't be committed
```

### **3. Test Git Add**
```bash
# This should NOT add .env
git add .env
# Git will ignore it due to .gitignore

# Verify
git status
# .env should NOT be in "Changes to be committed"
```

---

## 📝 Complete `.env` Template

Here's a complete `.env` file with all API keys (copy this template):

```bash
# ============================================
# CORE GOOGLE CLOUD CONFIGURATION
# ============================================
PROJECT_ID=your-gcp-project-id
REGION=us-central1
BUCKET_NAME=${PROJECT_ID}-vertex-ai-training
ENDPOINT_ID=your-vertex-endpoint-id

# ============================================
# OPENAI EVALUATION SYSTEM
# ============================================
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
EVAL_MODEL=gpt-4-turbo-preview
EVAL_PROVIDER=openai
MIN_EVAL_SCORE=0.80
MIN_PASS_RATE=0.85

# ============================================
# TICKET PLATFORM INTEGRATIONS
# ============================================
# StubHub
STUBHUB_API_KEY=your-stubhub-key
STUBHUB_API_SECRET=your-stubhub-secret
STUBHUB_ENV=production

# SeatGeek
SEATGEEK_CLIENT_ID=your-seatgeek-client-id
SEATGEEK_CLIENT_SECRET=your-seatgeek-secret

# Ticketmaster
TICKETMASTER_API_KEY=your-ticketmaster-key

# ============================================
# OPTIONAL SERVICES
# ============================================
# Authentication
API_KEY=your-api-authentication-key

# Redis
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Optimization Settings
MAX_CONTEXT_TOKENS=2000

# Monitoring
WANDB_API_KEY=your-wandb-key
LOG_LEVEL=INFO
```

---

## 🚨 NEVER DO THIS

### ❌ Don't Commit Keys Directly
```bash
# WRONG - Never do this
git add .env
git commit -m "Added API keys"  # Keys would be in git history forever!
```

### ❌ Don't Hardcode in Files
```python
# WRONG - Never hardcode keys
OPENAI_API_KEY = "sk-abc123..."  # Don't do this!

# RIGHT - Always use environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
```

### ❌ Don't Share .env Files
- Don't email `.env` files
- Don't paste in Slack/Discord
- Don't screenshot with keys visible

---

## ✅ Safe Practices

### **1. Use Environment Variables**
```python
import os

# Always load from environment
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    raise ValueError("OPENAI_API_KEY not set!")
```

### **2. Use python-dotenv** (Load .env automatically)
```python
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Now environment variables are available
api_key = os.getenv('OPENAI_API_KEY')
```

### **3. Google Secret Manager** (Production)
For production deployments, use Google Secret Manager:

```bash
# Store secret
gcloud secrets create openai-api-key \
  --data-file=- <<< "sk-your-key-here"

# Access in Cloud Run
gcloud run services update messaging-agent \
  --update-secrets=OPENAI_API_KEY=openai-api-key:latest
```

---

## 🎯 Your Action Items

### **Step 1: Create `.env` file** (Safe - already in .gitignore)
```bash
cd "/Users/abel/Desktop/Work/messaging agent"

# Create .env with your OpenAI key
echo "OPENAI_API_KEY=sk-your-actual-key-here" > .env
```

### **Step 2: Verify Security**
```bash
# Check it's ignored
git status | grep .env
# Should be empty or show as "Untracked" (not "Changes to be committed")

# Try to add it (should be ignored)
git add .env
git status
# Should NOT show .env in "Changes to be committed"
```

### **Step 3: Test Evaluation**
```bash
# Load .env and run eval
cd evals
python3 eval_suite.py
```

---

## 🔐 Key Rotation

If your key is ever compromised:

```bash
# 1. Delete from OpenAI dashboard
# 2. Generate new key
# 3. Update .env file
echo "OPENAI_API_KEY=sk-new-key-here" > .env

# 4. Update production secrets (if deployed)
gcloud secrets versions add openai-api-key \
  --data-file=- <<< "sk-new-key-here"
```

---

## 📋 Checklist

Before running evaluations:
- [ ] `.env` file created in project root
- [ ] `OPENAI_API_KEY=sk-...` added to `.env`
- [ ] Verified `.env` is in `.gitignore` ✅ (already done)
- [ ] Tested: `git add .env` doesn't stage it ✅
- [ ] Never committed keys to git ✅
- [ ] Ready to run evaluations!

---

## ✅ Your .gitignore Already Protects You

Line 4 of `.gitignore`:
```
.env*
```

This protects:
- `.env`
- `.env.local`
- `.env.production`
- `.env.development`
- `.env.anything`

**You're safe!** Just create `.env` and add your key. It will never be committed to GitHub.

---

## 🎯 Summary

**Where to add your OpenAI API key:**
1. Create file: `.env` in project root
2. Add line: `OPENAI_API_KEY=sk-your-key-here`
3. Save file
4. **Already protected** by `.gitignore` ✅

**Then run:**
```bash
cd evals
python3 eval_suite.py
```

Your key is safe and the evaluation system will work! 🚀
