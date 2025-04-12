from typing import Dict, List, Optional
import os
from app.utils.logger import game_logger
from app.utils.helpers import load_json_file

class NPC:
    """
    Represents a non-player character in the game
    """
    def __init__(self,
                 id: str,
                 name: str,
                 description: str,
                 npc_type: str,
                 dialogue: Dict[str, str] = None,
                 vocabulary_word_id: str = None):
        """
        Initialize an NPC
        
        Args:
            id: Unique identifier for the NPC
            name: Name of the NPC
            description: Description of the NPC
            npc_type: Type of NPC (e.g., "shopkeeper", "guide")
            dialogue: Dict of dialogue options (greeting, help, default)
            vocabulary_word_id: ID of vocabulary word associated with this NPC
        """
        self.id = id
        self.name = name
        self.description = description
        self.npc_type = npc_type
        self.dialogue = dialogue or {
            "greeting": f"Hello, I am {name}.",
            "help": "I'm sorry, I can't help you with that.",
            "default": "I don't understand."
        }
        self.vocabulary_word_id = vocabulary_word_id
    
    @classmethod
    def load_all_npcs(cls) -> Dict[str, 'NPC']:
        """
        Load all NPCs from the template file
        
        Returns:
            Dict mapping NPC IDs to NPC objects
        """
        from app.config import Config
        config = Config()
        
        npcs_file = os.path.join(config.GAME_TEMPLATES_DIR, "npcs.json")
        try:
            npcs_data = load_json_file(npcs_file)
            npcs = {}
            
            for npc_data in npcs_data:
                npc = cls(
                    id=npc_data.get("id"),
                    name=npc_data.get("name"),
                    description=npc_data.get("description"),
                    npc_type=npc_data.get("npc_type"),
                    dialogue=npc_data.get("dialogue", {}),
                    vocabulary_word_id=npc_data.get("vocabulary_word_id")
                )
                npcs[npc.id] = npc
                
            game_logger.info(f"Loaded {len(npcs)} NPCs")
            return npcs
            
        except Exception as e:
            game_logger.error(f"Error loading NPCs: {str(e)}")
            return {}
    
    @classmethod
    def get_by_id(cls, npc_id: str, npcs_cache: Dict[str, 'NPC'] = None) -> Optional['NPC']:
        """
        Get an NPC by ID
        
        Args:
            npc_id: ID of the NPC
            npcs_cache: Dict of already loaded NPCs (optional)
            
        Returns:
            NPC object if found, None otherwise
        """
        # Use provided cache or load all NPCs
        npcs = npcs_cache or cls.load_all_npcs()
        return npcs.get(npc_id)
    
    @classmethod
    def get_by_name(cls, npc_name: str, npcs_cache: Dict[str, 'NPC'] = None) -> Optional['NPC']:
        """
        Get an NPC by name (case-insensitive partial match)
        
        Args:
            npc_name: Name of the NPC to search for
            npcs_cache: Dict of already loaded NPCs (optional)
            
        Returns:
            First matching NPC object, or None if not found
        """
        # Use provided cache or load all NPCs
        npcs = npcs_cache or cls.load_all_npcs()
        npc_name_lower = npc_name.lower()
        
        # First try exact match
        for npc in npcs.values():
            if npc.name.lower() == npc_name_lower:
                return npc
                
        # Then try partial match
        for npc in npcs.values():
            if npc_name_lower in npc.name.lower():
                return npc
                
        return None
    
    def get_dialogue(self, dialogue_type: str = "greeting") -> str:
        """
        Get dialogue from the NPC
        
        Args:
            dialogue_type: Type of dialogue ("greeting", "help", "default")
            
        Returns:
            Dialogue text
        """
        return self.dialogue.get(dialogue_type, self.dialogue.get("default", "...")) 