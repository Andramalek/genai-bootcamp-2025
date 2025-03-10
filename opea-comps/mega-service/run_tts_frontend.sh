#!/bin/bash

# Script to set up and run the Japanese TTS service with frontend
set -e  # Exit on error

# Define key paths
VENV_PATH="/home/andramalek/projects/clone/gen-ai-bootcamp-2025/path/to/venv"
SERVICE_DIR="/home/andramalek/projects/clone/gen-ai-bootcamp-2025/opea-comps/mega-service"
DOCKER_COMPOSE_PATH="/home/andramalek/projects/clone/gen-ai-bootcamp-2025/opea-comps/docker-compose.yml"

# Print status header
echo "========================================================"
echo "🚀 Setting up and running Japanese TTS Service with Frontend"
echo "========================================================"

# Step 1: Check if we're in the right directory, if not, go there
if [ "$(pwd)" != "$SERVICE_DIR" ]; then
    echo "📂 Changing to service directory: $SERVICE_DIR"
    cd "$SERVICE_DIR"
fi

# Step 2: Activate the virtual environment
echo "🔌 Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Step 3: Check if dependencies are installed
echo "📦 Checking dependencies..."
pip install -r requirements.txt

# Step 4: Check if Ollama is running
echo "🐳 Checking if Ollama service is running..."
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/api/tags | grep -q "200"; then
    echo "⚠️ Ollama service not running. Starting it now..."
    if [ -f "$DOCKER_COMPOSE_PATH" ]; then
        docker compose -f "$DOCKER_COMPOSE_PATH" up -d
        echo "⏳ Waiting for Ollama service to start..."
        sleep 10  # Give it time to start
    else
        echo "❌ Docker compose file not found at: $DOCKER_COMPOSE_PATH"
        echo "Please start the Ollama service manually and try again."
        exit 1
    fi
else
    echo "✅ Ollama service is running."
fi

# Step 5: Check if any language model is available
echo "🧠 Checking for available language models..."
MODELS=$(curl -s http://localhost:9000/api/tags)
if [[ $MODELS == *"models\":[]"* ]]; then
    echo "⚠️ No language models found. Pulling phi model..."
    curl -X POST http://localhost:9000/api/pull -d '{"name": "phi"}'
    echo "⏳ Waiting for model to download... This might take a while."
    sleep 10  # Give it some time, but the actual download might take longer
else
    echo "✅ Language models are available."
fi

# Step 6: Start the Japanese TTS service in the background
echo "🎯 Running the Japanese TTS service in the background..."
python japanese_tts_service.py &
SERVICE_PID=$!
echo "Service started with PID: $SERVICE_PID"

# Step 7: Wait for the service to be ready
echo "⏳ Waiting for the service to be ready..."
sleep 5

# Step 8: Open the frontend in a browser
echo "🌐 Opening frontend in the default browser..."
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:8082/
elif command -v open > /dev/null; then
    open http://localhost:8082/
elif command -v start > /dev/null; then
    start http://localhost:8082/
else
    echo "Could not open browser automatically. Please open http://localhost:8082/ in your browser."
fi

echo "========================================================"
echo "Service is running! Access the frontend at: http://localhost:8082/"
echo "Press Ctrl+C to stop the service"
echo "========================================================"

# Wait for the service to exit or user to press Ctrl+C
wait $SERVICE_PID 