from typing import Dict, List, Optional
import os
from app.utils.logger import game_logger
from app.utils.helpers import load_json_file

class Item:
    """
    Represents an item in the game
    """
    def __init__(self,
                 id: str,
                 name: str,
                 description: str,
                 item_type: str,
                 can_be_taken: bool = True,
                 can_be_used: bool = False,
                 vocabulary_word_id: str = None):
        """
        Initialize an item
        
        Args:
            id: Unique identifier for the item
            name: Name of the item
            description: Description of the item
            item_type: Type of item (e.g., "weapon", "food", "book")
            can_be_taken: Whether the item can be picked up
            can_be_used: Whether the item can be used
            vocabulary_word_id: ID of vocabulary word associated with this item
        """
        self.id = id
        self.name = name
        self.description = description
        self.item_type = item_type
        self.can_be_taken = can_be_taken
        self.can_be_used = can_be_used
        self.vocabulary_word_id = vocabulary_word_id
    
    @classmethod
    def load_all_items(cls) -> Dict[str, 'Item']:
        """
        Load all items from the template file
        
        Returns:
            Dict mapping item IDs to Item objects
        """
        from app.config import Config
        config = Config()
        
        items_file = os.path.join(config.GAME_TEMPLATES_DIR, "items.json")
        try:
            items_data = load_json_file(items_file)
            items = {}
            
            for item_data in items_data:
                item = cls(
                    id=item_data.get("id"),
                    name=item_data.get("name"),
                    description=item_data.get("description"),
                    item_type=item_data.get("item_type"),
                    can_be_taken=item_data.get("can_be_taken", True),
                    can_be_used=item_data.get("can_be_used", False),
                    vocabulary_word_id=item_data.get("vocabulary_word_id")
                )
                items[item.id] = item
                
            game_logger.info(f"Loaded {len(items)} items")
            return items
            
        except Exception as e:
            game_logger.error(f"Error loading items: {str(e)}")
            return {}
    
    @classmethod
    def get_by_id(cls, item_id: str, items_cache: Dict[str, 'Item'] = None) -> Optional['Item']:
        """
        Get an item by ID
        
        Args:
            item_id: ID of the item
            items_cache: Dict of already loaded items (optional)
            
        Returns:
            Item object if found, None otherwise
        """
        # Use provided cache or load all items
        items = items_cache or cls.load_all_items()
        return items.get(item_id)
    
    @classmethod
    def get_by_name(cls, item_name: str, items_cache: Dict[str, 'Item'] = None) -> Optional['Item']:
        """
        Get an item by name (case-insensitive partial match)
        
        Args:
            item_name: Name of the item to search for
            items_cache: Dict of already loaded items (optional)
            
        Returns:
            First matching Item object, or None if not found
        """
        # Use provided cache or load all items
        items = items_cache or cls.load_all_items()
        item_name_lower = item_name.lower()
        
        # First try exact match
        for item in items.values():
            if item.name.lower() == item_name_lower:
                return item
                
        # Then try partial match
        for item in items.values():
            if item_name_lower in item.name.lower():
                return item
                
        return None 