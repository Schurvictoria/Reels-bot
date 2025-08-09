#!/bin/bash

# ReelsBot startup script

set -e

echo "🎬 Starting ReelsBot..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from env.example..."
    cp env.example .env
    echo "📝 Please edit .env file with your API keys before running again."
    exit 1
fi

# Check for required environment variables
source .env

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY is required. Please set it in .env file."
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo "❌ SECRET_KEY is required. Please set it in .env file."
    exit 1
fi

# Create necessary directories
mkdir -p data/prompts data/templates logs

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $1 is already in use"
        return 1
    fi
    return 0
}

# Check if ports are available
if ! check_port 8000; then
    echo "Please stop the service running on port 8000 or change the API port."
    exit 1
fi

if ! check_port 7860; then
    echo "Please stop the service running on port 7860 or change the UI port."
    exit 1
fi

# Start services based on argument
case "${1:-all}" in
    "api")
        echo "🚀 Starting API server only..."
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    "ui")
        echo "🎨 Starting UI only..."
        python app/interface.py
        ;;
    "docker")
        echo "🐳 Starting with Docker..."
        docker-compose up --build
        ;;
    "docker-prod")
        echo "🐳 Starting production Docker stack..."
        docker-compose --profile monitoring up --build -d
        ;;
    "all"|*)
        echo "🚀 Starting API and UI servers..."
        
        # Start API in background
        echo "Starting API server on port 8000..."
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
        API_PID=$!
        
        # Wait for API to start
        sleep 5
        
        # Check if API is running
        if ! curl -f http://localhost:8000/health/ >/dev/null 2>&1; then
            echo "❌ API failed to start"
            kill $API_PID 2>/dev/null || true
            exit 1
        fi
        
        echo "✅ API server started successfully"
        echo "📖 API documentation: http://localhost:8000/docs"
        
        # Start UI
        echo "Starting UI server on port 7860..."
        python app/interface.py &
        UI_PID=$!
        
        echo "✅ UI server started successfully"
        echo "🎨 Web interface: http://localhost:7860"
        echo ""
        echo "🎬 ReelsBot is now running!"
        echo "📝 Press Ctrl+C to stop all services"
        
        # Handle shutdown
        trap 'echo "🛑 Shutting down..."; kill $API_PID $UI_PID 2>/dev/null || true; exit' INT TERM
        
        # Wait for both processes
        wait
        ;;
esac