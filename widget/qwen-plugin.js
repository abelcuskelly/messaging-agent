/**
 * Qwen Messaging Agent - Easy Integration Plugin
 * Include this script on your website to add the chat widget
 */

(function() {
    'use strict';
    
    // Load chat widget
    const script = document.createElement('script');
    script.src = 'chat-widget.js';
    script.async = true;
    document.head.appendChild(script);
    
    // Initialize when loaded
    script.onload = function() {
        if (window.qwenConfig) {
            window.qwenWidget = new QwenChatWidget(window.qwenConfig);
            console.log('✅ Qwen Chat Widget loaded!');
        } else {
            console.warn('⚠️  Qwen Chat Widget: No configuration found. Please define qwenConfig.');
        }
    };
    
})();

/**
 * Configuration Example:
 * 
 * <script>
 *   window.qwenConfig = {
 *     apiUrl: 'https://your-api.com',
 *     apiKey: 'your-api-key',
 *     position: 'bottom-right',
 *     title: 'Chat with us',
 *     subtitle: 'Ask us anything',
 *     primaryColor: '#667eea',
 *     secondaryColor: '#764ba2',
 *     greeting: 'Hi! How can we help?',
 *     placeholder: 'Type your message...',
 *     autoOpen: false,
 *     showPoweredBy: true
 *   };
 * </script>
 * <script src="https://cdn.yoursite.com/widget/qwen-plugin.js"></script>
 */
