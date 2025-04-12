from typing import Dict, List, Optional
import os
import json
from uuid import uuid4
from app.utils.logger import game_logger
from app.player.learning_tracker import PlayerVocabulary

class PlayerProgress:
    """Tracks player progress in the game"""
    def __init__(self):
        self.current_location_id: str = "start"
        self.visited_locations: List[str] = []
        self.inventory: List[str] = []
        self.quest_progress: Dict[str, str] = {}  # quest_id -> status
        self.npc_interactions: Dict[str, int] = {}  # npc_id -> interaction count

class Player:
    """Represents a player in the game"""
    def __init__(
        self, 
        username: str, 
        player_id: Optional[str] = None,
        jlpt_level: str = "N5"
    ):
        self.username = username
        self.player_id = player_id or str(uuid4())
        self.jlpt_level = jlpt_level
        self.progress = PlayerProgress()
        self.vocabulary = PlayerVocabulary(self.player_id)
        
    def get_save_path(self, player_id: str) -> str:
        """
        Get the path to save player data
        
        Args:
            player_id: The player's unique ID
            
        Returns:
            Path to save file
        """
        # Ensure the directory exists
        base_dir = os.path.join("data", "user_data")
        os.makedirs(base_dir, exist_ok=True)
        
        return os.path.join(base_dir, f"{player_id}.json")
    
    def save(self) -> bool:
        """
        Save player progress to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            save_path = self.get_save_path(self.player_id)
            player_dict = {
                "player_id": self.player_id,
                "username": self.username,
                "jlpt_level": self.jlpt_level,
                "progress": {
                    "current_location_id": self.progress.current_location_id,
                    "visited_locations": self.progress.visited_locations,
                    "inventory": self.progress.inventory,
                    "quest_progress": self.progress.quest_progress,
                    "npc_interactions": self.progress.npc_interactions
                }
            }
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(player_dict, f, ensure_ascii=False, indent=2)
                
            # Save vocabulary separately
            self.vocabulary.save()
            
            return True
            
        except Exception as e:
            game_logger.error(f"Error saving player {self.username}: {str(e)}")
            return False
    
    @classmethod
    def load(cls, player_id: str) -> Optional['Player']:
        """
        Load player from save file
        
        Args:
            player_id: The player's unique ID
            
        Returns:
            Player object if successful, None otherwise
        """
        try:
            save_path = cls.get_save_path(cls, player_id)
            
            if not os.path.exists(save_path):
                game_logger.error(f"No save file found for player ID: {player_id}")
                return None
                
            with open(save_path, 'r', encoding='utf-8') as f:
                player_dict = json.load(f)
                
            player = cls(
                username=player_dict["username"],
                player_id=player_dict["player_id"],
                jlpt_level=player_dict.get("jlpt_level", "N5")
            )
            
            # Load progress
            progress_dict = player_dict.get("progress", {})
            player.progress.current_location_id = progress_dict.get("current_location_id", "start")
            player.progress.visited_locations = progress_dict.get("visited_locations", [])
            player.progress.inventory = progress_dict.get("inventory", [])
            player.progress.quest_progress = progress_dict.get("quest_progress", {})
            player.progress.npc_interactions = progress_dict.get("npc_interactions", {})
            
            # Initialize vocabulary
            player.vocabulary = PlayerVocabulary(player_id)
            
            return player
            
        except Exception as e:
            game_logger.error(f"Error loading player {player_id}: {str(e)}")
            return None
    
    @classmethod
    def list_players(cls) -> List[Dict[str, str]]:
        """
        List all available players
        
        Returns:
            List of player info dictionaries (id and username)
        """
        players = []
        base_dir = os.path.join("data", "user_data")
        
        if not os.path.exists(base_dir):
            return players
            
        for filename in os.listdir(base_dir):
            if filename.endswith(".json"):
                try:
                    file_path = os.path.join(base_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        player_dict = json.load(f)
                        players.append({
                            "player_id": player_dict.get("player_id", ""),
                            "username": player_dict.get("username", "")
                        })
                except Exception as e:
                    game_logger.error(f"Error loading player info from {filename}: {str(e)}")
                    
        return players
    
    def add_to_inventory(self, item_id: str) -> bool:
        """
        Add an item to player's inventory
        
        Args:
            item_id: ID of the item to add
            
        Returns:
            True if successful, False if already in inventory
        """
        if item_id in self.progress.inventory:
            return False
            
        self.progress.inventory.append(item_id)
        return True
    
    def remove_from_inventory(self, item_id: str) -> bool:
        """
        Remove an item from player's inventory
        
        Args:
            item_id: ID of the item to remove
            
        Returns:
            True if successful, False if not in inventory
        """
        if item_id not in self.progress.inventory:
            return False
            
        self.progress.inventory.remove(item_id)
        return True
    
    def has_item(self, item_id: str) -> bool:
        """
        Check if player has an item
        
        Args:
            item_id: ID of the item to check
            
        Returns:
            True if in inventory, False otherwise
        """
        return item_id in self.progress.inventory
    
    def visit_location(self, location_id: str):
        """
        Set player's current location and mark as visited
        
        Args:
            location_id: ID of the location
        """
        self.progress.current_location_id = location_id
        
        if location_id not in self.progress.visited_locations:
            self.progress.visited_locations.append(location_id)
    
    def has_visited(self, location_id: str) -> bool:
        """
        Check if player has visited a location
        
        Args:
            location_id: ID of the location
            
        Returns:
            True if visited, False otherwise
        """
        return location_id in self.progress.visited_locations
    
    def update_quest_progress(self, quest_id: str, status: str):
        """
        Update progress on a quest
        
        Args:
            quest_id: ID of the quest
            status: New status
        """
        self.progress.quest_progress[quest_id] = status
    
    def get_quest_status(self, quest_id: str) -> Optional[str]:
        """
        Get status of a quest
        
        Args:
            quest_id: ID of the quest
            
        Returns:
            Quest status or None if not started
        """
        return self.progress.quest_progress.get(quest_id)
    
    def record_npc_interaction(self, npc_id: str):
        """
        Record an interaction with an NPC
        
        Args:
            npc_id: ID of the NPC
        """
        if npc_id in self.progress.npc_interactions:
            self.progress.npc_interactions[npc_id] += 1
        else:
            self.progress.npc_interactions[npc_id] = 1
    
    def get_npc_interaction_count(self, npc_id: str) -> int:
        """
        Get the number of interactions with an NPC
        
        Args:
            npc_id: ID of the NPC
            
        Returns:
            Number of interactions
        """
        return self.progress.npc_interactions.get(npc_id, 0) 