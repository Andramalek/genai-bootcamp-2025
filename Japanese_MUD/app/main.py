#!/usr/bin/env python3
"""
Japanese MUD - A text-based adventure game for learning Japanese
"""
import os
import sys
import asyncio
from typing import List, Dict, Optional
import argparse

from app.utils.logger import game_logger
from app.game.game_engine import GameEngine
from app.player.player import Player

async def main():
    """Main entry point for the game"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Japanese MUD - A text-based adventure game for learning Japanese")
    parser.add_argument("--player", help="Load an existing player by ID")
    args = parser.parse_args()
    
    # Initialize game engine
    game_engine = GameEngine()
    
    try:
        # Load game data
        print("Loading game data...")
        await game_engine.load_game_data()
        
        # Handle player selection or creation
        player = None
        
        if args.player:
            print(f"Loading player {args.player}...")
            player = game_engine.load_player(args.player)
            
        if not player:
            # No player specified or loading failed, create a new one
            username = input("Enter your username: ")
            jlpt_level = input("Select your JLPT level (N5, N4, N3, N2, N1) [default: N5]: ") or "N5"
            
            print(f"Creating new player: {username} (Level: {jlpt_level})...")
            player = game_engine.create_player(username, jlpt_level)
            print(f"Player created with ID: {player.player_id}")
            print("Remember this ID to continue your game later!")
        
        # Display welcome message
        print("\n" + "="*60)
        print("Welcome to the Japanese MUD - A Language Learning Adventure!")
        print("Type 'help' for a list of commands.")
        print("="*60 + "\n")
        
        # Show initial location
        current_location = game_engine.state.get_current_location()
        if current_location:
            # Display the location image
            location_id = current_location["id"]
            game_engine.display_location_image(location_id)
            
            # Display location description
            print(game_engine.get_location_description(location_id))
        
        # Main game loop
        game_engine.running = True
        
        while game_engine.running:
            # Get command from user
            command = input("\n> ")
            
            # Process command
            response = game_engine.process_command(command)
            print(response)
        
        # Save game on exit
        if player:
            player.save()
            print("Game progress saved.")
    
    except KeyboardInterrupt:
        print("\nExiting game...")
        if game_engine.state.get_current_player():
            game_engine.save_game()
            print("Game progress saved.")
    
    except Exception as e:
        game_logger.error(f"Error: {str(e)}")
        print(f"An error occurred: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data/images", exist_ok=True)
    os.makedirs("data/user_data", exist_ok=True)
    
    # Run the main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 