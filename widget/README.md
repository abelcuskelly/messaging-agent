# 📱 Qwen Chat Widget - Integration Guide

## Overview

The Qwen Chat Widget is an **embeddable chat interface** that you can easily add to your company's website to connect visitors with your AI messaging agent.

---

## 🚀 Quick Start (3 Steps)

### **1. Include the Widget Script**

Add this to your website's `<head>` section:

```html
<script>
  window.qwenConfig = {
    apiUrl: 'https://your-api.com',
    apiKey: 'your-api-key',
    position: 'bottom-right',
    title: 'Chat with us',
    subtitle: 'Ask us anything'
  };
</script>
<script src="https://cdn.yoursite.com/widget/qwen-plugin.js"></script>
```

### **2. That's It!**

The chat widget will automatically appear on your website as a floating button.

### **3. Customize (Optional)**

Configure colors, position, messages, and more using the configuration options below.

---

## ⚙️ Configuration Options

### **Required Settings**

| Option | Type | Description |
|--------|------|-------------|
| `apiUrl` | string | Your API endpoint URL |
| `apiKey` | string | Your API authentication key |

### **Optional Settings**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `position` | string | `'bottom-right'` | Widget position: `'bottom-right'`, `'bottom-left'`, `'top-right'`, `'top-left'` |
| `title` | string | `'Chat with us'` | Chat window header title |
| `subtitle` | string | `'Ask us anything'` | Chat window header subtitle |
| `greeting` | string | `'Hi! How can we help you today?'` | Initial greeting message |
| `placeholder` | string | `'Type your message...'` | Input placeholder text |
| `primaryColor` | string | `'#667eea'` | Primary brand color |
| `secondaryColor` | string | `'#764ba2'` | Secondary brand color |
| `autoOpen` | boolean | `false` | Automatically open chat on page load |
| `showPoweredBy` | boolean | `true` | Show "Powered by Qwen" footer |

---

## 📋 Complete Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Website</title>
    
    <!-- Qwen Chat Widget -->
    <script>
        window.qwenConfig = {
            apiUrl: 'https://api.mycompany.com',
            apiKey: 'sk-your-api-key-here',
            
            // Customization
            position: 'bottom-right',
            title: 'Need help?',
            subtitle: 'Chat with our AI assistant',
            greeting: 'Welcome! How can we help you today?',
            placeholder: 'Ask us anything...',
            
            // Colors
            primaryColor: '#667eea',
            secondaryColor: '#764ba2',
            
            // Behavior
            autoOpen: false,
            showPoweredBy: true
        };
    </script>
    <script src="https://cdn.mycompany.com/widget/qwen-plugin.js"></script>
</head>
<body>
    <!-- Your website content -->
    <h1>Welcome to My Website</h1>
    <p>Chat widget will appear as a floating button.</p>
</body>
</html>
```

---

## 🎨 Customization Examples

### **Brand Colors**

```javascript
window.qwenConfig = {
    primaryColor: '#FF6B6B',    // Red
    secondaryColor: '#4ECDC4',   // Teal
    // ... other config
};
```

### **Different Positions**

```javascript
// Bottom-left corner
position: 'bottom-left'

// Top-right corner
position: 'top-right'

