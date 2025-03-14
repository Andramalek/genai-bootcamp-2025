#!/bin/bash

# Set the directory of this script as the working directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Create and activate a virtual environment if it doesn't exist
echo "Activating opea-comps virtual environment..."

# Check if we have Python 3.10 or higher
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

# Check for required packages
echo "Checking for required packages..."

# Check for SpeechRecognition
if ! python3 -c "import speech_recognition" &> /dev/null; then
    echo "Installing required package: SpeechRecognition"
    pip install SpeechRecognition
else
    echo "SpeechRecognition is already installed."
fi

# Check for ffmpeg (needed for audio format conversion)
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg is required for audio conversion but is not installed."
    echo "Please install ffmpeg. On Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "On macOS with Homebrew: brew install ffmpeg"
    echo "Then run this script again."
    exit 1
else
    echo "ffmpeg is installed and available."
fi

# Start the Japanese Conversation Agent
echo "Starting Japanese Conversation Agent..."
python3 japanese_conversation_agent.py &

# Wait a bit for the service to start
echo "Waiting for the service to start..."
sleep 3

# Try to open the frontend in a browser
echo "Japanese Conversation Agent is now running."
echo "You can access the frontend at: http://localhost:8083"
echo "Opening frontend in your default browser..."

# Determine the platform and try to open a browser
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open http://localhost:8083 2>/dev/null || (
        echo "Could not automatically open a browser. Please open this URL manually:"
        echo "http://localhost:8083"
    )
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:8083 || (
        echo "Could not automatically open a browser. Please open this URL manually:"
        echo "http://localhost:8083"
    )
elif [[ "$OSTYPE" == "cygwin" || "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    start http://localhost:8083 || (
        echo "Could not automatically open a browser. Please open this URL manually:"
        echo "http://localhost:8083"
    )
else
    echo "Could not automatically open a browser. Please open this URL manually:"
    echo "http://localhost:8083"
fi

echo "If the browser doesn't open automatically, please go to: http://localhost:8083"
echo "Press Ctrl+C to stop the service when you're done."

# Keep the script running so we can see the output
wait 