#!/usr/bin/env python3
"""
Run script for the Japanese MUD Game web interface.
This script provides a simplified way to start the web server.
"""

import os
import sys
import argparse
from app.web.app import app, socketio

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Japanese MUD Game web interface")
    parser.add_argument("--host", default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--init-db", action="store_true", help="Initialize the database before starting")
    return parser.parse_args()

def main():
    """Run the web interface."""
    args = parse_args()
    
    # Initialize database if requested
    if args.init_db:
        print("Initializing database...")
        from app.utils.database import Database
        db = Database.get_db_instance()
        db.init_schema()
        db.import_data()
        print("Database initialized successfully.")
    
    # Print instructions
    print(f"Starting Japanese MUD Game web server on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server.")
    
    # Run the Flask app with SocketIO
    socketio.run(app, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main() 