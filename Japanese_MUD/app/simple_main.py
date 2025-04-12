#!/usr/bin/env python3
"""
Japanese MUD - A text-based adventure game for learning Japanese (Simple Version)
"""
import os
import sys
import asyncio
from typing import Dict, List, Optional
import json

def load_json_file(file_path: str):
    """Load a JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

class SimpleGameEngine:
    """Simple game engine for the Japanese MUD game"""
    def __init__(self):
        self.locations = {}
        self.items = {}
        self.npcs = {}
        self.vocabulary = {}
        self.current_location_id = "loc-001"  # Starting location
        
    async def load_game_data(self):
        """Load game data from JSON files"""
        print("Loading game data...")
        
        # Load locations
        locations_file = "data/game_templates/locations.json"
        locations_data = load_json_file(locations_file)
        for location in locations_data:
            self.locations[location["id"]] = location
            if location.get("is_starting_location", False):
                self.current_location_id = location["id"]
        
        # Load items
        items_file = "data/game_templates/items.json"
        items_data = load_json_file(items_file)
        for item in items_data:
            self.items[item["id"]] = item
        
        # Load NPCs
        npcs_file = "data/game_templates/npcs.json"
        npcs_data = load_json_file(npcs_file)
        for npc in npcs_data:
            self.npcs[npc["id"]] = npc
        
        # Load vocabulary
        vocab_file = "data/vocabulary/jlpt_n5.json"
        vocab_data = load_json_file(vocab_file)
        for word in vocab_data:
            self.vocabulary[word["id"]] = word
            
        print(f"Loaded {len(self.locations)} locations, {len(self.items)} items, and {len(self.npcs)} NPCs.")
    
    def get_location_description(self):
        """Get the current location description"""
        location = self.locations.get(self.current_location_id)
        if not location:
            return "You are nowhere."
        
        # Basic location description
        description = f"\n**{location.get('name')}** ({location.get('japanese_name', '')})\n\n"
        description += f"{location.get('description', '')}\n\n"
        
        # Show cultural note if available
        if "cultural_note" in location:
            description += f"Cultural Note: {location['cultural_note']}\n\n"
        
        # List exits
        exits = location.get("exits", {})
        if exits:
            description += "Exits: "
            exit_list = []
            for direction, exit_loc in exits.items():
                exit_location = self.locations.get(exit_loc, {})
                exit_list.append(f"{direction.capitalize()} to {exit_location.get('name', 'Unknown')}")
            description += ", ".join(exit_list) + "\n\n"
        
        # List items
        items_in_location = []
        for item_id in location.get("items", []):
            if item_id in self.items:
                items_in_location.append(self.items[item_id])
        
        if items_in_location:
            description += "Items: "
            item_names = [f"{item.get('name', 'Unknown Item')} ({item.get('japanese_name', '')})" 
                         for item in items_in_location]
            description += ", ".join(item_names) + "\n\n"
        
        # List NPCs
        npcs_in_location = []
        for npc_id in location.get("npcs", []):
            if npc_id in self.npcs:
                npcs_in_location.append(self.npcs[npc_id])
        
        if npcs_in_location:
            description += "People: "
            npc_names = [f"{npc.get('name', 'Unknown Person')} ({npc.get('japanese_name', '')})" 
                        for npc in npcs_in_location]
            description += ", ".join(npc_names) + "\n"
        
        return description
    
    def process_command(self, command: str):
        """Process a user command"""
        parts = command.lower().strip().split()
        if not parts:
            return "Please enter a command."
        
        # Look command
        if parts[0] in ["look", "examine", "見る"]:
            return self.get_location_description()
        
        # Go command
        elif parts[0] in ["go", "move", "行く"] and len(parts) > 1:
            direction = parts[1]
            location = self.locations.get(self.current_location_id)
            exits = location.get("exits", {})
            
            if direction in exits:
                self.current_location_id = exits[direction]
                return f"You go {direction}.\n" + self.get_location_description()
            else:
                return f"You cannot go {direction} from here."
        
        # Help command
        elif parts[0] in ["help", "ヘルプ"]:
            return """
Commands:
- look/examine: Look at your surroundings
- go [direction]: Move in a direction (north, south, east, west)
- help: Show this help
- quit/exit: Exit the game
            """
        
        # Exit command
        elif parts[0] in ["quit", "exit", "終了"]:
            return "exit"
        
        # Unknown command
        else:
            return f"I don't understand '{command}'. Type 'help' for a list of commands."

async def main():
    """Main function to run the game"""
    print("\n" + "="*60)
    print("Welcome to the Japanese MUD - A Language Learning Adventure!")
    print("This is a simple version without image generation or complex features.")
    print("Type 'help' for a list of commands.")
    print("="*60 + "\n")
    
    game = SimpleGameEngine()
    try:
        await game.load_game_data()
        
        # Show initial location
        print(game.get_location_description())
        
        # Main game loop
        running = True
        while running:
            command = input("\n> ")
            response = game.process_command(command)
            
            if response == "exit":
                running = False
                print("Thank you for playing!")
            else:
                print(response)
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data/images", exist_ok=True)
    os.makedirs("data/user_data", exist_ok=True)
    
    # Run the main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 