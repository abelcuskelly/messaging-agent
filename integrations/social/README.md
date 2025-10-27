# 📱 Social Media Integration

## Overview

Connect your messaging agent to social media platforms to engage with customers across Twitter, LinkedIn, and Facebook (including Instagram).

---

## 🚀 Quick Start

### **1. Configure Social Media Credentials**

Add to your `.env` file:

```bash
# Twitter/X
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# LinkedIn
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token

# Facebook
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_account_id
```

### **2. Initialize the Manager**

```python
from integrations.social.manager import SocialMediaManager

# Initialize all platforms
manager = SocialMediaManager()

# Check which platforms are authenticated
stats = manager.get_unified_stats()
print(f"Active platforms: {stats['active_platforms']}")
```

### **3. Get Messages from All Platforms**

```python
# Get messages from all platforms
messages = manager.get_all_messages(limit_per_platform=20)

# Filter by platform
twitter_messages = [m for m in messages if m.platform == 'twitter']
linkedin_messages = [m for m in messages if m.platform == 'linkedin']
```

### **4. Send Messages**

```python
# Send a message on a specific platform
response = manager.get_platform('twitter').send_message(
    to='@username',
    message='Thanks for reaching out! How can I help?'
)

# Auto-respond with AI
response = manager.auto_respond_to_message('twitter', message_id, user_id)
```

---

## 📋 Available Features

### **Multi-Platform Support**

- ✅ **Twitter/X**: Mentions, DMs, tweets, hashtag monitoring
- ✅ **LinkedIn**: Professional messaging, posts, connection requests
- ✅ **Facebook**: Messenger, Instagram DMs, page comments

### **Core Functionality**

- 📨 **Get Messages**: Retrieve messages from all platforms
- 💬 **Send Messages**: Send messages and replies
- 🤖 **Auto-Respond**: AI-powered automatic responses
- 📊 **Statistics**: Platform-specific and unified stats
- 🔔 **Monitoring**: Brand mention tracking across platforms
- 🎯 **Campaigns**: Post to multiple platforms simultaneously
- 👋 **Welcome Messages**: Automated welcome for new customers

---

## 🔌 API Endpoints

### **Get Available Platforms**

```bash
GET /social/platforms
```

**Response:**
```json
{
  "platforms": ["twitter", "linkedin", "facebook"],
  "count": 3
}
```

### **Get All Messages**

```bash
GET /social/messages?limit=20&platform=twitter
```

**Response:**
```json
{
  "messages": [
    {
      "platform": "twitter",
      "message_id": "msg_123",
      "user_id": "user_456",
      "username": "customer",
      "text": "Need help with tickets",
      "timestamp": "2024-01-15T10:00:00Z"
    }
  ],
  "count": 1
}
```

### **Send Message**

```bash
POST /social/send
{
  "platform": "twitter",
  "to": "@username",
  "message": "Hi! How can I help you?"
}
```

**Response:**
```json
{
  "success": true,
  "platform": "twitter",
  "message_id": "msg_789",
  "timestamp": "2024-01-15T10:05:00Z"
}
```

### **Reply to Message**

```bash
POST /social/reply/{platform}/{message_id}
{
  "reply_text": "Great! I can help you with that."
}
```

### **Auto-Respond with AI**

```bash
POST /social/auto-respond/{platform}
?message_id=msg_123&user_id=user_456
```

### **Monitor Brand Mentions**

```bash
GET /social/mentions/lakers
```

**Response:**
```json
{
  "keyword": "lakers",
  "mentions": [
    {
      "platform": "twitter",
      "username": "@fan123",
      "text": "Looking for Lakers tickets!",
      "timestamp": "2024-01-15T10:00:00Z"
    }
  ],
  "count": 1
}
```

### **Create Social Media Campaign**

```bash
POST /social/campaign
{
  "message": "New ticket options available!",
  "platforms": ["twitter", "facebook"]
}
```

**Response:**
```json
{
  "success": true,
  "campaign_message": "New ticket options available!",
  "successful_platforms": ["twitter", "facebook"],
  "failed_platforms": [],
  "platforms_posted": 2,
  "platforms_failed": 0
}
```

### **Get Statistics**

```bash
# Platform-specific stats
GET /social/stats/twitter

# Unified stats
GET /social/stats
```

**Response:**
```json
{
  "total_platforms": 3,
  "active_platforms": 2,
  "platform_stats": {
    "twitter": {
      "platform": "twitter",
      "is_authenticated": true,
      "total_messages": 150,
      "recent_messages": 20
    }
  }
}
```

### **Check Platform Health**

```bash
GET /social/health/twitter
```

**Response:**
```json
{
  "platform": "twitter",
  "status": "healthy",
  "authenticated": true
}
```

