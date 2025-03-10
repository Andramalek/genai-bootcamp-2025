#!/bin/bash

# Script to set up and run the Japanese TTS service
set -e  # Exit on error

# Define key paths
VENV_PATH="/home/andramalek/projects/clone/gen-ai-bootcamp-2025/path/to/venv"
SERVICE_DIR="/home/andramalek/projects/clone/gen-ai-bootcamp-2025/opea-comps/mega-service"
DOCKER_COMPOSE_PATH="/home/andramalek/projects/clone/gen-ai-bootcamp-2025/opea-comps/docker-compose.yml"

# Print status header
echo "========================================================"
echo "🚀 Setting up and running Japanese TTS Service"
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

# Step 6: Run the Japanese TTS service
echo "🎯 Running the Japanese TTS service..."
echo "========================================================"
python japanese_tts_service.py

# If we get here, the script exited
echo "Service has stopped." 