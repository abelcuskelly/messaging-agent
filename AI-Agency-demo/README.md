# AI Agent Demo - Rationa

Interactive demo page showcasing the capabilities of Rationa's AI Messaging Agent for customer service and ticketing.

## Overview

This demo page allows visitors to experience Rationa's AI agent through realistic conversation scenarios:

1. **Simple Ticket Purchase** - Watch the AI help a customer buy Lakers tickets
2. **Seat Upgrade Service** - See intelligent upgrade suggestions
3. **Purchase + Upgrade** - Multi-step interaction demonstration
4. **General Inquiry** - Handle various customer questions

## Features

- **Live Scenarios**: Pre-configured realistic conversation flows
- **Interactive Chat Interface**: Modern, responsive design
- **Agent Capabilities Showcase**: Highlights key features
- **Performance Metrics**: Response times and capabilities
- **Responsive Design**: Works on all devices

## Deployment

### For AI-Agency Repository

Copy the demo files to your AI-Agency GitHub repository:

```bash
# From messaging agent directory
cd AI-Agency-demo

# Copy to AI-Agency repository
cp index.html /path/to/AI-Agency/
```

### GitHub Pages

The demo will automatically be available at:
```
https://abelcuskelly.github.io/AI-Agency/agent-demo/index.html
```

## Customization

### Adding New Scenarios

Edit `index.html` and add scenarios to the `scenarios` object:

```javascript
const scenarios = {
    5: {
        title: "New Scenario",
        messages: [
            {role: "agent", text: "Agent response..."},
            {role: "user", text: "User message..."}
        ]
    }
};
```

### Styling

The demo uses inline CSS for easy customization. Key sections:
- `.demo-container` - Main container
- `.demo-scenario` - Scenario cards
- `.chat-interface` - Chat UI

### API Integration

For live API integration, update the `sendMessage()` function:

```javascript
async function sendMessage() {
    const message = document.getElementById('userInput').value;
    addMessage('user', message);
    
    // Call real API
    const response = await fetch('https://your-api.com/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: message})
    });
    
    const data = await response.json();
    addMessage('agent', data.response);
}
```

## Integration with Main Site

Add a link to the demo from the main Rationa website:

```html
<a href="/agent-demo/index.html" class="demo-button">
    Try Live Demo
</a>
```

## Performance

- **Fast Loading**: Optimized HTML/CSS/JS
- **No Dependencies**: Pure vanilla JavaScript
- **Mobile Friendly**: Responsive design
- **Browser Compatible**: Works in all modern browsers

## License

© 2024 Rationa. All rights reserved.
