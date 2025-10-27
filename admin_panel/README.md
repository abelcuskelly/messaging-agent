# Admin Panel for Messaging Agent System

A comprehensive web-based administration panel for managing, monitoring, and configuring your AI messaging agent system.

## 🎯 Features

### 📊 Real-time Dashboard
- **Live Metrics**: Monitor conversations, active users, response times, and success rates
- **System Health**: Track API, database, cache, and model endpoint status
- **Conversation Volume**: 24-hour activity charts with hourly breakdowns
- **Recent Conversations**: View and manage ongoing customer interactions

### ⚙️ System Configuration
- **Model Management**: Switch between providers (Anthropic, OpenAI, Bedrock, Qwen)
- **Parameter Tuning**: Adjust temperature, max tokens, and other model settings
- **Rate Limiting**: Configure API rate limits and throttling
- **Auto-scaling**: Set min/max instances for automatic scaling
- **Cache Control**: Enable/disable caching and clear cache on demand

### 👥 User Management
- **Access Control**: Create and manage admin, operator, and viewer accounts
- **API Keys**: Generate and revoke API keys for different users
- **Permissions**: Fine-grained role-based access control
- **Activity Tracking**: Monitor user logins and actions

### 📈 Analytics & Insights
- **Conversation Analytics**: Deep dive into conversation patterns and trends
- **Performance Metrics**: Response times, success rates, error analysis
- **User Behavior**: Track user journeys and interaction patterns
- **Intent Analysis**: Understand most common customer requests
- **Export Reports**: Generate CSV/PDF reports for stakeholders

### 💳 Billing & Usage
- **Usage Tracking**: Monitor API calls, tokens, storage, and bandwidth
- **Cost Analysis**: Real-time cost calculations and projections
- **Budget Alerts**: Set spending limits and receive notifications
- **Usage History**: View historical usage patterns and trends

### 🔔 Alerts & Monitoring
- **Custom Alerts**: Configure alerts for error rates, response times, etc.
- **Multi-channel Notifications**: Email, Slack, SMS, and webhook alerts
- **Alert History**: Track triggered alerts and resolutions
- **Escalation Rules**: Define alert escalation paths

### 🧠 Model Management
- **Model Switching**: Seamlessly switch between different LLM providers
- **A/B Testing**: Run experiments with different models
- **Performance Comparison**: Compare model performance metrics
- **Version Control**: Track model versions and rollback if needed

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.8+
python --version

# Node.js (optional, for React frontend)
node --version

# Redis (for real-time data)
redis-server --version
```

### Installation

1. **Install Backend Dependencies**:
```bash
cd admin_panel/backend
pip install -r requirements.txt
```

2. **Set Environment Variables**:
```bash
# Create .env file
cat > .env << EOF
# Admin Authentication
ADMIN_TOKEN=your-secure-admin-token

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Google Cloud (optional)
GCP_PROJECT=your-project-id

# LLM Provider Settings
LLM_PROVIDER=anthropic
MODEL_NAME=claude-3-sonnet
TEMPERATURE=0.7
MAX_TOKENS=2000
RATE_LIMIT=100
EOF
```

3. **Start Redis**:
```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or using local Redis
redis-server
```

4. **Run the Admin Panel**:
```bash
# Start backend server
cd admin_panel/backend
python server.py

# Access at http://localhost:8000
```

5. **Open Frontend**:
```bash
# Open in browser
open admin_panel/frontend/index.html

# Or serve with Python
cd admin_panel/frontend
python -m http.server 8080
```

## 📝 API Documentation

### Authentication
All API endpoints require Bearer token authentication:
```javascript
headers: {
    'Authorization': 'Bearer YOUR_ADMIN_TOKEN'
}
```

### Key Endpoints

#### System Configuration
- `GET /api/config` - Get current configuration
- `PUT /api/config` - Update configuration
- `POST /api/system/restart` - Restart services
- `POST /api/system/clear-cache` - Clear cache

#### Analytics
- `GET /api/analytics/overview` - Dashboard overview
- `POST /api/analytics/conversations` - Detailed analytics
- `GET /api/conversations/recent` - Recent conversations

#### User Management
- `GET /api/users` - List all users
- `POST /api/users` - Create new user
- `DELETE /api/users/{id}` - Delete user

#### Billing
- `GET /api/billing/usage` - Current usage stats
- `GET /api/billing/history` - Historical usage

#### Alerts
- `GET /api/alerts` - List configured alerts
- `POST /api/alerts` - Create new alert
- `PUT /api/alerts/{id}` - Update alert

#### Models
- `GET /api/models` - Available models
- `POST /api/models/switch` - Switch active model

### WebSocket Events
Connect to `ws://localhost:8000/ws` for real-time updates:
```javascript
{
    "type": "metrics_update",
    "timestamp": "2024-01-01T00:00:00Z",
    "active_conversations": 42,
    "queue_size": 5,
    "response_time": 250
}
```

## 🎨 Customization

### Adding Custom Metrics
```python
# In server.py, add to get_analytics_overview()
custom_metric = await r.get("metrics:custom_metric") or 0
```

### Custom Alert Types
```python
# Define new alert in AlertConfig
class CustomAlert(AlertConfig):
    custom_field: str
    custom_threshold: float
```

### Extending the Dashboard
```javascript
// In index.html, add new chart
function addCustomChart(data) {
    new Chart(ctx, {
        type: 'bar',
        data: customData
    });
}
```

## 🔒 Security

### Best Practices
1. **Strong Admin Token**: Use a secure, randomly generated token
2. **HTTPS Only**: Always use HTTPS in production
3. **IP Whitelisting**: Restrict admin panel access by IP
4. **Audit Logging**: Log all admin actions
5. **MFA**: Enable multi-factor authentication

### Role-Based Access
```python
roles = {
    "admin": ["read", "write", "delete", "configure"],
    "operator": ["read", "write"],
    "viewer": ["read"]
}
```

## 📊 Monitoring the Admin Panel

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics Endpoint
```bash
curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/api/metrics
```

## 🚢 Production Deployment

### Using Docker
```dockerfile
# Dockerfile for admin panel
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Deploy to Cloud Run
```bash
# Build and deploy
gcloud run deploy admin-panel \
    --source . \
    --region us-central1 \
    --allow-unauthenticated
```

### Nginx Configuration
```nginx
server {
    listen 443 ssl;
    server_name admin.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🔧 Troubleshooting

### Common Issues

**WebSocket Connection Failed**
```bash
# Check Redis is running
redis-cli ping

# Check CORS settings
# Ensure frontend origin is allowed
```

**Authentication Errors**
```bash
# Verify token in .env
echo $ADMIN_TOKEN

# Check token in request headers
```

**No Data Showing**
```bash
# Check BigQuery permissions
gcloud auth application-default login

# Verify Redis has data
redis-cli keys "*"
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Chart.js Documentation](https://www.chartjs.org/)
- [TailwindCSS Documentation](https://tailwindcss.com/)
- [Redis Documentation](https://redis.io/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details
