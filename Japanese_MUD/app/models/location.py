from typing import Dict, List, Optional
import os
from app.utils.logger import game_logger
from app.utils.helpers import load_json_file

class Location:
    """
    Represents a location in the game world
    """
    def __init__(self,
                 id: str,
                 name: str,
                 description: str,
                 setting: str = None,
                 is_starting_location: bool = False,
                 exits: Dict[str, str] = None,
                 items: List[str] = None,
                 npcs: List[str] = None,
                 vocabulary_word_id: str = None):
        """
        Initialize a location
        
        Args:
            id: Unique identifier for the location
            name: Name of the location
            description: Description of the location
            setting: Type of location (e.g., "temple", "market")
            is_starting_location: Whether this is a starting location
            exits: Dict mapping directions to location IDs
            items: List of item IDs present in the location
            npcs: List of NPC IDs present in the location
            vocabulary_word_id: ID of vocabulary word associated with this location
        """
        self.id = id
        self.name = name
        self.description = description
        self.setting = setting
        self.is_starting_location = is_starting_location
        self.exits = exits or {}
        self.items = items or []
        self.npcs = npcs or []
        self.vocabulary_word_id = vocabulary_word_id
        
    @classmethod
    def load_all_locations(cls) -> Dict[str, 'Location']:
        """
        Load all locations from the template file
        
        Returns:
            Dict mapping location IDs to Location objects
        """
        from app.config import Config
        config = Config()
        
        locations_file = os.path.join(config.GAME_TEMPLATES_DIR, "locations.json")
        try:
            locations_data = load_json_file(locations_file)
            locations = {}
            
            for location_data in locations_data:
                location = cls(
                    id=location_data.get("id"),
                    name=location_data.get("name"),
                    description=location_data.get("description"),
                    setting=location_data.get("setting"),
                    is_starting_location=location_data.get("is_starting_location", False),
                    exits=location_data.get("exits", {}),
                    items=location_data.get("items", []),
                    npcs=location_data.get("npcs", []),
                    vocabulary_word_id=location_data.get("vocabulary_word_id")
                )
                locations[location.id] = location
                
            game_logger.info(f"Loaded {len(locations)} locations")
            return locations
            
        except Exception as e:
            game_logger.error(f"Error loading locations: {str(e)}")
            return {}
    
    @classmethod
    def get_by_id(cls, location_id: str, locations_cache: Dict[str, 'Location'] = None) -> Optional['Location']:
        """
        Get a location by ID
        
        Args:
            location_id: ID of the location
            locations_cache: Dict of already loaded locations (optional)
            
        Returns:
            Location object if found, None otherwise
        """
        # Use provided cache or load all locations
        locations = locations_cache or cls.load_all_locations()
        return locations.get(location_id)
    
    @classmethod
    def get_starting_location(cls) -> Optional['Location']:
        """
        Get the starting location for new players
        
        Returns:
            Starting location if found, None otherwise
        """
        locations = cls.load_all_locations()
        
        # Find location with is_starting_location = True
        for location in locations.values():
            if location.is_starting_location:
                return location
                
        # If no starting location found, return first location as fallback
        if locations:
            return next(iter(locations.values()))
            
        return None
        
    def get_exit_location(self, direction: str, locations_cache: Dict[str, 'Location'] = None) -> Optional['Location']:
        """
        Get the location in the specified direction
        
        Args:
            direction: Direction to move ("north", "south", etc.)
            locations_cache: Dict of already loaded locations (optional)
            
        Returns:
            Location object in that direction, or None if no exit
        """
        if direction not in self.exits:
            return None
            
        exit_location_id = self.exits[direction]
        return self.get_by_id(exit_location_id, locations_cache)
    
    def add_item(self, item_id: str) -> None:
        """
        Add an item to the location
        
        Args:
            item_id: ID of the item to add
        """
        if item_id not in self.items:
            self.items.append(item_id)
    
    def remove_item(self, item_id: str) -> bool:
        """
        Remove an item from the location
        
        Args:
            item_id: ID of the item to remove
            
        Returns:
            True if item was removed, False if not found
        """
        if item_id in self.items:
            self.items.remove(item_id)
            return True
        return False 