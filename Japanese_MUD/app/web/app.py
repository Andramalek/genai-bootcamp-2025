#!/usr/bin/env python3
"""
Web application for Japanese MUD game.
Provides a browser interface for the game using Flask and WebSockets.
"""

import os
import sys
import asyncio
import threading
from pathlib import Path
from queue import Queue
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit

# Add the parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.core.game_engine import GameEngine
from app.utils.logger import game_logger
from app.config import Config

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
socketio = SocketIO(app, async_mode="threading")

# Game engine and player sessions
game_engine = None
player_sessions = {}  # Maps session IDs to player IDs
output_queues = {}    # Maps player IDs to output queues

# Initialize game engine in a separate thread
def init_game_engine():
    global game_engine
    
    # Create event loop for the thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Initialize game engine
    config = Config()
    game_engine = GameEngine(use_db=config.USE_DATABASE)
    loop.run_until_complete(game_engine.initialize())
    
    game_logger.info("Game engine initialized for web interface")

# Start game engine initialization in a separate thread
threading.Thread(target=init_game_engine).start()

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
    if not username:
        return redirect(url_for("index"))
    
    session["username"] = username
    return redirect(url_for("game"))

@app.route("/logout")
def logout():
    """Handle player logout."""
    username = session.pop("username", None)
    session_id = request.sid if hasattr(request, "sid") else None
    
    if username and session_id in player_sessions:
        player_id = player_sessions[session_id]
        if player_id in output_queues:
            del output_queues[player_id]
        del player_sessions[session_id]
    
    return redirect(url_for("index"))

# WebSocket events
@socketio.on("connect")
def handle_connect():
    """Handle WebSocket connection."""
    if "username" not in session or not session["username"]:
        return
    
    # Create output queue for the player
    player_id = session["username"].lower().replace(" ", "_")
    output_queues[player_id] = Queue()
    player_sessions[request.sid] = player_id
    
    # Start player session in a separate thread
    threading.Thread(target=start_player_session, args=(player_id, request.sid)).start()

@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection."""
    if request.sid in player_sessions:
        player_id = player_sessions[request.sid]
        if player_id in output_queues:
            del output_queues[player_id]
        del player_sessions[request.sid]

@socketio.on("command")
def handle_command(data):
    """Handle game commands from the player."""
    if "command" not in data or request.sid not in player_sessions:
        return
    
    player_id = player_sessions[request.sid]
    command_text = data["command"]
    
    # Process command in a separate thread
    threading.Thread(target=process_command, args=(player_id, command_text)).start()

# Game processing functions
def start_player_session(player_id, session_id):
    """Start a new player session."""
    global game_engine
    
    # Wait for game engine to initialize
    while game_engine is None:
        threading.Event().wait(0.1)
    
    # Create event loop for the thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Add player to the game
    username = player_id.replace("_", " ").title()
    player = loop.run_until_complete(game_engine.add_player(username, session_id))
    
    # Override game engine's send_output method to use our queue
    game_engine.send_output = lambda text: send_output(player_id, text)
    
    # Send initial output to player
    send_output(player_id, f"Welcome to the Japanese MUD Game, {username}!")
    send_output(player_id, "Type 'help' to see available commands.")

def process_command(player_id, command_text):
    """Process a command from the player."""
    global game_engine
    
    # Create event loop for the thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Process the command
    loop.run_until_complete(game_engine.process_command(command_text, player_id))

def send_output(player_id, text):
    """Send output to the player's browser."""
    if player_id not in output_queues:
        return
    
    # Find session ID for this player
    session_id = None
    for sid, pid in player_sessions.items():
        if pid == player_id:
            session_id = sid
            break
    
    if session_id:
        socketio.emit("output", {"text": text}, room=session_id)

# Main entry point
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True) 