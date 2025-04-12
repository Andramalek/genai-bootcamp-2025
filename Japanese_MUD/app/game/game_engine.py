import os
import random
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from app.utils.logger import game_logger
from app.utils.helpers import load_json_file
from app.player.player import Player
from app.utils.ai_integration import AIManager
from app.ui.image_display import ImageDisplay

class GameState:
    """Class to track the current state of the game"""
    def __init__(self):
        self.locations: Dict = {}
        self.items: Dict = {}
        self.npcs: Dict = {}
        self.players: Dict[str, Player] = {}
        self.current_player_id: Optional[str] = None
        self.vocabulary: Dict = {}
        self.loading_complete = False
        
    def get_current_player(self) -> Optional[Player]:
        """Get the current active player"""
        if not self.current_player_id:
            return None
        return self.players.get(self.current_player_id)
    
    def get_current_location(self) -> Optional[Dict]:
        """Get the current location for the active player"""
        player = self.get_current_player()
        if not player:
            return None
        return self.locations.get(player.progress.current_location_id)
    
    def get_location_items(self, location_id: str) -> List[Dict]:
        """Get all items in a location"""
        location = self.locations.get(location_id)
        if not location:
            return []
            
        return [self.items.get(item_id) for item_id in location.get("items", []) 
                if item_id in self.items]
    
    def get_location_npcs(self, location_id: str) -> List[Dict]:
        """Get all NPCs in a location"""
        location = self.locations.get(location_id)
        if not location:
            return []
            
        return [self.npcs.get(npc_id) for npc_id in location.get("npcs", []) 
                if npc_id in self.npcs]

class CommandParser:
    """Parser for game commands"""
    # Basic command patterns
    COMMAND_PATTERNS = {
        "look": ["look", "examine", "観る", "見る"],
        "go": ["go", "move", "walk", "行く", "歩く"],
        "take": ["take", "pick up", "get", "取る", "拾う"],
        "inventory": ["inventory", "items", "持ち物", "アイテム"],
        "talk": ["talk", "speak", "chat", "話す", "喋る"],
        "help": ["help", "commands", "ヘルプ", "コマンド"],
        "quit": ["quit", "exit", "終了", "やめる"],
        "save": ["save", "保存"],
        "learn": ["learn", "study", "勉強", "学ぶ"],
        "vocabulary": ["vocabulary", "words", "vocab", "単語"]
    }
    
    @staticmethod
    def parse_command(command_text: str) -> Tuple[str, List[str]]:
        """
        Parse a command string into a command type and arguments
        
        Args:
            command_text: The raw command string
            
        Returns:
            Tuple of (command_type, arguments)
        """
        # Normalize and split the input
        command_text = command_text.lower().strip()
        parts = command_text.split()
        
        if not parts:
            return ("unknown", [])
            
        # Try to match the first word to a command pattern
        first_word = parts[0]
        
        for command_type, patterns in CommandParser.COMMAND_PATTERNS.items():
            if first_word in patterns:
                # Return the command type and the rest as arguments
                return (command_type, parts[1:])
        
        # Check if the first two words form a command (like "pick up")
        if len(parts) >= 2:
            first_two = f"{parts[0]} {parts[1]}"
            
            for command_type, patterns in CommandParser.COMMAND_PATTERNS.items():
                if first_two in patterns:
                    # Return the command type and the rest as arguments
                    return (command_type, parts[2:])
        
        # If no match found, return unknown command
        return ("unknown", parts)

