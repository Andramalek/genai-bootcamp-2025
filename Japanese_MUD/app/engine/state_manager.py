from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from app.engine.command_parser import Command
from app.models.player import Player
from app.models.location import Location
from app.models.item import Item
from app.models.npc import NPC
from app.utils.logger import game_logger
from app.language.vocabulary import VocabularyWord

@dataclass
class StateUpdate:
    """
    Represents an update to the game state
    """
    message: str
    new_location: bool = False
    location: Optional[Location] = None
    items_added: List[Item] = None
    items_removed: List[Item] = None
    vocabulary_word: Optional[VocabularyWord] = None
    show_image: bool = False

class StateManager:
    """
    Manages the game state and processes commands
    """
    def __init__(self):
        """
        Initialize the state manager
        """
        # Cache data to avoid reloading from files
        self.locations_cache = Location.load_all_locations()
        self.items_cache = Item.load_all_items()
        self.npcs_cache = NPC.load_all_npcs()
        
        game_logger.info("StateManager initialized")

    async def execute_command(self, command: Command, player: Player) -> StateUpdate:
        """
        Execute a command and update the game state
        
        Args:
            command: The command to execute
            player: The player executing the command
            
        Returns:
            StateUpdate object with the results of the command
        """
        # If command is not valid, return error message
        if not command.is_valid:
            return StateUpdate(message=command.error_message or "Invalid command")
        
        # Handle different command types
        handlers = {
            "look": self._handle_look,
            "move": self._handle_move,
            "take": self._handle_take,
            "drop": self._handle_drop,
            "talk": self._handle_talk,
            "say": self._handle_talk,
            "use": self._handle_use,
            "inventory": self._handle_inventory,
            "help": self._handle_help,
            "quit": self._handle_quit,
            "exit": self._handle_quit
        }
        
        handler = handlers.get(command.action)
        if not handler:
            return StateUpdate(message=f"I don't know how to {command.action}.")
            
        return await handler(command, player)
    
    async def _handle_look(self, command: Command, player: Player) -> StateUpdate:
        """
        Handle the 'look' command
        
        Args:
            command: The command to execute
            player: The player executing the command
            
        Returns:
            StateUpdate with the description of the current location
        """
        # Get the player's current location
        location = Location.get_by_id(player.location_id, self.locations_cache)
        if not location:
            return StateUpdate(message="You are in a void. Something went wrong.")
            
        # If player specifies a target, look at that item or NPC
        if command.target:
            # Check if it's an item in the location
            item = self._find_item_in_location(command.target, location)
            if item:
                return StateUpdate(
                    message=f"{item.name}: {item.description}"
                )
                
            # Check if it's an item in inventory
            item = self._find_item_in_inventory(command.target, player)
            if item:
                return StateUpdate(
                    message=f"{item.name} (in your inventory): {item.description}"
                )
                
            # Check if it's an NPC
            npc = self._find_npc_in_location(command.target, location)
            if npc:
                return StateUpdate(
                    message=f"{npc.name}: {npc.description}"
                )
                
            # Check if it's a direction
            if command.target in ["north", "south", "east", "west", "up", "down"]:
                exit_location = location.get_exit_location(command.target, self.locations_cache)
                if exit_location:
                    return StateUpdate(
                        message=f"You see {exit_location.name} to the {command.target}."
                    )
                else:
                    return StateUpdate(
                        message=f"There is no exit to the {command.target}."
                    )
            
            return StateUpdate(
                message=f"You don't see any '{command.target}' here."
            )
        
        # Get items and NPCs in the location
        items_desc = ""
        if location.items:
            item_names = [Item.get_by_id(item_id, self.items_cache).name 
                         for item_id in location.items 
                         if Item.get_by_id(item_id, self.items_cache)]
            if item_names:
                items_desc = f"\nYou see: {', '.join(item_names)}."
                
        npcs_desc = ""
        if location.npcs:
            npc_names = [NPC.get_by_id(npc_id, self.npcs_cache).name 
                        for npc_id in location.npcs 
                        if NPC.get_by_id(npc_id, self.npcs_cache)]
            if npc_names:
                npcs_desc = f"\nPeople here: {', '.join(npc_names)}."
                
        exits_desc = ""
        if location.exits:
            exits_desc = f"\nExits: {', '.join(location.exits.keys())}."
            
        # Construct the full description
        full_desc = f"{location.name}\n\n{location.description}{items_desc}{npcs_desc}{exits_desc}"
        
        return StateUpdate(
            message=full_desc,
            location=location,
            show_image=True
        )
    
    async def _handle_move(self, command: Command, player: Player) -> StateUpdate:
        """
        Handle the 'move' command
        
        Args:
            command: The command to execute
            player: The player executing the command
            
        Returns:
            StateUpdate with the result of the movement
        """
        if not command.target:
            return StateUpdate(
                message="Which direction do you want to move? Try 'north', 'south', 'east', or 'west'."
            )
            
        # Get the player's current location
        location = Location.get_by_id(player.location_id, self.locations_cache)
        if not location:
            return StateUpdate(message="You are in a void. Something went wrong.")
            
        # Check if there's an exit in that direction
        direction = command.target.lower()
        if direction not in location.exits:
            return StateUpdate(
                message=f"There is no exit to the {direction}."
            )
            
        # Move to the new location
        new_location_id = location.exits[direction]
        new_location = Location.get_by_id(new_location_id, self.locations_cache)
        if not new_location:
            return StateUpdate(
                message="That location doesn't exist. Something went wrong."
            )
            
        # Update player's location
        player.location_id = new_location_id
        player.save()
        
        # Get items and NPCs in the new location
        items_desc = ""
        if new_location.items:
            item_names = [Item.get_by_id(item_id, self.items_cache).name 
                         for item_id in new_location.items 
                         if Item.get_by_id(item_id, self.items_cache)]
            if item_names:
                items_desc = f"\nYou see: {', '.join(item_names)}."
                
        npcs_desc = ""
        if new_location.npcs:
            npc_names = [NPC.get_by_id(npc_id, self.npcs_cache).name 
                        for npc_id in new_location.npcs 
                        if NPC.get_by_id(npc_id, self.npcs_cache)]
            if npc_names:
                npcs_desc = f"\nPeople here: {', '.join(npc_names)}."
                
        exits_desc = ""
        if new_location.exits:
            exits_desc = f"\nExits: {', '.join(new_location.exits.keys())}."
            
        # Construct the full description
        full_desc = f"{new_location.name}\n\n{new_location.description}{items_desc}{npcs_desc}{exits_desc}"
        
        # Return update with new location info
        return StateUpdate(
            message=full_desc,
            new_location=True,
            location=new_location,
            show_image=True
        )
    
    async def _handle_take(self, command: Command, player: Player) -> StateUpdate:
        """
        Handle the 'take' command
        
        Args:
            command: The command to execute
            player: The player executing the command
            
        Returns:
            StateUpdate with the result of taking an item
        """
        if not command.target:
            return StateUpdate(
                message="What do you want to take?"
            )
            
        # Get the player's current location
        location = Location.get_by_id(player.location_id, self.locations_cache)
        if not location:
            return StateUpdate(message="You are in a void. Something went wrong.")
            
        # Find the item in the location
        item = self._find_item_in_location(command.target, location)
        if not item:
            return StateUpdate(
                message=f"There is no '{command.target}' here."
            )
            
        # Check if the item can be taken
        if not item.can_be_taken:
            return StateUpdate(
                message=f"You can't take the {item.name}."
            )
            
        # Remove the item from the location
        location.remove_item(item.id)
        
        # Add the item to the player's inventory
        player.add_to_inventory(item.id)
        
        return StateUpdate(
            message=f"You take the {item.name}.",
            items_added=[item]
        )
    
    async def _handle_drop(self, command: Command, player: Player) -> StateUpdate:
        """
        Handle the 'drop' command
        
        Args:
            command: The command to execute
            player: The player executing the command
            
        Returns:
            StateUpdate with the result of dropping an item
        """
        if not command.target:
            return StateUpdate(
                message="What do you want to drop?"
            )
            
        # Get the player's current location
        location = Location.get_by_id(player.location_id, self.locations_cache)
        if not location:
            return StateUpdate(message="You are in a void. Something went wrong.")
            
        # Find the item in the player's inventory
        item = self._find_item_in_inventory(command.target, player)
        if not item:
            return StateUpdate(
                message=f"You don't have a '{command.target}'."
            )
            
        # Remove the item from the player's inventory
        player.remove_from_inventory(item.id)
        
        # Add the item to the location
        location.add_item(item.id)
        
        return StateUpdate(
            message=f"You drop the {item.name}.",
            items_removed=[item]
        )
    
    async def _handle_talk(self, command: Command, player: Player) -> StateUpdate:
        """
        Handle the 'talk' command
        
        Args:
            command: The command to execute
            player: The player executing the command
            
        Returns:
            StateUpdate with the result of talking to an NPC
        """
        if not command.target:
            return StateUpdate(
                message="Who do you want to talk to?"
            )
            
        # Get the player's current location
        location = Location.get_by_id(player.location_id, self.locations_cache)
        if not location:
            return StateUpdate(message="You are in a void. Something went wrong.")
            
        # Find the NPC in the location
        npc = self._find_npc_in_location(command.target, location)
        if not npc:
            return StateUpdate(
                message=f"There is no '{command.target}' here to talk to."
            )
            
        # Get the NPC's dialogue
        dialogue = npc.get_dialogue("greeting")
        
        return StateUpdate(
            message=f"{npc.name}: \"{dialogue}\""
        )
    
    async def _handle_use(self, command: Command, player: Player) -> StateUpdate:
        """
        Handle the 'use' command
        
        Args:
            command: The command to execute
            player: The player executing the command
            
        Returns:
            StateUpdate with the result of using an item
        """
        if not command.target:
            return StateUpdate(
                message="What do you want to use?"
            )
            
        # Find the item in the player's inventory
        item = self._find_item_in_inventory(command.target, player)
        if not item:
            return StateUpdate(
                message=f"You don't have a '{command.target}'."
            )
            
        # Check if the item can be used
        if not item.can_be_used:
            return StateUpdate(
                message=f"You can't use the {item.name}."
            )
            
        # Handle different item types
        if item.item_type == "drink":
            return StateUpdate(
                message=f"You drink the {item.name}. It's refreshing!"
            )
        elif item.item_type == "food":
            return StateUpdate(
                message=f"You eat the {item.name}. Delicious!"
            )
        elif item.item_type == "book":
            return StateUpdate(
                message=f"You read the {item.name}. You learn something new!"
            )
        elif item.item_type == "map":
            return StateUpdate(
                message=f"You look at the {item.name}. It shows your current location and nearby areas."
            )
        else:
            return StateUpdate(
                message=f"You use the {item.name}."
            )
    
    async def _handle_inventory(self, command: Command, player: Player) -> StateUpdate:
        """
        Handle the 'inventory' command
        
        Args:
            command: The command to execute
            player: The player executing the command
            
        Returns:
            StateUpdate with the player's inventory
        """
        if not player.inventory:
            return StateUpdate(
                message="Your inventory is empty."
            )
            
        # Get item names
        item_names = []
        for item_id in player.inventory:
            item = Item.get_by_id(item_id, self.items_cache)
            if item:
                item_names.append(item.name)
                
        inventory_str = ", ".join(item_names)
        return StateUpdate(
            message=f"Your inventory: {inventory_str}"
        )
    
    async def _handle_help(self, command: Command, player: Player) -> StateUpdate:
        """
        Handle the 'help' command
        
        Args:
            command: The command to execute
            player: The player executing the command
            
        Returns:
            StateUpdate with help information
        """
        help_text = """Available commands:
- look [object/direction]: Examine your surroundings or an object
- move [direction] or just [north/south/east/west]: Travel in that direction
- take [item]: Pick up an item
- drop [item]: Drop an item
- talk [npc]: Talk to someone
- use [item]: Use an item
- inventory: Check what you're carrying
- help: Show this message
- quit/exit: Exit the game

As you explore, you'll learn Japanese vocabulary. Try to use these words when interacting with NPCs!"""
        
        return StateUpdate(
            message=help_text
        )
    
    async def _handle_quit(self, command: Command, player: Player) -> StateUpdate:
        """
        Handle the 'quit' command
        
        Args:
            command: The command to execute
            player: The player executing the command
            
        Returns:
            StateUpdate with quit message
        """
        return StateUpdate(
            message="Thank you for playing! さようなら！"
        )
    
    def _find_item_in_location(self, item_name: str, location: Location) -> Optional[Item]:
        """
        Find an item in a location by name
        
        Args:
            item_name: Name of the item to find
            location: Location to search in
            
        Returns:
            Item object if found, None otherwise
        """
        for item_id in location.items:
            item = Item.get_by_id(item_id, self.items_cache)
            if item and (item_name.lower() in item.name.lower()):
                return item
        return None
    
    def _find_item_in_inventory(self, item_name: str, player: Player) -> Optional[Item]:
        """
        Find an item in a player's inventory by name
        
        Args:
            item_name: Name of the item to find
            player: Player whose inventory to search
            
        Returns:
            Item object if found, None otherwise
        """
        for item_id in player.inventory:
            item = Item.get_by_id(item_id, self.items_cache)
            if item and (item_name.lower() in item.name.lower()):
                return item
        return None
    
    def _find_npc_in_location(self, npc_name: str, location: Location) -> Optional[NPC]:
        """
        Find an NPC in a location by name
        
        Args:
            npc_name: Name of the NPC to find
            location: Location to search in
            
        Returns:
            NPC object if found, None otherwise
        """
        for npc_id in location.npcs:
            npc = NPC.get_by_id(npc_id, self.npcs_cache)
            if npc and (npc_name.lower() in npc.name.lower()):
                return npc
        return None 