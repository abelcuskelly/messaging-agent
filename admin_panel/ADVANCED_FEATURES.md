# Advanced Admin Panel Features

Enterprise-grade features for sophisticated monitoring, automation, and integrations.

## 🎨 Custom Dashboards

Create personalized dashboards tailored to your specific needs.

### Features
- **Drag-and-Drop Interface**: Visual dashboard builder
- **Widget Library**: Metrics, charts, tables, maps, and custom widgets
- **Templates**: Pre-built dashboards for executives, operations, and customer support
- **Data Sources**: Connect to conversations, metrics, users, and billing data
- **Auto-refresh**: Configurable refresh intervals for real-time data
- **Sharing**: Public or private dashboards

### Quick Start

```python
import httpx

# Create a custom dashboard
dashboard = {
    "id": "my-dashboard",
    "name": "Sales Dashboard",
    "description": "Track sales conversations and conversions",
    "owner": "admin@company.com",
    "widgets": [
        {
            "id": "widget-1",
            "type": "metric",
            "title": "Total Sales Conversations",
            "position": {"x": 0, "y": 0, "width": 3, "height": 2},
            "data_source": "conversations",
            "config": {"metric": "total", "filter": {"intent": "purchase"}},
            "refresh_interval": 30
        }
    ],
    "layout": "grid",
    "is_public": False
}

response = httpx.post(
    "http://localhost:8000/api/dashboards",
    json=dashboard,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### Available Templates

1. **Executive Dashboard**: High-level metrics for leadership
2. **Operations Dashboard**: System health and performance
3. **Customer Support Dashboard**: Active conversations and insights

## 🔔 Webhook Integrations

Configure webhooks to receive real-time notifications for system events.

### Supported Events
- `conversation_started` - New conversation initiated
- `conversation_completed` - Conversation finished
- `message_received` - Incoming message
- `message_sent` - Outgoing message
- `error_occurred` - System error
- `alert_triggered` - Alert threshold exceeded
- `model_switched` - Model configuration changed
- `user_created` - New user account
- `threshold_exceeded` - Metric threshold breach

### Setup

```python
webhook = {
    "id": "webhook-1",
    "name": "Slack Integration",
    "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "events": {
        "conversation_started": True,
        "error_occurred": True,
        "alert_triggered": True
    },
    "secret": "your-secret-key",
    "headers": {
        "Custom-Header": "value"
    },
    "enabled": True,
    "retry_count": 3,
    "timeout": 30
}

response = httpx.post(
    "http://localhost:8000/api/webhooks",
    json=webhook,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### Security

Webhooks include HMAC signatures for verification:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    computed = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed, signature)
```

## 📊 Automated Reports

Schedule automated reports for stakeholders.

### Features
- **Multiple Formats**: PDF, CSV, Excel, HTML, JSON
- **Flexible Scheduling**: Hourly, daily, weekly, monthly
- **Email Delivery**: Auto-send to recipients
- **Custom Metrics**: Choose specific data to include
- **Charts & Tables**: Visual and tabular data
- **Filtering**: Date ranges and custom filters

### Create a Report

```python
report = {
    "id": "weekly-report",
    "name": "Weekly Performance Report",
    "description": "Weekly summary of system performance",
    "frequency": "weekly",  # hourly, daily, weekly, monthly
    "format": "pdf",  # pdf, csv, excel, html, json
    "recipients": [
        "ceo@company.com",
        "cto@company.com"
    ],
    "include_charts": True,
    "include_tables": True,
    "metrics": [
        "conversations",
        "users",
        "performance",
        "billing"
    ],
    "filters": {
        "min_conversation_count": 10
    },
    "enabled": True
}