class GameEngine:
    """Main engine for the Japanese MUD game"""
    def __init__(self):
        self.state = GameState()
        self.command_parser = CommandParser()
        self.running = False
        
    async def load_game_data(self):
        """Load all game data from JSON files"""
        try:
            # Load locations
            locations_file = "data/game_templates/locations.json"
            locations_data = load_json_file(locations_file)
            
            for location in locations_data:
                self.state.locations[location["id"]] = location
                # Generate and cache images for locations
                self._generate_location_image(location)
            
            # Load items
            items_file = "data/game_templates/items.json"
            items_data = load_json_file(items_file)
            
            for item in items_data:
                self.state.items[item["id"]] = item
                # Generate and cache images for items
                self._generate_item_image(item)
            
            # Load NPCs
            npcs_file = "data/game_templates/npcs.json"
            npcs_data = load_json_file(npcs_file)
            
            for npc in npcs_data:
                self.state.npcs[npc["id"]] = npc
                # Generate and cache images for NPCs
                self._generate_npc_image(npc)
            
            # Load vocabulary
            vocab_file = "data/vocabulary/jlpt_n5.json"
            vocab_data = load_json_file(vocab_file)
            
            for word in vocab_data:
                self.state.vocabulary[word["id"]] = word
            
            # Mark loading as complete
            self.state.loading_complete = True
            
        except Exception as e:
            game_logger.error(f"Error loading game data: {str(e)}")
            raise
    
    def _generate_location_image(self, location: Dict):
        """Generate and cache an image for a location"""
        try:
            # Check if we already have an image for this location
            location_id = location["id"]
            cache_key = f"location:{location_id}"
            cached_path = ImageDisplay.get_cached_image(cache_key)
            
            if cached_path and os.path.exists(cached_path):
                return
                
            # Generate a new image
            image_path = AIManager.generate_location_image(
                location["name"], 
                location["description"]
            )
            
            if image_path:
                ImageDisplay.cache_image(cache_key, image_path)
                
        except Exception as e:
            game_logger.error(f"Error generating location image: {str(e)}")
    
    def _generate_item_image(self, item: Dict):
        """Generate and cache an image for an item"""
        try:
            # Check if we already have an image for this item
            item_id = item["id"]
            cache_key = f"item:{item_id}"
            cached_path = ImageDisplay.get_cached_image(cache_key)
            
            if cached_path and os.path.exists(cached_path):
                return
                
            # Generate a new image
            image_path = AIManager.generate_item_image(
                item["name"], 
                item["description"]
            )
            
            if image_path:
                ImageDisplay.cache_image(cache_key, image_path)
                
        except Exception as e:
            game_logger.error(f"Error generating item image: {str(e)}")
    
    def _generate_npc_image(self, npc: Dict):
        """Generate and cache an image for an NPC"""
        try:
            # Check if we already have an image for this NPC
            npc_id = npc["id"]
            cache_key = f"npc:{npc_id}"
            cached_path = ImageDisplay.get_cached_image(cache_key)
            
            if cached_path and os.path.exists(cached_path):
                return
                
            # Generate a new image
            image_path = AIManager.generate_npc_image(
                npc["name"], 
                npc["description"]
            )
            
            if image_path:
                ImageDisplay.cache_image(cache_key, image_path)
                
        except Exception as e:
            game_logger.error(f"Error generating NPC image: {str(e)}")
    
    def display_location_image(self, location_id: str):
        """Display the image for a location"""
        cache_key = f"location:{location_id}"
        image_path = ImageDisplay.get_cached_image(cache_key)
        
        if image_path and os.path.exists(image_path):
            ImageDisplay.show_location_image(location_id, image_path)
    
    def display_item_image(self, item_id: str):
        """Display the image for an item"""
        cache_key = f"item:{item_id}"
        image_path = ImageDisplay.get_cached_image(cache_key)
        
        if image_path and os.path.exists(image_path):
            ImageDisplay.show_item_image(item_id, image_path)
    
    def display_npc_image(self, npc_id: str):
        """Display the image for an NPC"""
        cache_key = f"npc:{npc_id}"
        image_path = ImageDisplay.get_cached_image(cache_key)
        
        if image_path and os.path.exists(image_path):
            ImageDisplay.show_npc_image(npc_id, image_path)
    
    def create_player(self, username: str, jlpt_level: str = "N5") -> Player:
        """Create a new player"""
        player = Player(username=username, jlpt_level=jlpt_level)
        self.state.players[player.player_id] = player
        self.state.current_player_id = player.player_id
        
        # Set starting location
        for loc_id, location in self.state.locations.items():
            if location.get("is_starting_location", False):
                player.visit_location(loc_id)
                break
        
        # If no starting location found, use the first location
        if not player.progress.current_location_id and self.state.locations:
            first_location = next(iter(self.state.locations))
            player.visit_location(first_location)
        
        return player
    
    def load_player(self, player_id: str) -> Optional[Player]:
        """Load an existing player"""
        player = Player.load(player_id)
        if player:
            self.state.players[player.player_id] = player
            self.state.current_player_id = player.player_id
        return player
    
    def save_game(self) -> bool:
        """Save the current game state"""
        player = self.state.get_current_player()
        if not player:
            return False
        
        return player.save()
    
    def get_location_description(self, location_id: str) -> str:
        """Get the full description for a location, including items and NPCs"""
        location = self.state.locations.get(location_id)
        if not location:
            return "This place doesn't exist."
        
        # Basic location description
        description = f"**{location.get('name')}** ({location.get('japanese_name', '')})\n\n"
        description += f"{location.get('description', '')}\n\n"
        
        # Show cultural note if available
        if "cultural_note" in location:
            description += f"Cultural Note: {location['cultural_note']}\n\n"
        
        # List exits
        exits = location.get("exits", {})
        if exits:
            description += "Exits: "
            exit_list = [f"{direction.capitalize()} to {self.state.locations.get(exit_loc, {}).get('name', 'Unknown')}" 
                         for direction, exit_loc in exits.items()]
            description += ", ".join(exit_list) + "\n\n"
        
        # List items
        items = self.state.get_location_items(location_id)
        if items:
            description += "Items: "
            item_list = [f"{item.get('name', 'Unknown Item')} ({item.get('japanese_name', '')})" 
                         for item in items]
            description += ", ".join(item_list) + "\n\n"
        
        # List NPCs
        npcs = self.state.get_location_npcs(location_id)
        if npcs:
            description += "People: "
            npc_list = [f"{npc.get('name', 'Unknown Person')} ({npc.get('japanese_name', '')})" 
                        for npc in npcs]
            description += ", ".join(npc_list) + "\n"
        
        return description
    
    def process_look_command(self, args: List[str]) -> str:
        """Process the 'look' command"""
        player = self.state.get_current_player()
        if not player:
            return "No active player."
        
        location_id = player.progress.current_location_id
        
        # If no args, look at the current location
        if not args:
            # Display the location image
            self.display_location_image(location_id)
            
            # Return the location description
            return self.get_location_description(location_id)
        
        # Handle looking at specific items or NPCs
        target = " ".join(args)
        
        # Check items in location
        items = self.state.get_location_items(location_id)
        for item in items:
            if target.lower() in item.get("name", "").lower() or \
               target.lower() in item.get("japanese_name", "").lower():
                # Display the item image
                self.display_item_image(item["id"])
                
                # Show vocabulary word if linked
                vocab_note = ""
                if "vocabulary_id" in item and item["vocabulary_id"] in self.state.vocabulary:
                    vocab = self.state.vocabulary[item["vocabulary_id"]]
                    vocab_note = f"\n\nVocabulary: {vocab.get('japanese', '')} ({vocab.get('romaji', '')}) - {vocab.get('english', '')}"
                    
                    # Mark word as seen
                    player.vocabulary.mark_word_seen(item["vocabulary_id"])
                
                return f"**{item.get('name')}** ({item.get('japanese_name', '')})\n\n{item.get('description', '')}{vocab_note}"
        
        # Check NPCs in location
        npcs = self.state.get_location_npcs(location_id)
        for npc in npcs:
            if target.lower() in npc.get("name", "").lower() or \
               target.lower() in npc.get("japanese_name", "").lower():
                # Display the NPC image
                self.display_npc_image(npc["id"])
                
                # Show vocabulary word if linked
                vocab_note = ""
                if "vocabulary_id" in npc and npc["vocabulary_id"] in self.state.vocabulary:
                    vocab = self.state.vocabulary[npc["vocabulary_id"]]
                    vocab_note = f"\n\nVocabulary: {vocab.get('japanese', '')} ({vocab.get('romaji', '')}) - {vocab.get('english', '')}"
                    
                    # Mark word as seen
                    player.vocabulary.mark_word_seen(npc["vocabulary_id"])
                
                return f"**{npc.get('name')}** ({npc.get('japanese_name', '')})\n\n{npc.get('description', '')}{vocab_note}"
        
        return f"You don't see '{target}' here."
    
    def process_go_command(self, args: List[str]) -> str:
        """Process the 'go' command"""
        player = self.state.get_current_player()
        if not player:
            return "No active player."
        
        if not args:
            return "Go where? Please specify a direction (north, south, east, west)."
        
        direction = args[0].lower()
        current_location = self.state.get_current_location()
        
        if not current_location:
            return "You are nowhere. This is strange..."
        
        exits = current_location.get("exits", {})
        
        if direction not in exits:
            return f"You cannot go {direction} from here."
        
        # Move to the new location
        new_location_id = exits[direction]
        player.visit_location(new_location_id)
        
        # Check for vocabulary at the new location
        new_location = self.state.locations.get(new_location_id)
        if new_location and "vocabulary_id" in new_location:
            vocab_id = new_location["vocabulary_id"]
            if vocab_id in self.state.vocabulary:
                player.vocabulary.mark_word_seen(vocab_id)
        
        # Display the location image
        self.display_location_image(new_location_id)
        
        # Return the new location description
        return self.get_location_description(new_location_id)
    
    def process_take_command(self, args: List[str]) -> str:
        """Process the 'take' command"""
        player = self.state.get_current_player()
        if not player:
            return "No active player."
        
        if not args:
            return "Take what? Please specify an item."
        
        item_name = " ".join(args).lower()
        location_id = player.progress.current_location_id
        
        # Check items in location
        items = self.state.get_location_items(location_id)
        for item in items:
            if item_name in item.get("name", "").lower() or \
               item_name in item.get("japanese_name", "").lower():
                
                # Check if item can be taken
                if not item.get("is_takeable", False):
                    return f"You cannot take the {item.get('name')}."
                
                # Add to inventory
                if player.add_to_inventory(item["id"]):
                    # Remove from location
                    location = self.state.locations[location_id]
                    if item["id"] in location.get("items", []):
                        location["items"].remove(item["id"])
                    
                    # Display the item image
                    self.display_item_image(item["id"])
                    
                    return f"You take the {item.get('name')} ({item.get('japanese_name', '')})."
                else:
                    return f"You already have the {item.get('name')}."
        
        return f"You don't see '{item_name}' here."
    
    def process_inventory_command(self, args: List[str]) -> str:
        """Process the 'inventory' command"""
        player = self.state.get_current_player()
        if not player:
            return "No active player."
        
        if not player.progress.inventory:
            return "Your inventory is empty."
        
        inventory_list = []
        for item_id in player.progress.inventory:
            item = self.state.items.get(item_id)
            if item:
                inventory_list.append(f"**{item.get('name')}** ({item.get('japanese_name', '')})")
                
                # If the player specified an item to examine
                if args and " ".join(args).lower() in item.get("name", "").lower():
                    # Display the item image
                    self.display_item_image(item_id)
        
        return "Inventory:\n" + "\n".join(inventory_list)
    
    def process_talk_command(self, args: List[str]) -> str:
        """Process the 'talk' command"""
        player = self.state.get_current_player()
        if not player:
            return "No active player."
        
        if not args:
            return "Talk to whom? Please specify a person."
        
        npc_name = " ".join(args).lower()
        location_id = player.progress.current_location_id
        
        # Check NPCs in location
        npcs = self.state.get_location_npcs(location_id)
        for npc in npcs:
            if npc_name in npc.get("name", "").lower() or \
               npc_name in npc.get("japanese_name", "").lower():
                
                # Record the interaction
                player.record_npc_interaction(npc["id"])
                
                # Display the NPC image
                self.display_npc_image(npc["id"])
                
                # Get appropriate dialogue
                interaction_count = player.get_npc_interaction_count(npc["id"])
                dialog = npc.get("dialog", {})
                
                if interaction_count == 1:
                    # First interaction, use greeting
                    response = dialog.get("greeting", "Hello.")
                elif interaction_count % 3 == 0:
                    # Every third interaction, teach something
                    response = dialog.get("learn", "I have nothing to teach you right now.")
                else:
                    # Other interactions, give hints
                    response = dialog.get("hint", "I have nothing else to say.")
                
                # Check for vocabulary
                if "vocabulary_id" in npc and npc["vocabulary_id"] in self.state.vocabulary:
                    vocab_id = npc["vocabulary_id"]
                    vocab = self.state.vocabulary[vocab_id]
                    
                    # Mark word as seen
                    player.vocabulary.mark_word_seen(vocab_id)
                    
                    # Add vocabulary info to response
                    response += f"\n\nVocabulary: {vocab.get('japanese', '')} ({vocab.get('romaji', '')}) - {vocab.get('english', '')}"
                
                return f"**{npc.get('name')}** ({npc.get('japanese_name', '')}) says:\n\n{response}"
        
        return f"You don't see '{npc_name}' here to talk to."
    
    def process_help_command(self, args: List[str]) -> str:
        """Process the 'help' command"""
        help_text = """
**Japanese MUD Commands:**

- **look** or **examine** [object/person]: Look at your surroundings or a specific object/person
- **go** [direction]: Move in a direction (north, south, east, west)
- **take** [item]: Pick up an item
- **inventory** or **items**: Check what items you're carrying
- **talk** or **speak** [person]: Talk to an NPC
- **learn** [word]: Practice a vocabulary word you've seen
- **vocabulary**: Check your vocabulary progress
- **save**: Save your game progress
- **help**: Show this help message
- **quit** or **exit**: Exit the game

Japanese commands are also supported (見る, 行く, 取る, etc.)
"""
        return help_text
    
    def process_command(self, command_text: str) -> str:
        """Process a command from the player"""
        command_type, args = self.command_parser.parse_command(command_text)
        
        # Process the command based on its type
        if command_type == "look":
            return self.process_look_command(args)
        elif command_type == "go":
            return self.process_go_command(args)
        elif command_type == "take":
            return self.process_take_command(args)
        elif command_type == "inventory":
            return self.process_inventory_command(args)
        elif command_type == "talk":
            return self.process_talk_command(args)
        elif command_type == "help":
            return self.process_help_command(args)
        elif command_type == "save":
            if self.save_game():
                return "Game saved successfully."
            else:
                return "Failed to save the game."
        elif command_type == "quit":
            self.running = False
            return "Exiting game. Thanks for playing!"
        elif command_type == "unknown":
            return f"I don't understand '{command_text}'. Type 'help' for a list of commands."
        else:
            return f"Command '{command_type}' not implemented yet."
    
    async def start_game(self, player_id: Optional[str] = None):
        """Start the game with either a new or existing player"""
        # Load game data
        await self.load_game_data()
        
        self.running = True 