---

## 🎨 Usage Examples

### **Send Welcome Message**

```python
# Send automated welcome on Twitter
response = manager.send_welcome_message('twitter', user_id)

# Send custom welcome on LinkedIn
response = manager.send_welcome_message(
    'linkedin',
    user_id,
    custom_message="Welcome! I can help with corporate ticket packages."
)
```

### **Monitor Brand Mentions**

```python
# Track mentions of your brand
mentions = manager.monitor_brand_mentions('yourbrand')

# Respond to each mention
for mention in mentions:
    response = manager.auto_respond_to_message(
        mention.platform,
        mention.message_id,
        mention.user_id
    )
```

### **Create Social Media Campaign**

```python
# Post announcement across all platforms
results = manager.create_social_campaign(
    "🎉 New ticket season starting soon! Special early bird pricing available.",
    platforms=['twitter', 'linkedin', 'facebook']
)

print(f"Posted to {results['platforms_posted']} platforms")
```

### **Get Platform-Specific Messages**

```python
# Get only Twitter messages
twitter_messages = manager.get_platform_messages('twitter', limit=50)

# Get only LinkedIn messages
linkedin_messages = manager.get_platform_messages('linkedin', limit=20)
```

### **Unified Statistics**

```python
# Get stats for all platforms
stats = manager.get_unified_stats()

for platform, data in stats['platform_stats'].items():
    print(f"{platform}: {data['total_messages']} messages")
```

---

## 🔐 Authentication Setup

### **Twitter/X**

1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Create an app and get:
   - API Key
   - API Secret
   - Access Token
   - Access Token Secret
   - Bearer Token

### **LinkedIn**

1. Go to [developer.linkedin.com](https://developer.linkedin.com)
2. Create an app and get:
   - Client ID
   - Client Secret
   - Access Token (OAuth 2.0)

### **Facebook**

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create an app and page
3. Get:
   - App ID
   - App Secret
   - Page Access Token

---

## 🔧 Advanced Configuration

### **Platform-Specific Validation**

Each platform has different message limits:

- **Twitter**: 280 characters
- **LinkedIn**: 3,000 characters
- **Facebook**: 8,000 characters

The manager automatically validates messages before sending.

### **Media Upload**

```python
# Upload media to Twitter
twitter = manager.get_platform('twitter')
media_id = twitter.upload_media('/path/to/image.jpg')

# Tweet with media
twitter.tweet("Check out our new ticket options!", media_ids=[media_id])
```

### **Error Handling**

All methods return structured `SocialResponse` objects:

```python
response = manager.send_message('twitter', 'user', 'Hello')

if response.success:
    print(f"Message sent: {response.message_id}")
else:
    print(f"Error: {response.error}")
```

---

## 🐛 Troubleshooting

### **Platform Not Authenticated**

**Problem**: Platform status shows "not_authenticated"

**Solution**:
1. Check environment variables are set
2. Verify credentials are correct
3. Check token expiration
4. Re-authenticate the platform

### **Message Sending Fails**

**Problem**: `SocialResponse.success = False`

**Solutions**:
1. Check message length limits
2. Verify user ID format is correct
3. Check if user has blocked your account
4. Review error message in `SocialResponse.error`

### **No Messages Retrieved**

**Problem**: `get_mentions()` returns empty list

**Solutions**:
1. Verify platform is authenticated
2. Check API rate limits
3. Verify webhook configurations
4. Check if there are actually new messages

---

## 📊 Monitoring & Analytics

### **Track Platform Usage**

```python
# Get unified statistics
stats = manager.get_unified_stats()

print(f"Total Platforms: {stats['total_platforms']}")
print(f"Active Platforms: {stats['active_platforms']}")

for platform, data in stats['platform_stats'].items():
    print(f"{platform}: {data['total_messages']} total messages")
```

### **Monitor Response Times**

The manager tracks:
- Message sending success rate
- Response time per platform
- Error rates
- Active conversation count

---

## ✅ Best Practices

1. **Rate Limiting**: Respect platform API rate limits
2. **Message Length**: Check character limits before sending
3. **Authentication**: Keep tokens refreshed
4. **Error Handling**: Always check `success` field in responses
5. **Monitoring**: Use unified stats to track platform health
6. **Testing**: Test in development before production deployment

---

## 🎉 You're Ready!

Your messaging agent can now connect with customers across:

- ✅ **Twitter/X** - Public and private messaging
- ✅ **LinkedIn** - Professional networking
- ✅ **Facebook & Instagram** - Social and visual platforms

**Next Steps**:
1. Configure your API credentials
2. Test each platform
3. Set up automated responses
4. Monitor brand mentions
5. Create your first social media campaign

**Happy Social Messaging! 📱✨**
