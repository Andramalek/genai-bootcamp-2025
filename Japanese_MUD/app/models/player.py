from datetime import datetime
from typing import Dict, List, Optional
import os
import json
from app.utils.logger import game_logger
from app.utils.helpers import save_json_file, load_json_file

class Player:
    """
    Represents a player in the game
    """
    def __init__(self, 
                 player_id: str = None, 
                 username: str = None, 
                 location_id: str = None,
                 inventory: List[str] = None, 
                 jlpt_level: int = 5, 
                 learned_words: Dict[str, float] = None,
                 created_at: datetime = None, 
                 last_active: datetime = None):
        """
        Initialize a player
        
        Args:
            player_id: Unique identifier for the player
            username: Player's username
            location_id: ID of the player's current location
            inventory: List of item IDs in the player's inventory
            jlpt_level: Player's current JLPT level (5=N5, 1=N1)
            learned_words: Dict of word_id to proficiency level (0.0-1.0)
            created_at: Timestamp when the player was created
            last_active: Timestamp when the player was last active
        """
        self.player_id = player_id or username  # Use username as ID if not provided
        self.username = username
        self.location_id = location_id
        self.inventory = inventory or []
        self.jlpt_level = jlpt_level
        self.learned_words = learned_words or {}
        self.created_at = created_at or datetime.now().isoformat()
        self.last_active = last_active or datetime.now().isoformat()

    @staticmethod
    def get_save_path(player_id: str) -> str:
        """
        Get the file path for saving/loading player data
        
        Args:
            player_id: Player's unique identifier
            
        Returns:
            Path to the player's save file
        """
        from app.config import Config
        config = Config()
        return os.path.join(config.USER_DATA_DIR, f"{player_id}.json")

    @classmethod
    def load(cls, player_id: str) -> Optional['Player']:
        """
        Load a player from file
        
        Args:
            player_id: Player's unique identifier
            
        Returns:
            Player object if found, None otherwise
        """
        save_path = cls.get_save_path(player_id)
        if not os.path.exists(save_path):
            return None
            
        try:
            player_data = load_json_file(save_path)
            return cls(**player_data)
        except Exception as e:
            game_logger.error(f"Error loading player {player_id}: {str(e)}")
            return None

    @classmethod
    def create_new(cls, username: str, starting_location_id: str = "loc-001") -> 'Player':
        """
        Create a new player
        
        Args:
            username: Player's username
            starting_location_id: ID of the starting location
            
        Returns:
            New Player object
        """
        from app.config import Config
        config = Config()
        
        player = cls(
            player_id=username,
            username=username,
            location_id=starting_location_id,
            jlpt_level=config.STARTING_JLPT_LEVEL
        )
        player.save()
        game_logger.info(f"Created new player: {username}")
        return player

    def save(self) -> bool:
        """
        Save player data to file
        
        Returns:
            True if save was successful, False otherwise
        """
        try:
            save_path = self.get_save_path(self.player_id)
            
            # Convert to dict for saving
            player_dict = {
                "player_id": self.player_id,
                "username": self.username,
                "location_id": self.location_id,
                "inventory": self.inventory,
                "jlpt_level": self.jlpt_level,
                "learned_words": self.learned_words,
                "created_at": self.created_at,
                "last_active": datetime.now().isoformat()
            }
            
            save_json_file(save_path, player_dict)
            game_logger.debug(f"Saved player data for {self.username}")
            return True
        except Exception as e:
            game_logger.error(f"Error saving player {self.username}: {str(e)}")
            return False
    
    def add_to_inventory(self, item_id: str) -> bool:
        """
        Add an item to the player's inventory
        
        Args:
            item_id: ID of the item to add
            
        Returns:
            True if item was added, False if already in inventory
        """
        if item_id in self.inventory:
            return False
        
        self.inventory.append(item_id)
        self.save()
        return True
    
    def remove_from_inventory(self, item_id: str) -> bool:
        """
        Remove an item from the player's inventory
        
        Args:
            item_id: ID of the item to remove
            
        Returns:
            True if item was removed, False if not in inventory
        """
        if item_id not in self.inventory:
            return False
        
        self.inventory.remove(item_id)
        self.save()
        return True
    
    def learn_word(self, word_id: str, proficiency_increase: float = 0.2) -> float:
        """
        Increase a player's proficiency with a vocabulary word
        
        Args:
            word_id: ID of the vocabulary word
            proficiency_increase: Amount to increase proficiency by (0.0-1.0)
            
        Returns:
            New proficiency level for the word
        """
        current_proficiency = self.learned_words.get(word_id, 0.0)
        new_proficiency = min(1.0, current_proficiency + proficiency_increase)
        self.learned_words[word_id] = new_proficiency
        self.save()
        return new_proficiency 