response = httpx.post(
    "http://localhost:8000/api/reports",
    json=report,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### Report Scheduling

Reports automatically run based on frequency:
- **Hourly**: On the hour
- **Daily**: 9 AM daily
- **Weekly**: Monday 9 AM
- **Monthly**: 1st day of month, 9 AM

### Manual Generation

```python
# Generate report immediately
response = httpx.post(
    "http://localhost:8000/api/reports/weekly-report/generate",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

## 🔗 Business Tool Integrations

Connect with your existing business tools for seamless workflows.

### Supported Platforms

1. **Slack** - Team notifications
2. **PagerDuty** - Incident management
3. **Microsoft Teams** - Team collaboration
4. **Discord** - Community engagement
5. **Jira** - Issue tracking
6. **Datadog** - Monitoring and analytics

### Slack Integration

```python
# Configure Slack
slack_config = {
    "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK",
    "channel": "#alerts",
    "username": "Messaging Agent Bot",
    "icon_emoji": ":robot_face:",
    "mention_on_critical": True,
    "mention_users": ["U123456", "U789012"]
}

httpx.post(
    "http://localhost:8000/api/integrations/slack/configure",
    json=slack_config,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

# Send notification
httpx.post(
    "http://localhost:8000/api/integrations/slack/notify",
    params={
        "title": "High Error Rate Detected",
        "message": "Error rate exceeded 5% threshold",
        "severity": "warning"
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### PagerDuty Integration

```python
# Configure PagerDuty
pagerduty_config = {
    "integration_key": "YOUR_INTEGRATION_KEY",
    "service_id": "SERVICE_ID",
    "escalation_policy": "POLICY_ID",
    "auto_resolve": True
}

httpx.post(
    "http://localhost:8000/api/integrations/pagerduty/configure",
    json=pagerduty_config,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

# Create incident
httpx.post(
    "http://localhost:8000/api/integrations/pagerduty/incident",
    params={
        "title": "System Down",
        "description": "API service is not responding",
        "severity": "critical"
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### Microsoft Teams Integration

```python
# Configure Teams
teams_config = {
    "webhook_url": "https://outlook.office.com/webhook/YOUR/WEBHOOK",
    "channel_id": "CHANNEL_ID",
    "mention_on_critical": True
}

httpx.post(
    "http://localhost:8000/api/integrations/teams/configure",
    json=teams_config,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### Broadcast Alerts

Send alerts to all configured platforms simultaneously:

```python
httpx.post(
    "http://localhost:8000/api/integrations/broadcast",
    json={
        "title": "System Alert",
        "message": "Database connection lost",
        "severity": "critical",
        "details": {
            "component": "database",
            "error": "Connection timeout",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

## 📱 Mobile App

Native iOS and Android apps for admin panel access.

### Features
- **Real-time Dashboard**: View metrics on mobile
- **Push Notifications**: Receive alerts instantly
- **Conversation Monitoring**: View active conversations
- **System Controls**: Restart services, clear cache
- **Quick Actions**: Common administrative tasks
- **Offline Mode**: Cache data for offline viewing

### Installation

```bash
# iOS
cd admin_panel/mobile
npm install
cd ios && pod install && cd ..
npm run ios

# Android
npm run android
```

### Configuration

```typescript
// Update API endpoint
const API_BASE_URL = 'https://your-api.com/api';

// Set auth token (use secure storage)
import AsyncStorage from '@react-native-async-storage/async-storage';
await AsyncStorage.setItem('admin_token', 'YOUR_TOKEN');
```

## 🔒 Security Best Practices

### API Authentication
- Use strong, randomly generated admin tokens
- Rotate tokens regularly
- Store tokens securely (environment variables, secret managers)
- Use HTTPS only in production

### Webhook Security
- Always verify HMAC signatures
- Use unique secrets per webhook
- Implement rate limiting
- Monitor for suspicious activity

### Integration Security
- Limit permissions to minimum required
- Use service accounts where possible
- Audit integration access regularly
- Revoke unused integrations

## 📈 Performance Optimization

### Caching Strategy
- Cache dashboard data with TTL
- Use Redis for real-time metrics
- Implement query result caching
- Cache webhook delivery status

### Database Optimization
- Index frequently queried fields
- Use time-series partitioning
- Implement data retention policies
- Regular vacuum/optimize operations

### API Rate Limiting
- Set per-user rate limits
- Implement sliding window algorithm
- Use Redis for distributed rate limiting
- Return 429 status with retry-after header

## 🔧 Troubleshooting

### Webhooks Not Delivering
1. Check webhook URL is accessible
2. Verify HMAC secret is correct
3. Check firewall/security group rules
4. Review webhook logs for errors
5. Test with webhook testing tools

### Reports Not Generating
1. Verify SMTP credentials
2. Check recipient email addresses
3. Review report scheduler logs
4. Ensure data sources are accessible
5. Check disk space for temporary files

### Mobile App Issues
1. Verify API endpoint is correct
2. Check authentication token
3. Ensure device has network connectivity
4. Clear app cache and restart
5. Review mobile app logs

## 📚 API Reference

### Custom Dashboards

**Endpoints:**
- `POST /api/dashboards` - Create dashboard
- `GET /api/dashboards` - List dashboards
- `GET /api/dashboards/{id}` - Get dashboard
- `PUT /api/dashboards/{id}` - Update dashboard
- `DELETE /api/dashboards/{id}` - Delete dashboard
- `GET /api/dashboards/templates` - Get templates

### Webhooks

**Endpoints:**
- `POST /api/webhooks` - Create webhook
- `GET /api/webhooks` - List webhooks
- `GET /api/webhooks/{id}` - Get webhook
- `DELETE /api/webhooks/{id}` - Delete webhook
- `POST /api/webhooks/{id}/test` - Test webhook
- `GET /api/webhooks/{id}/stats` - Get statistics

### Reports

**Endpoints:**
- `POST /api/reports` - Create report
- `GET /api/reports` - List reports
- `GET /api/reports/{id}` - Get report
- `DELETE /api/reports/{id}` - Delete report
- `POST /api/reports/{id}/generate` - Generate now

### Integrations

**Endpoints:**
- `POST /api/integrations/{type}/configure` - Configure
- `POST /api/integrations/{type}/test` - Test
- `GET /api/integrations` - List all
- `POST /api/integrations/slack/notify` - Slack notification
- `POST /api/integrations/pagerduty/incident` - PagerDuty incident
- `POST /api/integrations/broadcast` - Broadcast alert

## 📄 License

MIT License - See LICENSE file for details
