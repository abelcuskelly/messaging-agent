// SMS Portal JavaScript

// WebSocket connection
let ws = null;
let messageHistory = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket();
    setupTabs();
    loadInitialData();
    startAutoRefresh();
});

// WebSocket connection
function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    
    ws.onopen = () => {
        console.log('✅ Connected to SMS Portal');
        updateConnectionStatus(true);
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    ws.onclose = () => {
        console.log('❌ Disconnected from SMS Portal');
        updateConnectionStatus(false);
        // Reconnect after 3 seconds
        setTimeout(initializeWebSocket, 3000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus(false);
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    if (data.type === 'stats') {
        updateStats(data.data);
    } else if (data.type === 'new_message') {
        addActivityItem(`📤 New SMS sent to ${data.data.to}`);
        loadMessages();
    }
}

// Update connection status
function updateConnectionStatus(connected) {
    const indicator = document.querySelector('.status-indicator');
    const statusText = document.querySelector('.status-text');
    
    if (connected) {
        indicator.classList.add('connected');
        statusText.textContent = 'Connected';
    } else {
        indicator.classList.remove('connected');
        statusText.textContent = 'Disconnected';
    }
}

// Setup tabs
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and panels
            tabButtons.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked button
            button.classList.add('active');
            
            // Show corresponding panel
            const tabName = button.getAttribute('data-tab');
            document.getElementById(`${tabName}Panel`).classList.add('active');
        });
    });
}

// Load initial data
function loadInitialData() {
    loadStats();
    loadMessages();
    loadCustomers();
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        updateStats(stats);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Update statistics display
function updateStats(stats) {
    document.getElementById('totalSent').textContent = stats.total_sent || 0;
    document.getElementById('totalFailed').textContent = stats.total_failed || 0;
    document.getElementById('successRate').textContent = 
        `${((stats.success_rate || 0) * 100).toFixed(1)}%`;
    document.getElementById('last24h').textContent = stats.last_24h || 0;
}

// Load messages
async function loadMessages() {
    try {
        const response = await fetch('/api/messages');
        const data = await response.json();
        displayMessages(data.messages);
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

// Display messages
function displayMessages(messages) {
    const container = document.getElementById('messagesList');
    
    if (messages.length === 0) {
        container.innerHTML = '<p style="color: #999; text-align: center; padding: 40px;">No messages yet</p>';
        return;
    }
    
    container.innerHTML = messages.map(msg => `
        <div class="message-card">
            <div class="message-header">
                <div class="message-to">To: ${msg.to}</div>
                <div class="message-status">${msg.status}</div>
            </div>
            <div class="message-body">${msg.body}</div>
            <div class="message-meta">
                SID: ${msg.sid} | Sent: ${formatDate(msg.sent_at)}
            </div>
        </div>
    `).join('');
}

// Load customers
async function loadCustomers() {
    try {
        const response = await fetch('/api/customers');
        const data = await response.json();
        displayCustomers(data.customers);
    } catch (error) {
        console.error('Error loading customers:', error);
    }
}

// Display customers
function displayCustomers(customers) {
    const container = document.getElementById('customersList');
    
    if (customers.length === 0) {
        container.innerHTML = '<p style="color: #999; text-align: center; padding: 40px;">No customers yet</p>';
        return;
    }
    
    container.innerHTML = customers.map(phone => `
        <div class="customer-card">
            <div class="customer-phone">${phone}</div>
            <div class="customer-stats">
                <button class="btn btn-secondary" onclick="viewCustomerHistory('${phone}')">
                    View History
                </button>
            </div>
        </div>
    `).join('');
}

// Send test SMS
async function sendTestSMS() {
    const phone = document.getElementById('phoneNumber').value;
    const body = document.getElementById('messageText').value;
    
    if (!phone || !body) {
        alert('Please fill in phone number and message');
        return;
    }
    
    try {
        const response = await fetch('/api/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ to: phone, body: body })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ SMS sent successfully!');
            addActivityItem(`📤 Test SMS sent to ${phone}`);
            loadMessages();
            loadStats();
        } else {
            alert(`❌ Error: ${result.error}`);
        }
    } catch (error) {
        alert('Error sending SMS: ' + error.message);
    }
}

// Send ticket confirmation
async function sendTicketConfirmation() {
    const phone = prompt('Enter phone number (E.164 format):');
    if (!phone) return;
    
    try {
        const response = await fetch('/api/send/confirmation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                to: phone,
                order_id: 'TEST123',
                game: 'Lakers vs Warriors',
                date: 'January 15, 2024'
            })
        });
        
        const result = await response.json();
        if (result.success) {
            alert('✅ Confirmation SMS sent!');
            addActivityItem(`📧 Ticket confirmation sent to ${phone}`);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Send game reminder
async function sendGameReminder() {
    const phone = prompt('Enter phone number (E.164 format):');
    if (!phone) return;
    
    try {
        const response = await fetch('/api/send/reminder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                to: phone,
                game: 'Lakers vs Warriors',
                date: 'January 15, 2024',
                time: '7:00 PM'
            })
        });
        
        const result = await response.json();
        if (result.success) {
            alert('✅ Game reminder sent!');
            addActivityItem(`⏰ Game reminder sent to ${phone}`);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Send upgrade notification
async function sendUpgradeNotification() {
    alert('Upgrade notification feature coming soon!');
}

// Refresh messages
function refreshMessages() {
    loadMessages();
    addActivityItem('🔄 Messages refreshed');
}

// View customer history
async function viewCustomerHistory(phone) {
    try {
        const response = await fetch(`/api/customer/${phone}/history`);
        const data = await response.json();
        
        if (data.messages.length > 0) {
            displayMessages(data.messages);
            // Switch to messages tab
            document.querySelector('[data-tab="messages"]').click();
        } else {
            alert(`No messages found for ${phone}`);
        }
    } catch (error) {
        alert('Error loading customer history: ' + error.message);
    }
}

// Add activity item
function addActivityItem(text) {
    const feed = document.getElementById('activityFeed');
    const timestamp = new Date().toLocaleTimeString();
    
    const item = document.createElement('div');
    item.className = 'activity-item';
    item.textContent = `${timestamp}: ${text}`;
    
    feed.insertBefore(item, feed.firstChild);
    
    // Keep only last 20 items
    while (feed.children.length > 20) {
        feed.removeChild(feed.lastChild);
    }
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Start auto-refresh
function startAutoRefresh() {
    setInterval(() => {
        loadStats();
    }, 5000); // Refresh every 5 seconds
}

// Export functions for onclick handlers
window.sendTestSMS = sendTestSMS;
window.sendTicketConfirmation = sendTicketConfirmation;
window.sendGameReminder = sendGameReminder;
window.sendUpgradeNotification = sendUpgradeNotification;
window.refreshMessages = refreshMessages;
window.viewCustomerHistory = viewCustomerHistory;
