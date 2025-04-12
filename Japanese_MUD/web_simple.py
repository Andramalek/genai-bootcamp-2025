#!/usr/bin/env python3
"""
Web interface for the simplified Japanese MUD Game.
This provides a browser interface using Flask and Socket.IO.
"""

import os
import sys
import asyncio
import threading
from pathlib import Path
from queue import Queue
from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import logging
import time

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web_server")

# Import the SimpleGameEngine
from run_game import SimpleGameEngine

# Import image client
try:
    from app.utils.image_client import ImageClient
    HAS_IMAGE_CLIENT = True
    logger.info("Image client loaded successfully.")
except ImportError:
    HAS_IMAGE_CLIENT = False
    logger.warning("Image client not available. Location images will not be generated.")

# Initialize Flask app
app = Flask(__name__, 
            template_folder='app/web/templates',
            static_folder='app/web/static')
app.config["SECRET_KEY"] = os.urandom(24)
socketio = SocketIO(app, async_mode="threading")

# Game engine and player sessions
game_engine = None
player_sessions = {}  # Maps session IDs to player data
output_queues = {}    # Maps session IDs to output queues
location_images = {}  # Cache of location images

# Initialize game engine in a separate thread
def init_game_engine():
    global game_engine
    
    # Create event loop for the thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Initialize game engine
    game_engine = SimpleGameEngine()
    loop.run_until_complete(game_engine.load_game_data())
    
    logger.info("Game engine initialized for web interface.")

def _generate_and_push_image(location_id, image_prompt, setting, sid):
    """Helper function to run image generation in a thread and push update."""
    logger.info(f"Background thread started for image generation: {location_id}")
    try:
        # Synchronous call within the thread
        result_path = ImageClient.generate_location_image(
            location_id=location_id, 
            prompt=image_prompt, 
            location_setting=setting
        )
        
        if result_path and Path(result_path).exists():
            image_url = f"/images/{location_id}.jpg"
            logger.info(f"Background generation complete for {location_id}. Pushing update to {sid}")
            # Push the real image URL to the specific client
            socketio.emit('location_image', {'url': image_url}, room=sid)
        else:
            logger.error(f"Background image generation failed for {location_id}")
            # Optionally push an error or just leave the placeholder/loading state
    except Exception as e:
        logger.error(f"Error in background image generation thread for {location_id}: {e}")

# Routes
@app.route("/")
def index():
    """Render the game login page."""
    if "username" in session and session["username"]:
        return redirect(url_for("game"))
    return render_template("index.html")

@app.route("/game")
def game():
    """Render the main game interface."""
    if "username" not in session or not session["username"]:
        return redirect(url_for("index"))
    return render_template("game.html", username=session["username"])

@app.route("/login", methods=["POST"])
def login():
    """Handle player login."""
    username = request.form.get("username")
    jlpt_level = request.form.get("jlpt_level", "N5")
    
    if not username:
        return redirect(url_for("index"))
    
    session["username"] = username
    session["jlpt_level"] = jlpt_level
    return redirect(url_for("game"))

@app.route("/logout")
def logout():
    """Handle player logout."""
    username = session.pop("username", None)
    session_id = request.sid if hasattr(request, "sid") else None
    
    if username and session_id in player_sessions:
        del player_sessions[session_id]
    
    return redirect(url_for("index"))

@app.route("/images/<path:filename>")
def serve_image(filename):
    """Serve location images from the data/images directory."""
    return send_from_directory("data/images", filename)

