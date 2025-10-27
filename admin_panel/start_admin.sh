#!/bin/bash

# Admin Panel Quick Start Script
# Starts both backend and frontend for the admin panel

echo "🚀 Starting Messaging Agent Admin Panel..."

# Check if Redis is running
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  Redis not found. Starting Redis in Docker..."
    docker run -d --name redis-admin -p 6379:6379 redis:alpine
    echo "✅ Redis started in Docker"
else
    if ! redis-cli ping &> /dev/null; then
        echo "⚠️  Redis not running. Starting Redis..."
        redis-server --daemonize yes
        echo "✅ Redis started"
    else
        echo "✅ Redis is already running"
    fi
fi

# Create .env if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating .env file..."
    cat > backend/.env << EOF
# Admin Authentication
ADMIN_TOKEN=admin-secret-token-$(openssl rand -hex 16)

# Redis Configuration
REDIS_URL=redis://localhost:6379

# LLM Provider Settings
LLM_PROVIDER=anthropic
MODEL_NAME=claude-3-sonnet
TEMPERATURE=0.7
MAX_TOKENS=2000
RATE_LIMIT=100
EOF
    echo "✅ .env file created"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install -q -r requirements.txt

# Start backend server
echo "🔧 Starting backend server..."
python server.py &
BACKEND_PID=$!
echo "✅ Backend running on http://localhost:8000 (PID: $BACKEND_PID)"

# Start frontend server
echo "🌐 Starting frontend server..."
cd ../frontend
python -m http.server 8080 &
FRONTEND_PID=$!
echo "✅ Frontend running on http://localhost:8080 (PID: $FRONTEND_PID)"

echo ""
echo "========================================="
echo "✨ Admin Panel is ready!"
echo "========================================="
echo "📊 Dashboard: http://localhost:8080"
echo "🔧 API Docs: http://localhost:8000/docs"
echo ""
echo "Default credentials:"
echo "Token: Check backend/.env for ADMIN_TOKEN"
echo ""
echo "To stop: Press Ctrl+C"
echo "========================================="

# Wait for Ctrl+C
trap "echo '🛑 Shutting down...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
