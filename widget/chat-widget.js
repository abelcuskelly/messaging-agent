/**
 * Qwen Messaging Agent - Embeddable Chat Widget
 * Easy integration for company websites
 */

class QwenChatWidget {
    constructor(config = {}) {
        // Default configuration
        this.config = {
            apiUrl: config.apiUrl || 'https://your-api.com',
            apiKey: config.apiKey || '',
            position: config.position || 'bottom-right',
            title: config.title || 'Chat with us',
            subtitle: config.subtitle || 'Ask us anything about tickets',
            primaryColor: config.primaryColor || '#667eea',
            secondaryColor: config.secondaryColor || '#764ba2',
            showPoweredBy: config.showPoweredBy !== false,
            autoOpen: config.autoOpen || false,
            greeting: config.greeting || 'Hi! How can we help you today?',
            placeholder: config.placeholder || 'Type your message...',
            ...config
        };
        
        this.isOpen = false;
        this.messages = [];
        this.conversationId = null;
        
        // Initialize
        this.init();
    }
    
    init() {
        // Create widget container
        this.createWidget();
        
        // Load initial messages
        if (this.config.greeting) {
            this.addMessage(this.config.greeting, 'system');
        }
    }
    
    createWidget() {
        // Create main container
        const container = document.createElement('div');
        container.id = 'qwen-chat-widget';
        container.innerHTML = this.getWidgetHTML();
        document.body.appendChild(container);
        
        // Add styles
        this.injectStyles();
        
        // Attach event listeners
        this.attachEventListeners();
        
        // Show/hide based on autoOpen
        if (this.config.autoOpen) {
            this.openChat();
        }
    }
    
    getWidgetHTML() {
        return `
            <!-- Chat Toggle Button -->
            <div class="qwen-toggle" id="qwen-toggle">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
            </div>
            
            <!-- Chat Window -->
            <div class="qwen-chat" id="qwen-chat" style="display: none;">
                <!-- Header -->
                <div class="qwen-header">
                    <div class="qwen-header-content">
                        <div class="qwen-status">
                            <span class="qwen-status-dot"></span>
                            <span>Online</span>
                        </div>
                        <h3>${this.config.title}</h3>
                        <p>${this.config.subtitle}</p>
                    </div>
                    <button class="qwen-close" id="qwen-close">×</button>
                </div>
                
                <!-- Messages -->
                <div class="qwen-messages" id="qwen-messages">
                    <div class="qwen-message qwen-system">
                        ${this.config.greeting}
                    </div>
                </div>
                
                <!-- Input -->
                <div class="qwen-input-container">
                    <input 
                        type="text" 
                        id="qwen-input" 
                        class="qwen-input" 
                        placeholder="${this.config.placeholder}"
                        autocomplete="off"
                    />
                    <button class="qwen-send" id="qwen-send">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="22" y1="2" x2="11" y2="13"></line>
                            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }
    
    injectStyles() {
        const style = document.createElement('style');
        style.textContent = this.getWidgetCSS();
        document.head.appendChild(style);
    }
    
    getWidgetCSS() {
        const positionStyles = this.getPositionStyles();
        
        return `
            #qwen-chat-widget {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                position: fixed;
                ${positionStyles}
                z-index: 999999;
            }
            
            /* Toggle Button */
            .qwen-toggle {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, ${this.config.primaryColor} 0%, ${this.config.secondaryColor} 100%);
                box-shadow: 0 5px 20px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .qwen-toggle:hover {
                transform: scale(1.1);
                box-shadow: 0 8px 30px rgba(0,0,0,0.4);
            }
            
            .qwen-toggle svg {
                color: white;
                width: 28px;
                height: 28px;
            }
            
            /* Chat Window */
            .qwen-chat {
                width: 380px;
                height: 600px;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                animation: slideUp 0.3s;
            }
            
            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            /* Header */
            .qwen-header {
                background: linear-gradient(135deg, ${this.config.primaryColor} 0%, ${this.config.secondaryColor} 100%);
                color: white;
                padding: 20px;
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
            }
            
            .qwen-header-content h3 {
                margin: 0 0 5px 0;
                font-size: 1.2em;
            }
            
            .qwen-header-content p {
                margin: 0;
                opacity: 0.9;
                font-size: 0.9em;
            }
            
            .qwen-status {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 0.85em;
                margin-bottom: 10px;
            }
            
            .qwen-status-dot {
                width: 8px;
                height: 8px;
                background: #4ade80;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .qwen-close {
                background: transparent;
                border: none;
                color: white;
                font-size: 28px;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.2s;
            }
            
            .qwen-close:hover {
                transform: scale(1.2);
            }
            