# WebSocket events
@socketio.on("connect")
def handle_connect():
    """Handle WebSocket connection."""
    if "username" not in session or not session["username"]:
        return
    
    session_id = request.sid
    username = session["username"]
    jlpt_level = session.get("jlpt_level", "N5")
    
    game_engine.player_jlpt_level = jlpt_level
    
    current_coords_str = game_engine._coords_to_str(game_engine.current_coords)
    
    player_sessions[session_id] = {
        "username": username,
        "jlpt_level": jlpt_level,
        "current_coords_str": current_coords_str
    }
    
    emit("output", {"text": f"Welcome to the Japanese MUD Game, {username}!"})
    emit("output", {"text": f"Your Japanese level is set to {jlpt_level}."})
    emit("output", {"text": "Type 'help' for a list of commands."})
    
    # --- Send structured location data --- 
    # --- FIX: Wait briefly/check if engine/start location is ready --- 
    max_wait = 5.0 # Max seconds to wait for engine
    wait_interval = 0.2
    waited = 0.0
    location_data = None
    
    while waited < max_wait:
        if game_engine and current_coords_str in game_engine.locations:
            location_data = game_engine.get_location_description(current_coords_str)
            if location_data: # Check if description itself is valid
                break # Got valid data
        logger.info(f"Waiting for game engine/start location... ({waited:.1f}s)")
        time.sleep(wait_interval)
        waited += wait_interval
        
    if location_data:
        emit("update_location", location_data) # New event with structured data
    else:
        logger.error(f"Failed to get starting location data for {current_coords_str} after {max_wait}s")
        emit("output", {"text": "Error: Could not load starting location details after waiting."}) 
    
    # Determine starting image URL, trigger background generation if needed
    location_id = f"loc_{current_coords_str}"
    image_path = Path(f"data/images/{location_id}.jpg")
    image_url = "/images/placeholder.jpg" # Default to placeholder/loading state
    
    if image_path.exists():
        image_url = f"/images/{location_id}.jpg"
    elif HAS_IMAGE_CLIENT:
        # Image doesn't exist, trigger background generation
        location_data = game_engine.locations.get(current_coords_str)
        if location_data:
            image_prompt = location_data.get("image_prompt", "")
            setting = location_data.get("setting", "")
            if image_prompt:
                 logger.info(f"Triggering background image generation for starting location {location_id}")
                 threading.Thread(
                     target=_generate_and_push_image, 
                     args=(location_id, image_prompt, setting, session_id) # Pass SID
                 ).start()
            else:
                 logger.warning(f"Cannot generate starting image {location_id}: missing prompt.")
        else:
            logger.warning(f"Cannot generate starting image {location_id}: location data missing.")

    # Send the initial URL (placeholder or actual)
    emit("location_image", {"url": image_url})

@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection."""
    if request.sid in player_sessions:
        del player_sessions[request.sid]

@socketio.on("command")
def handle_command(data):
    """Handle game commands from the player."""
    if "command" not in data or request.sid not in player_sessions:
        return
    
    session_id = request.sid # Get session ID for potential push
    command_text = data["command"]
    previous_coords_str = game_engine._coords_to_str(game_engine.current_coords)
    
    response = game_engine.process_command(command_text)
    
    if response != "exit":
        # --- Check if response is location data --- 
        # The engine now returns a dict on successful move/look
        if isinstance(response, dict) and "description" in response and "items" in response:
            # It's the structured location data from get_location_description
            emit("update_location", response)
        else:
            # It's a normal text response (e.g., inventory, take result, error)
            emit("output", {"text": response})
    else:
        emit("output", {"text": "Thank you for playing! Goodbye."})
        # Disconnect? Or just leave the page as is?
        return # Important: stop processing if user quits

    current_coords_str = game_engine._coords_to_str(game_engine.current_coords)
    
    # Update player session coords if they changed
    if current_coords_str != previous_coords_str:
        player_sessions[session_id]["current_coords_str"] = current_coords_str

        # Location changed, handle image update (existing logic)
        location_id = f"loc_{current_coords_str}"
        image_path = Path(f"data/images/{location_id}.jpg")
        image_url = "/images/placeholder.jpg" # Default to placeholder/loading state

        if image_path.exists():
            image_url = f"/images/{location_id}.jpg"
        elif HAS_IMAGE_CLIENT:
            # Trigger background generation
            location_data = game_engine.locations.get(current_coords_str)
            if location_data:
                image_prompt = location_data.get("image_prompt", "")
                setting = location_data.get("setting", "")
                if image_prompt:
                    logger.info(f"Triggering background image generation for new location: {location_id}")
                    threading.Thread(
                        target=_generate_and_push_image,
                        args=(location_id, image_prompt, setting, session_id) # Pass SID
                    ).start()
                else:
                     logger.warning(f"Cannot generate image for {location_id}: missing image prompt.")
            else:
                 logger.warning(f"Cannot generate image for {location_id}: location data not found.")
        
        # Send the initial URL (placeholder or actual)
        emit("location_image", {"url": image_url})

def main():
    """Run the web interface."""
    # Create necessary directories
    os.makedirs("data/images", exist_ok=True)
    os.makedirs("data/user_data", exist_ok=True)
    
    # Start game engine initialization in a separate thread
    threading.Thread(target=init_game_engine).start()
    
    # Wait for game engine to initialize
    while game_engine is None:
        threading.Event().wait(0.1)
    
    # Print instructions
    host = "0.0.0.0"
    port = 5000
    print(f"Starting Japanese MUD Game web server on http://{host}:{port}")
    print("Press Ctrl+C to stop the server.")
    print(f"Image generation {'enabled' if HAS_IMAGE_CLIENT else 'disabled'}")
    
    # Run the Flask app with SocketIO
    socketio.run(app, host=host, port=port, debug=True)

if __name__ == "__main__":
    main() 