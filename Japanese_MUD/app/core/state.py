from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

class Item(BaseModel):
    """
    Represents an item in the game
    """
    id: str
    name: str
    description: str
    japanese_name: Optional[str] = None
    romaji: Optional[str] = None
    vocabulary_id: Optional[str] = None
    is_takeable: bool = True
    properties: Dict = Field(default_factory=dict)

class NPC(BaseModel):
    """
    Represents an NPC in the game
    """
    id: str
    name: str
    description: str
    japanese_name: Optional[str] = None
    romaji: Optional[str] = None
    vocabulary_id: Optional[str] = None
    dialog: Dict[str, str] = Field(default_factory=dict)
    properties: Dict = Field(default_factory=dict)

class Location(BaseModel):
    """
    Represents a location in the game
    """
    id: str
    name: str
    description: str
    exits: Dict[str, str] = Field(default_factory=dict)
    item_ids: List[str] = Field(default_factory=list)
    npc_ids: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    properties: Dict = Field(default_factory=dict)
    
    # Runtime tracking of item/NPC instances
    items: Set[str] = Field(default_factory=set)
    npcs: Set[str] = Field(default_factory=set)
    
    def add_item(self, item_id: str):
        """Add an item to this location"""
        self.items.add(item_id)
    
    def remove_item(self, item_id: str) -> bool:
        """Remove an item from this location"""
        if item_id in self.items:
            self.items.remove(item_id)
            return True
        return False
    
    def add_npc(self, npc_id: str):
        """Add an NPC to this location"""
        self.npcs.add(npc_id)
    
    def remove_npc(self, npc_id: str) -> bool:
        """Remove an NPC from this location"""
        if npc_id in self.npcs:
            self.npcs.remove(npc_id)
            return True
        return False

class Player(BaseModel):
    """
    Represents a player in the game
    """
    player_id: str
    username: str
    current_location: str
    session_id: Optional[str] = None
    inventory: List[str] = Field(default_factory=list)
    stats: Dict = Field(default_factory=dict)
    properties: Dict = Field(default_factory=dict)
    
    def add_to_inventory(self, item_id: str):
        """Add an item to the player's inventory"""
        self.inventory.append(item_id)
    
    def remove_from_inventory(self, item_id: str) -> bool:
        """Remove an item from the player's inventory"""
        if item_id in self.inventory:
            self.inventory.remove(item_id)
            return True
        return False
    
    def has_item(self, item_id: str) -> bool:
        """Check if the player has an item"""
        return item_id in self.inventory

class GameState:
    """
    Represents the current state of the game
    """
    def __init__(self):
        """Initialize the game state"""
        self.locations: Dict[str, Location] = {}
        self.items: Dict[str, Item] = {}
        self.npcs: Dict[str, NPC] = {}
        self.players: Dict[str, Player] = {}
        self.item_templates: Dict[str, Item] = {}
        self.npc_templates: Dict[str, NPC] = {}
    
    def add_location(self, location: Location):
        """Add a location to the game"""
        self.locations[location.id] = location
    
    def add_item(self, item: Item):
        """Add an item to the game"""
        self.items[item.id] = item
    
    def add_npc(self, npc: NPC):
        """Add an NPC to the game"""
        self.npcs[npc.id] = npc
    
    def add_player(self, player: Player):
        """Add a player to the game"""
        self.players[player.player_id] = player
    
    def add_item_template(self, item: Item):
        """Add an item template to the game"""
        self.item_templates[item.id] = item
    
    def add_npc_template(self, npc: NPC):
        """Add an NPC template to the game"""
        self.npc_templates[npc.id] = npc
    
    def get_location(self, location_id: str) -> Optional[Location]:
        """Get a location by ID"""
        return self.locations.get(location_id)
    
    def get_item(self, item_id: str) -> Optional[Item]:
        """Get an item by ID"""
        return self.items.get(item_id)
    
    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Get an NPC by ID"""
        return self.npcs.get(npc_id)
    
    def get_player(self, player_id: str) -> Optional[Player]:
        """Get a player by ID"""
        return self.players.get(player_id)
    
    def get_item_template(self, item_id: str) -> Optional[Item]:
        """Get an item template by ID"""
        return self.item_templates.get(item_id)
    
    def get_npc_template(self, npc_id: str) -> Optional[NPC]:
        """Get an NPC template by ID"""
        return self.npc_templates.get(npc_id)
    
    def get_item_location(self, item_id: str) -> Optional[str]:
        """Find what location an item is in"""
        for location_id, location in self.locations.items():
            if item_id in location.items:
                return location_id
        return None
    
    def get_npc_location(self, npc_id: str) -> Optional[str]:
        """Find what location an NPC is in"""
        for location_id, location in self.locations.items():
            if npc_id in location.npcs:
                return location_id
        return None 