            /* Messages */
            .qwen-messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                background: #f8f9fa;
            }
            
            .qwen-message {
                margin-bottom: 15px;
                animation: fadeIn 0.3s;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .qwen-message-user {
                text-align: right;
            }
            
            .qwen-message-user .qwen-bubble {
                background: linear-gradient(135deg, ${this.config.primaryColor} 0%, ${this.config.secondaryColor} 100%);
                color: white;
                display: inline-block;
                padding: 12px 16px;
                border-radius: 18px 18px 4px 18px;
                max-width: 80%;
            }
            
            .qwen-message-agent {
                text-align: left;
            }
            
            .qwen-message-agent .qwen-bubble {
                background: white;
                color: #333;
                display: inline-block;
                padding: 12px 16px;
                border-radius: 18px 18px 18px 4px;
                max-width: 80%;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .qwen-message-system {
                text-align: center;
                color: #666;
                font-size: 0.9em;
                font-style: italic;
                padding: 10px;
            }
            
            /* Input */
            .qwen-input-container {
                padding: 15px;
                background: white;
                border-top: 1px solid #e9ecef;
                display: flex;
                gap: 10px;
            }
            
            .qwen-input {
                flex: 1;
                padding: 12px 15px;
                border: 2px solid #e9ecef;
                border-radius: 25px;
                font-size: 0.95em;
                outline: none;
                transition: border-color 0.3s;
            }
            
            .qwen-input:focus {
                border-color: ${this.config.primaryColor};
            }
            
            .qwen-send {
                background: linear-gradient(135deg, ${this.config.primaryColor} 0%, ${this.config.secondaryColor} 100%);
                border: none;
                border-radius: 50%;
                width: 45px;
                height: 45px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            .qwen-send:hover {
                transform: scale(1.1);
            }
            
            .qwen-send svg {
                color: white;
            }
            
            /* Powered by */
            .qwen-powered-by {
                padding: 10px;
                text-align: center;
                font-size: 0.75em;
                color: #999;
                border-top: 1px solid #e9ecef;
            }
            
            .qwen-powered-by a {
                color: ${this.config.primaryColor};
                text-decoration: none;
            }
            
            .qwen-powered-by a:hover {
                text-decoration: underline;
            }
            
            /* Responsive */
            @media (max-width: 480px) {
                .qwen-chat {
                    width: 100vw;
                    height: 100vh;
                    border-radius: 0;
                }
            }
            
            /* Scrollbar */
            .qwen-messages::-webkit-scrollbar {
                width: 6px;
            }
            
            .qwen-messages::-webkit-scrollbar-track {
                background: transparent;
            }
            
            .qwen-messages::-webkit-scrollbar-thumb {
                background: #cbd5e0;
                border-radius: 3px;
            }
            
            .qwen-messages::-webkit-scrollbar-thumb:hover {
                background: #a0aec0;
            }
        `;
    }
    
    getPositionStyles() {
        const positions = {
            'bottom-right': 'bottom: 20px; right: 20px;',
            'bottom-left': 'bottom: 20px; left: 20px;',
            'top-right': 'top: 20px; right: 20px;',
            'top-left': 'top: 20px; left: 20px;'
        };
        return positions[this.config.position] || positions['bottom-right'];
    }
    
    attachEventListeners() {
        // Toggle button
        const toggle = document.getElementById('qwen-toggle');
        toggle.addEventListener('click', () => this.toggleChat());
        
        // Close button
        const close = document.getElementById('qwen-close');
        close.addEventListener('click', () => this.closeChat());
        
        // Send button
        const sendBtn = document.getElementById('qwen-send');
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Input enter key
        const input = document.getElementById('qwen-input');
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }
    
    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }
    
    openChat() {
        document.getElementById('qwen-chat').style.display = 'flex';
        document.getElementById('qwen-toggle').style.display = 'none';
        this.isOpen = true;
        
        // Focus input
        setTimeout(() => {
            document.getElementById('qwen-input').focus();
        }, 100);
    }
    
    closeChat() {
        document.getElementById('qwen-chat').style.display = 'none';
        document.getElementById('qwen-toggle').style.display = 'flex';
        this.isOpen = false;
    }
    
    addMessage(text, type = 'agent') {
        const messagesContainer = document.getElementById('qwen-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `qwen-message qwen-${type}`;
        
        if (type === 'system') {
            messageDiv.textContent = text;
        } else {
            const bubble = document.createElement('div');
            bubble.className = 'qwen-bubble';
            bubble.textContent = text;
            messageDiv.appendChild(bubble);
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.messages.push({ text, type, timestamp: new Date() });
    }
    
    async sendMessage() {
        const input = document.getElementById('qwen-input');
        const text = input.value.trim();
        
        if (!text) return;
        
        // Add user message
        this.addMessage(text, 'user');
        input.value = '';
        
        // Show typing indicator
        const typingId = this.addTypingIndicator();
        
        try {
            // Send to API
            const response = await fetch(`${this.config.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.config.apiKey
                },
                body: JSON.stringify({
                    message: text,
                    conversation_id: this.conversationId
                })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator(typingId);
            
            // Add agent response
            this.addMessage(data.response, 'agent');
            
            // Store conversation ID
            if (data.conversation_id) {
                this.conversationId = data.conversation_id;
            }
        } catch (error) {
            // Remove typing indicator
            this.removeTypingIndicator(typingId);
            
            // Show error
            this.addMessage('Sorry, there was an error. Please try again.', 'agent');
            console.error('Chat error:', error);
        }
    }
    
    addTypingIndicator() {
        const messagesContainer = document.getElementById('qwen-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'qwen-message qwen-agent qwen-typing';
        typingDiv.id = 'qwen-typing';
        typingDiv.innerHTML = '<div class="qwen-bubble">Thinking...</div>';
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return 'qwen-typing';
    }
    
    removeTypingIndicator(id) {
        const element = document.getElementById(id);
        if (element) {
            element.remove();
        }
    }
}

// Auto-initialize if qwenConfig is defined
if (typeof window !== 'undefined' && window.qwenConfig) {
    window.qwenWidget = new QwenChatWidget(window.qwenConfig);
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QwenChatWidget;
}