// Top-left corner
position: 'top-left'
```

### **Auto-Open Chat**

```javascript
autoOpen: true  // Opens automatically when page loads
```

### **Sports Ticketing**

```javascript
window.qwenConfig = {
    apiUrl: 'https://tickets.mysports.com/api',
    apiKey: 'sk-tickets-key',
    title: 'Ticket Assistant',
    subtitle: 'Ask about tickets, games, and seating',
    greeting: 'Hi! I can help you find tickets for upcoming games.',
    placeholder: 'What game are you interested in?'
};
```

---

## 📱 Mobile Responsive

The widget is **fully responsive** and works perfectly on:
- ✅ Desktop browsers
- ✅ Tablets
- ✅ Mobile phones

On mobile devices, the chat window automatically expands to full screen for better usability.

---

## 🔒 Security

### **API Key Protection**

Never expose your API key in client-side JavaScript!

**Option 1: Use a proxy endpoint**
```javascript
apiUrl: 'https://proxy.yourdomain.com/api/qwen'
// Your proxy server adds the API key server-side
```

**Option 2: Use short-lived tokens**
```javascript
apiKey: 'temporary-token-valid-for-1-hour'
// Generate new tokens server-side
```

**Option 3: Environment-specific config**
```javascript
apiUrl: '{{ API_URL }}',  // Injected by your CMS
apiKey: '{{ API_KEY }}'   // Injected by your CMS
```

### **HTTPS Required**

Always use HTTPS in production:
```javascript
apiUrl: 'https://api.yourdomain.com'  // ✅ Secure
// NOT: 'http://api.yourdomain.com'  // ❌ Insecure
```

---

## 🧪 Testing

### **Local Testing**

1. Start your API server locally:
   ```bash
   python api/main.py
   ```

2. Use local URL in config:
   ```javascript
   apiUrl: 'http://localhost:8000'
   ```

3. Open your website and test the widget.

### **Test Checklist**

- [ ] Widget appears on page load
- [ ] Toggle button works
- [ ] Can send messages
- [ ] Receives AI responses
- [ ] Mobile responsive
- [ ] Custom colors applied
- [ ] Custom messages display

---

## 📊 Analytics

The widget automatically tracks:
- Message count
- Conversation IDs
- Timestamps
- User interactions

Access via your API's analytics dashboard.

---

## 🛠️ Advanced Usage

### **Manual Initialization**

```javascript
// Load the widget script
const script = document.createElement('script');
script.src = 'chat-widget.js';
document.head.appendChild(script);

// Initialize when loaded
script.onload = function() {
    window.qwenWidget = new QwenChatWidget({
        apiUrl: 'https://your-api.com',
        apiKey: 'your-api-key'
    });
};
```

### **Custom Event Listeners**

```javascript
// Open/close events
document.addEventListener('qwen:open', () => {
    console.log('Chat opened');
});

document.addEventListener('qwen:close', () => {
    console.log('Chat closed');
});

// Message events
document.addEventListener('qwen:message', (event) => {
    console.log('Message sent:', event.detail);
});
```

### **Programmatic Control**

```javascript
// Open chat programmatically
window.qwenWidget.openChat();

// Close chat programmatically
window.qwenWidget.closeChat();

// Send message programmatically
window.qwenWidget.sendMessage();
```

---

## 🐛 Troubleshooting

### **Widget Not Appearing**

**Problem**: Chat widget doesn't show up
**Solutions**:
1. Check browser console for errors
2. Verify API URL is correct
3. Ensure script tag is in `<head>` section
4. Check for JavaScript conflicts

### **API Connection Errors**

**Problem**: Can't send messages
**Solutions**:
1. Verify API key is correct
2. Check API URL is reachable
3. Ensure CORS is enabled on API
4. Check network tab for 401/403 errors

### **Styling Issues**

**Problem**: Widget looks wrong
**Solutions**:
1. Clear browser cache
2. Check for CSS conflicts
3. Verify custom colors are valid hex codes
4. Test in incognito mode

---

## 📚 Additional Resources

- **API Documentation**: [README.md](../README.md)
- **Demo Portal**: `widget-demo/index.html`
- **Security Guide**: [SECURITY.md](../SECURITY.md)
- **Full Documentation**: [Twilio Setup](../TWILIO_SETUP.md)

---

## 🎉 You're Ready!

Your Qwen Chat Widget is now integrated into your website!

**Next Steps**:
1. Test the widget on your website
2. Customize colors and branding
3. Monitor analytics and usage
4. Iterate based on customer feedback

**Happy Chatting! 💬✨**
