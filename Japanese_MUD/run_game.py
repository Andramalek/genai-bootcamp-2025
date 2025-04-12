#!/usr/bin/env python3
"""
Japanese MUD - A text-based adventure game for learning Japanese (Simple Version)
"""
import os
import sys
import asyncio
import json
import requests
import logging
import random
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from app.utils.ai_client import AIClient
from app.utils.image_client import ImageClient

# Set up logging for this module
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__) # Define logger instance

# Load environment variables
load_dotenv()

# Import AI client
try:
    from app.utils.ai_client import AIClient
    HAS_AI_CLIENT = True
except ImportError:
    HAS_AI_CLIENT = False
    print("AI client not available. NPCs will use static responses.")

# Check for AI availability based on key existence
HAS_AI_CLIENT = bool(os.getenv("OPENAI_API_KEY"))
HAS_GEMINI_CLIENT = bool(os.getenv("GEMINI_API_KEY"))

def load_json_file(file_path: str):
    """Load a JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

class SimpleGameEngine:
    """Simple game engine for the Japanese MUD game"""
    def __init__(self):
        self.locations: Dict[str, Dict] = {} # Store generated locations keyed by "x,y"
        self.items = {} # Items will be generated dynamically
        self.npcs = {}
        self.vocabulary = {}
        self.vocabulary_themes = {}
        # self.current_location_id = "loc-001"  # No longer used, use current_coords
        self.player_inventory: List[str] = []
        self.player_jlpt_level = os.getenv("STARTING_JLPT_LEVEL", "N5")
        self.conversation_history: Dict[str, List] = {}
        self.current_coords = (0, 0)
        self.location_settings_pool = [
            "Residential Neighborhood", "Small Urban Park", "Quiet Shopping Street", 
            "Path near a Small Shrine", "Empty Field", "Riverside Path"
        ]
        
    async def load_game_data(self):
        """Load game data (vocab) and ensure starting location exists."""
        print("Loading game data...")
        
        # REMOVED: Loading items from JSON, they will be generated dynamically
        # try:
        #     items_file = "data/game_templates/items.json"
        #     items_data = load_json_file(items_file)
        #     for item in items_data:
        #         self.items[item["id"]] = item
        # except FileNotFoundError:
        #     logger.warning("Items file not found. 'take'/'drop' might behave unexpectedly.")
        #     self.items = {}
        self.items = {} # Initialize as empty dict

        # REMOVED: Loading NPCs from JSON, they will be generated dynamically
        # try:
        #     npcs_file = "data/game_templates/npcs.json"
        #     npcs_data = load_json_file(npcs_file)
        #     for npc in npcs_data:
        #         self.npcs[npc["id"]] = npc
        #         self.conversation_history[npc["id"]] = [] # Initialize history
        # except FileNotFoundError:
        #     logger.warning("NPCs file not found.")
        #     self.npcs = {}
        self.npcs = {} # Initialize as empty dict
        self.conversation_history = {} # Initialize as empty dict

        # Load vocabulary
        vocab_file = "data/vocabulary/jlpt_n5.json"
        vocab_data = load_json_file(vocab_file)
        for word in vocab_data:
            self.vocabulary[word["id"]] = word
            
        # Load vocabulary themes
        try:
            themes_file = "data/vocabulary/themes.json"
            themes_data = load_json_file(themes_file)
            self.vocabulary_themes = {theme["id"]: theme for theme in themes_data}
            print(f"Loaded {len(self.vocabulary_themes)} vocabulary themes.")
        except FileNotFoundError:
            print("Vocabulary themes file not found. Themes command will not work.")
            self.vocabulary_themes = {}
        except Exception as e:
            print(f"Error loading vocabulary themes: {e}")
            self.vocabulary_themes = {}
            
        print(f"Loaded {len(self.vocabulary)} vocabulary words.")
        print("Items and NPCs will be generated dynamically.")
        
        # Ensure starting location (0,0) exists
        start_coords_str = self._coords_to_str((0, 0))
        if start_coords_str not in self.locations:
            logger.info("Starting location (0,0) not found. Generating...")
            # Use a specific setting for the start or random from pool
            start_setting = "Quiet Shopping Street" # Example: Fixed starting setting
            # start_setting = random.choice(self.location_settings_pool)
            start_location_data = self._generate_location_data((0, 0), start_setting)
            self.locations[start_coords_str] = start_location_data
            logger.info(f"Generated starting location: {start_location_data.get('name')}")
        
        # Set current coordinates explicitly after loading/generation
        self.current_coords = (0, 0)
        logger.info(f"Game ready. Player starting at coordinates {self.current_coords}")
    
    def get_location_description(self, coords_str: str) -> Optional[Dict[str, Any]]:
        """Returns the description and item details for a given location.
        
        Returns:
            Dict: {
                'description': str, 
                'items': list[dict] containing full item details if available, 
                'npcs': list[dict] containing full npc details if available
            }
            or None if location doesn't exist.
        """
        location = self.locations.get(coords_str)
        if not location:
            return None

        description_parts = [
            f"Location: {location['name']} ({coords_str})",
            location["description"],
        ]
        
        # Get full item details
        items_present = []
        if location["items"]:
            description_parts.append("You see:")
            for item_id in location["items"]:
                item_details = self.items.get(item_id)
                if item_details:
                    # --- SIMPLIFY: Just list the primary (Japanese) name in the description --- 
                    description_parts.append(f"  - {item_details.get('name', item_id)}")
                    # items_present.append(item_details) # Keep adding full details to the list
                else:
                    description_parts.append(f"  - An unknown item ({item_id})")
                # --- Keep adding full details for the frontend --- 
                if item_details: items_present.append(item_details)
        else:
            description_parts.append("There are no items here.")
            
        # Get full NPC details
        npcs_present = []
        if location["npcs"]:
            description_parts.append("People present:")
            for npc_id in location["npcs"]:
                npc_details = self.npcs.get(npc_id)
                if npc_details:
                    # --- SIMPLIFY: Just list the primary (Japanese) name in the description --- 
                    description_parts.append(f"  - {npc_details.get('name', npc_id)}")
                    # npcs_present.append(npc_details) # Keep adding full details
                else:
                    description_parts.append(f"  - Someone unknown ({npc_id})")
                # --- Keep adding full details for the frontend --- 
                if npc_details: npcs_present.append(npc_details)
        else:
            description_parts.append("There is no one else here.")

        # --- FIX: Add available exits correctly --- 
        exits = [direction for direction, target_coords in location.get("exits", {}).items() if target_coords is not None] # Check if target coords exist
        description_parts.append(f"Exits: {', '.join(exits) if exits else 'None'}")

        # Combine description parts into a single string for the 'description' field
        full_description_text = "\n".join(description_parts)
        
        return {
            "description": full_description_text,
            "items": items_present,
            "npcs": npcs_present
        }
    
    def get_npc_in_location(self, target_name: str) -> Optional[dict]:
        """Find an NPC in the current location by name"""
        current_coords_str = self._coords_to_str(self.current_coords)
        location = self.locations.get(current_coords_str)
        if not location:
            return None
            
        for npc_id in location.get("npcs", []):
            if npc_id in self.npcs:
                npc = self.npcs[npc_id]
                name_matches = [
                    npc.get("id", "").lower(),
                    npc.get("name", "").lower(),
                    npc.get("japanese_name", "").lower(),
                    npc.get("romaji", "").lower()
                ]
                
                if any(target_name.lower() in name for name in name_matches):
                    return npc
        
        return None
    
    def get_item_in_location(self, target_item_name: str) -> Optional[dict]:
        """Find an item in the current location by name (English or Japanese)."""
        current_coords_str = self._coords_to_str(self.current_coords)
        location = self.locations.get(current_coords_str)
        if not location:
            return None
        
        target_item_name_lower = target_item_name.lower()
        
        for item_id in location.get("items", []):
            if item_id in self.items:
                item = self.items[item_id]
                name_matches = [
                    item.get("id", "").lower(),
                    item.get("name", "").lower(),
                    item.get("name_english", "").lower(),
                    item.get("japanese_name", "").lower()
                ]
                
                if any(target_item_name_lower in name for name in name_matches if name):
                    return item
        
        return None

    def get_item_in_inventory(self, target_item_name: str) -> Optional[dict]:
        """Find an item in the player's inventory by name."""
        target_item_name_lower = target_item_name.lower()
        
        for item_id in self.player_inventory:
            if item_id in self.items:
                item = self.items[item_id]
                # Check for matches (similar to location lookup)
                name_matches = [
                    item.get("id", "").lower(),
                    item.get("name", "").lower(),
                    item.get("name_english", "").lower(),
                    item.get("japanese_name", "").lower()
                ]
                
                if any(target_item_name_lower in name for name in name_matches if name):
                    return item
        
        return None
    
    def get_ai_enhanced_look_description(self, coords_str: str) -> str:
        """Calls AIClient to generate a richer description for the 'look' command."""
        location = self.locations.get(coords_str)
        if not location:
            return "You can't seem to get a good look at this place."

        setting = location.get("setting", "an unknown area")
        
        # Get names of items present
        item_names = []
        for item_id in location.get("items", []):
            item_details = self.items.get(item_id)
            if item_details:
                item_names.append(item_details.get("name_english", item_details.get("name", "an item")))
                
        # Get names of NPCs present
        npc_names = []
        for npc_id in location.get("npcs", []):
            npc_details = self.npcs.get(npc_id)
            if npc_details:
                npc_names.append(npc_details.get("name_english", npc_details.get("name", "someone")))
                
        # Call the AIClient method
        logger.info(f"Requesting enhanced look for {coords_str} (Setting: {setting}) with items: {item_names}, npcs: {npc_names}")
        return AIClient.generate_enhanced_look(setting, item_names, npc_names)
    
    def handle_npc_interaction(self, npc: dict, player_input: str = "") -> str:
        """
        Handle interaction with an NPC, either with static dialog or AI
        
        Args:
            npc: The NPC data
            player_input: What the player said, or empty for greeting
            
        Returns:
            str: The NPC's response
        """
        npc_id = npc["id"]
        npc_name = npc["name"]
        
        # If it's just a greeting (empty player input), or we don't have AI
        if not player_input or not HAS_AI_CLIENT:
            # Get greeting from dialog or directly from NPC
            if "dialog" in npc and "greeting" in npc["dialog"]:
                greeting = npc["dialog"]["greeting"]
            else:
                greeting = npc.get("greeting", "Hello!")
                
            response = f"\n{npc_name} says: \"{greeting}\"\n"
            response += "\nYou can have a conversation with NPCs using 'talk [name] [your message]'.\n"
            return response
            
        # Otherwise, generate a dynamic response with AI
        try:
            # Get conversation history for this NPC
            history = self.conversation_history.get(npc_id, [])
            
            # Call the AI client for a response
            ai_response = AIClient.npc_conversation(
                npc_data=npc,
                player_input=player_input,
                language_level=self.player_jlpt_level,
                conversation_history=history
            )
            
            # Format the response
            response = f"\n{npc_name} says in Japanese: \"{ai_response['response_japanese']}\"\n"
            response += f"Translation: \"{ai_response['response_english']}\"\n"
            
            # Add language note if available
            if "language_note" in ai_response and ai_response["language_note"]:
                response += f"\nLanguage Note: {ai_response['language_note']}\n"
                
            # Add to conversation history
            history.append({
                "user": player_input,
                "assistant": json.dumps(ai_response)
            })
            
            # Limit history length to prevent context window issues
            if len(history) > 5:
                history = history[-5:]
                
            self.conversation_history[npc_id] = history
            
            return response
            
        except Exception as e:
            return f"\n{npc_name} seems confused and doesn't respond properly. (Error: {str(e)})\n"
    
    def process_command(self, command: str) -> str | Dict[str, Any]: # Return type hint includes Dict
        """Process a player command."""
        parts = command.lower().split()
        original_parts = command.split() # Keep original case for proper nouns if needed
        
        # Look command
        if parts[0] in ["look", "l", "見る"]:
            if len(parts) == 1:
                # --- FIX: Call the specific AI enhanced look method --- 
                current_coords_str = self._coords_to_str(self.current_coords)
                # Return the richer description string directly
                return self.get_ai_enhanced_look_description(current_coords_str) 
            else:
                 return f"To look at something specific, use 'examine [target]'. To look around, just type 'look'."

        # Examine command
        elif parts[0] == "examine":
            if len(parts) > 1:
                target_name = " ".join(parts[1:])
                
                # Check inventory first
                item_in_inventory = self.get_item_in_inventory(target_name)
                if item_in_inventory:
                    # Call AIClient to generate detailed description
                    logger.info(f"Requesting AI examination for inventory item: {item_in_inventory.get('name_english')}")
                    ai_response = AIClient.generate_item_examination_details(item_in_inventory, self.player_jlpt_level)
                    # Return the full dictionary now, let the caller extract
                    return ai_response
                
                # Check items in location
                item_in_location = self.get_item_in_location(target_name)
                if item_in_location:
                    # --- Use AI for detailed examination --- 
                    logger.info(f"Requesting AI examination for location item: {item_in_location.get('name_english')}")
                    ai_response = self.get_ai_item_examination_details(item_in_location)
                    # Return the full dictionary now, let the caller extract
                    return ai_response
                
                return f"You don't see a '{target_name}' here or in your inventory."
            else:
                return "What do you want to examine? (e.g., 'examine [item/person]')"
        
        # Go command
        elif parts[0] in ["go", "move", "north", "south", "east", "west", "n", "s", "e", "w", "行く", "北", "南", "東", "西"]:
            # Determine direction
            direction = None
            if parts[0] in ["go", "move", "行く"] and len(parts) > 1:
                direction = parts[1].lower()
            elif parts[0] in ["north", "n", "北"]:
                direction = "north"
            elif parts[0] in ["south", "s", "南"]:
                direction = "south"
            elif parts[0] in ["east", "e", "東"]:
                direction = "east"
            elif parts[0] in ["west", "w", "西"]:
                direction = "west"

            if not direction:
                return "Where do you want to go? (e.g., 'go north')"

            direction_map = {
                "north": (0, 1),
                "south": (0, -1),
                "east": (1, 0),
                "west": (-1, 0),
                "北": (0, 1),
                "南": (0, -1),
                "東": (1, 0),
                "西": (-1, 0),
            }

            if direction in direction_map:
                dx, dy = direction_map[direction]
                current_x, current_y = self.current_coords
                target_coords = (current_x + dx, current_y + dy)
                target_coords_str = self._coords_to_str(target_coords)
                
                # Get the setting of the current location to influence the next one
                current_coords_str = self._coords_to_str(self.current_coords)
                current_setting = self.locations.get(current_coords_str, {}).get("setting", None)

                if target_coords_str not in self.locations:
                    logger.info(f"Generating new location at {target_coords} from {self.current_coords}")
                    # Always choose a new setting randomly for maximum diversity
                    new_setting = random.choice(self.location_settings_pool)
                    
                    logger.info(f"Chosen setting: {new_setting} (Randomly selected)")
                    new_location_data = self._generate_location_data(target_coords, new_setting)
                    self.locations[target_coords_str] = new_location_data
                    # (Web server image trigger might go here if refactored)
                    
                self.current_coords = target_coords
                new_location = self.locations[target_coords_str]
                
                # --- FIX: Return the location data dictionary directly --- 
                # The web handler is expecting this dictionary for the 'update_location' event.
                # arrival_desc = f"You go {direction}.\n\n" # No longer needed here
                # arrival_desc += self.get_location_description(target_coords_str) # Causes TypeError
                return self.get_location_description(target_coords_str)
            else:
                return f"'{direction}' is not a valid direction."
        
        # Take command
        elif parts[0] in ["take", "get", "取る"] and len(parts) > 1:
            target_item_name = " ".join(parts[1:])
            item_to_take = self.get_item_in_location(target_item_name) # Uses refactored helper
            
            if item_to_take:
                # --- Add Check: Can the item be taken? --- 
                if not item_to_take.get("can_be_taken", False):
                    return f"You can't take the {item_to_take['name']} ({item_to_take.get('name_english', '')}). It seems fixed in place."
                    
                item_id = item_to_take["id"]
                current_coords_str = self._coords_to_str(self.current_coords)
                location = self.locations[current_coords_str]
                
                if item_id in location.get("items", []):
                    location["items"].remove(item_id)
                
                self.player_inventory.append(item_id)
                return f"You take the {item_to_take['name']} ({item_to_take.get('name_english', '')})."
            else:
                return f"You don't see a '{target_item_name}' here."
                
        # Drop command
        elif parts[0] in ["drop", "捨てる"] and len(parts) > 1:
            target_item_name = " ".join(parts[1:])
            item_to_drop = self.get_item_in_inventory(target_item_name)
            
            if item_to_drop:
                item_id = item_to_drop["id"]
                current_coords_str = self._coords_to_str(self.current_coords)
                location = self.locations[current_coords_str]
                
                if item_id in self.player_inventory:
                    self.player_inventory.remove(item_id)
                
                if "items" not in location:
                    location["items"] = []
                location["items"].append(item_id)
                
                return f"You drop the {item_to_drop['name']} ({item_to_drop.get('name_english', '')})."
            else:
                return f"You don't have a '{target_item_name}' in your inventory."

        # Inventory command
        elif parts[0] in ["inventory", "inv", "持ち物"]:
            if not self.player_inventory:
                return "Your inventory is empty."
            else:
                inventory_list = []
                for item_id in self.player_inventory:
                    item = self.items.get(item_id)
                    if item:
                        inventory_list.append(f"- {item['name']} ({item.get('name_english', '')})")
                    else:
                        inventory_list.append(f"- Unknown item ({item_id})")
                return "You are carrying:\n" + "\n".join(inventory_list)
        
        # Talk command
        elif parts[0] in ["talk", "speak", "話す"] and len(parts) > 1:
            current_coords_str = self._coords_to_str(self.current_coords)
            location = self.locations.get(current_coords_str)
            npcs_here_ids = location.get("npcs", []) if location else []
            num_npcs_here = len(npcs_here_ids)
            
            target_npc = None
            player_message = ""
            
            # Try to determine the target NPC and the message
            potential_npc_name = parts[1]
            found_npc_by_name = self.get_npc_in_location(potential_npc_name.lower())
            
            if found_npc_by_name:
                # Case 1: Explicit NPC name provided (e.g., talk Suzuki-sensei hello)
                target_npc = found_npc_by_name
                player_message = " ".join(parts[2:])
            elif num_npcs_here == 1:
                # Case 2: No valid NPC name, but only one NPC present (e.g., talk hello)
                target_npc_id = npcs_here_ids[0]
                target_npc = self.npcs.get(target_npc_id)
                player_message = " ".join(parts[1:]) # The message starts from the second word
            elif num_npcs_here > 1:
                # Case 3: No valid NPC name, multiple NPCs present
                 return f"Who do you want to talk to? Options: {', '.join(self.npcs[npc_id]['name'] for npc_id in npcs_here_ids if npc_id in self.npcs)}"
            # else: num_npcs_here == 0, handled below
                
            # Process interaction if a target NPC was determined
            if target_npc:
                return self.handle_npc_interaction(target_npc, player_message)
            else:
                # No target NPC found (either none here, or name didn't match)
                if num_npcs_here > 0:
                    return f"You see {', '.join(self.npcs[npc_id]['name'] for npc_id in npcs_here_ids if npc_id in self.npcs)} here, but no one named '{potential_npc_name}'."
                else:
                    return "There is no one here to talk to."
        
        # Themes command
        elif parts[0] == "themes":
            if not self.vocabulary_themes:
                return "No vocabulary themes are currently loaded."
            
            response = "Available Vocabulary Themes:\n"
            theme_list = []
            for theme_id, theme_data in self.vocabulary_themes.items():
                theme_list.append(f"- **{theme_data.get('name', theme_id)}**: {theme_data.get('description', 'No description')}")
            response += "\n".join(sorted(theme_list))
            response += "\n\nUse 'theme [theme_name]' to study a specific theme."
            return response
            
        # Theme [name] command
        elif parts[0] == "theme" and len(parts) > 1:
            target_theme_name = " ".join(parts[1:])
            found_theme = None
            
            # Search for the theme by name or ID (case-insensitive)
            for theme_id, theme_data in self.vocabulary_themes.items():
                if (target_theme_name.lower() == theme_data.get("name", "").lower() or 
                    target_theme_name.lower() == theme_id.lower()):
                    found_theme = theme_data
                    break
            
            if found_theme:
                theme_name = found_theme.get("name", target_theme_name)
                vocab_ids = found_theme.get("words", [])
                
                if not vocab_ids:
                    return f"The theme '{theme_name}' currently has no vocabulary words associated with it."
                
                response = f"Vocabulary for Theme: **{theme_name}**\n"
                word_list = []
                for vocab_id in vocab_ids:
                    word_data = self.vocabulary.get(vocab_id)
                    if word_data:
                        word_list.append(
                            f"- {word_data['japanese']} ({word_data['romaji']}): {word_data['english']}"
                        )
                    else:
                        word_list.append(f"- (Word ID {vocab_id} not found)")
                        
                response += "\n".join(sorted(word_list))
                return response
            else:
                return f"Could not find a vocabulary theme named '{target_theme_name}'. Type 'themes' to see the list."
            
        # Learn [word] command
        elif parts[0] == "learn" and len(parts) > 1:
            target_word = " ".join(parts[1:]).lower()
            found_word_data = None
            
            # Search vocabulary by Japanese, Romaji, or English
            for word_id, word_data in self.vocabulary.items():
                if (target_word == word_data.get("japanese", "").lower() or
                    target_word == word_data.get("romaji", "").lower() or
                    target_word == word_data.get("english", "").lower()):
                    found_word_data = word_data
                    break
            
            if found_word_data:
                response = f"Learning about: **{found_word_data['japanese']}**\n\n"
                response += f"- **Romaji:** {found_word_data.get('romaji', 'N/A')}\n"
                response += f"- **English:** {found_word_data.get('english', 'N/A')}\n"
                response += f"- **Part of Speech:** {found_word_data.get('part_of_speech', 'N/A')}\n"
                response += f"- **JLPT Level:** {found_word_data.get('jlpt_level', 'N/A')}\n\n"
                
                if found_word_data.get("example_sentence"):
                    response += f"**Example:**\n"
                    response += f"  {found_word_data['example_sentence']}\n"
                    response += f"  (Translation: {found_word_data.get('example_translation', 'N/A')})\n\n"
                
                if found_word_data.get("context_categories"):
                    response += f"**Context:** {', '.join(found_word_data['context_categories'])}\n"
                    
                if found_word_data.get("related_words"):
                    response += f"**Related:** {', '.join(found_word_data['related_words'])}\n"
                
                if found_word_data.get("usage_notes"):
                    response += f"\n**Usage Notes:** {found_word_data['usage_notes']}\n"
                    
                return response
            else:
                return f"Could not find the word '{target_word}' in the current vocabulary list."
            
        # Help command
        elif parts[0] in ["help", "ヘルプ"]:
            return """
Commands:
- look: Look at your surroundings
- examine [object]: Look closely at an item
- go [direction]: Move in a direction (north, south, east, west)
- take [item name]: Pick up an item from the location
- drop [item name]: Leave an item from your inventory here
- inventory/inv: Check the items you are carrying
- talk [person]: Talk to a person in the current location
- talk [person] [message]: Have a conversation with an NPC
- themes: List available vocabulary themes
- theme [theme_name]: Show words for a specific theme
- learn [word]: Show detailed information about a specific vocabulary word
- help: Show this help
- quit/exit: Exit the game
            """
        
        # Exit command
        elif parts[0] in ["quit", "exit", "終了"]:
            return "exit"
        
        # Unknown command
        else:
            return f"I don't understand '{command}'. Type 'help' for a list of commands."

    # --- Placeholder for Procedural Location Generation --- 
    def _generate_location_data(self, coords: tuple, setting: str) -> Dict:
        """Generates data for a new location, including AI description and potentially AI-generated NPC."""
        coords_str = self._coords_to_str(coords)
        location_id = f"loc_{coords_str}"
        
        # --- Use AIClient to generate name and description --- 
        logger.info(f"Requesting location details for {coords} (Setting: {setting}) from AIClient...")
        ai_details = AIClient.generate_location_details(setting, coords)
        location_name = ai_details.get("name", f"{setting} at {coords}")
        location_jp_name = ai_details.get("japanese_name", f"{setting} ({coords[0]},{coords[1]})")
        location_desc = ai_details.get("description", f"A procedurally generated {setting.lower()} at {coords}.")
        
        # --- Generate exactly ONE item via AI --- 
        new_items = []
        item_names_for_prompt = []
        logger.info(f"Attempting to generate item for location {coords_str} (Setting: {setting})...")
        generated_item_data = AIClient.generate_item_details(setting)

        if generated_item_data:
            # Create a unique ID for this generated item instance
            new_item_id = f"item_{coords_str}_{len(self.items)}"
            generated_item_data['id'] = new_item_id # Add the ID

            # Store the item data in the global engine list
            self.items[new_item_id] = generated_item_data
            
            # --- REMOVED Vocabulary Tracking --- 
            # item_name_jp = generated_item_data.get("name")
            # item_name_en = generated_item_data.get("name_english")
            # found_item_name_id = self.find_vocab_id(item_name_jp) or self.find_vocab_id(item_name_en)
            # if found_item_name_id:
            #    logger.info(f"Added vocab '{found_item_name_id}' based on item name: {item_name_jp or item_name_en}")
            # item_vocab = generated_item_data.get("vocabulary", [])
            # if isinstance(item_vocab, list):
            #     for word in item_vocab:
            #         found_id = self.find_vocab_id(word)
            #         if found_id:
            #              logger.info(f"Added vocab '{found_id}' based on item name: {word}")
            
            # Add the ID to this location's list
            new_items.append(new_item_id)
            
            # Prepare info for image prompt
            item_name_en = generated_item_data.get('name_english', new_item_id)
            item_names_for_prompt.append(item_name_en)
            logger.info(f"Successfully generated and added item '{item_name_en}' ({new_item_id}) to location {coords_str}")
        else:
            logger.warning(f"AI failed to generate item details for location {coords_str}. Location will have no items.")
        
        # --- Generate NPC via AI --- 
        new_npcs = []
        npc_names_for_prompt = []
        # Use the 70% chance to decide IF an NPC should be generated
        if random.random() < 0.70: 
            logger.info(f"Attempting to generate NPC for location {coords_str} (Setting: {setting})...")
            generated_npc_data = AIClient.generate_npc_details(setting)
            
            if generated_npc_data:
                # Create a unique ID for this generated NPC instance
                new_npc_id = f"npc_{coords_str}_{len(self.npcs)}"
                generated_npc_data['id'] = new_npc_id # Add the ID to the data
                
                # Store the NPC data in the global engine list
                self.npcs[new_npc_id] = generated_npc_data
                self.conversation_history[new_npc_id] = [] # Initialize history
                
                # --- REMOVED Vocabulary Tracking --- 
                # npc_role = generated_npc_data.get("role")
                # found_role_id = self.find_vocab_id(npc_role)
                # if found_role_id:
                #     logger.info(f"Added vocab '{found_role_id}' based on NPC role: {npc_role}")
                # npc_vocab = generated_npc_data.get("vocabulary", [])
                # if isinstance(npc_vocab, list):
                #      for word in npc_vocab:
                #         found_id = self.find_vocab_id(word)
                #         if found_id:
                #              logger.info(f"Added vocab '{found_id}' based on NPC role: {word}")
                             
                # Add the ID to this location's list
                new_npcs.append(new_npc_id)
                
                # Prepare info for image prompt
                npc_name = generated_npc_data.get("name", new_npc_id)
                npc_role = generated_npc_data.get("role", "person")
                npc_names_for_prompt.append(f"{npc_name} (the {npc_role})")
                logger.info(f"Successfully generated and added NPC '{npc_name}' ({new_npc_id}) to location {coords_str}")
            else:
                logger.warning(f"AI failed to generate NPC details for location {coords_str}.")
        else:
             logger.info(f"Skipping NPC generation for location {coords_str} (chance not met).")

        # --- Create image prompt including items/NPCs --- 
        image_prompt = f"{location_desc} Setting: {setting}. Style: photorealistic."
        if item_names_for_prompt:
            image_prompt += f" Items visible: {', '.join(item_names_for_prompt)}."
        if npc_names_for_prompt:
            image_prompt += f" People present: {', '.join(npc_names_for_prompt)}."
            
        # --- Define basic structure --- 
        return {
            "id": location_id,
            "name": location_name,
            "japanese_name": location_jp_name,
            "description": location_desc,
            "setting": setting,
            "coords": coords,
            "exits": {}, 
            "items": new_items,
            "npcs": new_npcs, # List contains IDs of generated NPCs
            "image_prompt": image_prompt 
        }

    # --- Helper for AI Availability (Checks OpenAI key now) --- 
    def is_ai_available(self) -> bool:
        """Check if the primary AI key (OpenAI) is present."""
        return bool(os.getenv("OPENAI_API_KEY"))

    def _coords_to_str(self, coords: tuple) -> str:
        """Convert coordinates to a string format"""
        return f"{coords[0]},{coords[1]}"

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
        
        # Show initial location using the refactored helper
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