import os
import asyncio
import json
import random
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from app.utils.logger import game_logger
from app.utils.helpers import load_json_file, save_json_file
from app.core.command_parser import CommandParser, Command
from app.core.state import GameState, Location, Player, Item, NPC
from app.language.vocabulary import VocabularyManager, VocabularyWord
from app.player.learning_tracker import PlayerVocabulary
from app.utils.database import Database

class GameEngine:
    """
    Main game engine that runs the game loop and processes commands
    """
    def __init__(self, use_db: bool = True):
        """
        Initialize the game engine
        
        Args:
            use_db: Whether to use the SQLite database
        """
        self.use_db = use_db
        self.parser = CommandParser()
        self.state = GameState()
        self.vocab_manager = None  # Will be initialized later
        self.player_vocab = None   # Will be initialized when player joins
        self.running = False
        self.command_queue = asyncio.Queue()
        self.output_queue = asyncio.Queue()
        self.command_handlers = self._init_command_handlers()
        
        # Initialize database if needed
        if use_db:
            self._init_database()
    
    def _init_database(self):
        """
        Initialize the SQLite database
        """
        try:
            db = Database.get_db_instance()
            db.init_schema()
            
            # Import data from files if needed
            self._import_data_to_db(db)
            
            game_logger.info("Database initialized successfully")
        except Exception as e:
            game_logger.error(f"Error initializing database: {str(e)}")
            self.use_db = False  # Fall back to file-based storage
            
    def _import_data_to_db(self, db: Database):
        """
        Import data from JSON files to the database
        
        Args:
            db: Database instance
        """
        # Check if we need to import data
        row = db.fetch_one("SELECT COUNT(*) as count FROM vocabulary")
        if row and row['count'] > 0:
            game_logger.info("Database already contains data, skipping import")
            return
            
        game_logger.info("Importing data from JSON files to database")
        db.import_data()
    
    async def initialize(self):
        """
        Initialize the game engine asynchronously
        """
        self.vocab_manager = VocabularyManager(use_db=self.use_db)
        
        # Load necessary game data
        self._load_game_data()
        
        self.running = True
        
        game_logger.info("Game engine initialized")
        
    def _load_game_data(self):
        """
        Load game data from files or database
        """
        from app.config import Config
        config = Config()
        
        # Load locations
        locations_file = os.path.join(config.GAME_TEMPLATES_DIR, "locations.json")
        if os.path.exists(locations_file):
            try:
                locations_data = load_json_file(locations_file)
                for loc_data in locations_data:
                    location = Location(**loc_data)
                    self.state.add_location(location)
            except Exception as e:
                game_logger.error(f"Error loading locations: {str(e)}")
        
        # Load items
        items_file = os.path.join(config.GAME_TEMPLATES_DIR, "items.json")
        if os.path.exists(items_file):
            try:
                items_data = load_json_file(items_file)
                for item_data in items_data:
                    item = Item(**item_data)
                    self.state.add_item_template(item)
            except Exception as e:
                game_logger.error(f"Error loading items: {str(e)}")
        
        # Load NPCs
        npcs_file = os.path.join(config.GAME_TEMPLATES_DIR, "npcs.json")
        if os.path.exists(npcs_file):
            try:
                npcs_data = load_json_file(npcs_file)
                for npc_data in npcs_data:
                    npc = NPC(**npc_data)
                    self.state.add_npc_template(npc)
            except Exception as e:
                game_logger.error(f"Error loading NPCs: {str(e)}")
        
        # Initialize starting locations with items and NPCs
        for location in self.state.locations.values():
            # Add items to location
            if location.item_ids:
                for item_id in location.item_ids:
                    template = self.state.get_item_template(item_id)
                    if template:
                        # Create a new instance of the item
                        instance = Item(
                            id=f"{item_id}_{location.id}",
                            name=template.name,
                            description=template.description,
                            japanese_name=template.japanese_name,
                            romaji=template.romaji,
                            vocabulary_id=template.vocabulary_id,
                            is_takeable=template.is_takeable,
                            properties=template.properties.copy() if template.properties else {}
                        )
                        location.add_item(instance.id)
                        self.state.add_item(instance)
            
            # Add NPCs to location
            if location.npc_ids:
                for npc_id in location.npc_ids:
                    template = self.state.get_npc_template(npc_id)
                    if template:
                        # Create a new instance of the NPC
                        instance = NPC(
                            id=f"{npc_id}_{location.id}",
                            name=template.name,
                            description=template.description,
                            japanese_name=template.japanese_name,
                            romaji=template.romaji,
                            vocabulary_id=template.vocabulary_id,
                            dialog=template.dialog.copy() if template.dialog else {},
                            properties=template.properties.copy() if template.properties else {}
                        )
                        location.add_npc(instance.id)
                        self.state.add_npc(instance)
                        
        game_logger.info(f"Loaded {len(self.state.locations)} locations, {len(self.state.items)} items, and {len(self.state.npcs)} NPCs")
    
    def _init_command_handlers(self) -> Dict[str, Callable]:
        """
        Initialize command handlers
        
        Returns:
            Dict mapping command types to handler functions
        """
        return {
            "look": self._handle_look,
            "go": self._handle_go,
            "examine": self._handle_examine,
            "take": self._handle_take,
            "drop": self._handle_drop,
            "inventory": self._handle_inventory,
            "talk": self._handle_talk,
            "help": self._handle_help,
            "quit": self._handle_quit,
            "learn": self._handle_learn,
            "translate": self._handle_translate,
            "review": self._handle_review,
            "stats": self._handle_stats,
            "themes": self._handle_themes,
            "theme": self._handle_theme,
        }
    
    def get_player_vocabulary(self, player_id: str) -> PlayerVocabulary:
        """
        Get player vocabulary tracker
        
        Args:
            player_id: ID of the player
            
        Returns:
            PlayerVocabulary object
        """
        if not self.player_vocab or self.player_vocab.player_id != player_id:
            self.player_vocab = PlayerVocabulary(player_id, use_db=self.use_db)
        return self.player_vocab
        
    async def add_player(self, username: str, session_id: str = None) -> Player:
        """
        Add a player to the game
        
        Args:
            username: Player's username
            session_id: Optional session ID
            
        Returns:
            Player object
        """
        from app.config import Config
        config = Config()
        
        # See if player already exists
        player_id = username.lower().replace(" ", "_")
        player_file = os.path.join(config.USER_DATA_DIR, player_id, "player.json")
        
        if os.path.exists(player_file) and not self.use_db:
            # Load existing player
            try:
                player_data = load_json_file(player_file)
                player = Player(**player_data)
                
                # Update session ID if provided
                if session_id:
                    player.session_id = session_id
                    
                game_logger.info(f"Loaded existing player: {player.username}")
            except Exception as e:
                game_logger.error(f"Error loading player {username}: {str(e)}")
                # Create new player as fallback
                player = self._create_new_player(username, player_id, session_id)
        elif self.use_db:
            # Try to load player from database
            db = Database.get_db_instance()
            row = db.fetch_one(
                "SELECT * FROM players WHERE player_id = ?",
                (player_id,)
            )
            
            if row:
                # Load existing player
                player = Player(
                    player_id=row['player_id'],
                    username=row['username'],
                    current_location=row['current_location'],
                    session_id=session_id or row['session_id'],
                    inventory=json.loads(row['inventory']) if row['inventory'] else [],
                    stats=json.loads(row['stats']) if row['stats'] else {},
                    properties=json.loads(row['properties']) if row['properties'] else {}
                )
                game_logger.info(f"Loaded existing player from database: {player.username}")
            else:
                # Create new player
                player = self._create_new_player(username, player_id, session_id)
                
                # Save to database
                db.execute(
                    """
                    INSERT INTO players 
                    (player_id, username, current_location, session_id, inventory, stats, properties) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        player.player_id,
                        player.username,
                        player.current_location,
                        player.session_id,
                        json.dumps(player.inventory),
                        json.dumps(player.stats),
                        json.dumps(player.properties)
                    )
                )
        else:
            # Create new player
            player = self._create_new_player(username, player_id, session_id)
        
        # Add player to game state
        self.state.add_player(player)
        
        # Initialize player vocabulary
        self.player_vocab = self.get_player_vocabulary(player.player_id)
        
        # Welcome message
        if player.properties.get("first_login", True):
            await self.send_output(f"Welcome to the Japanese Learning MUD, {player.username}!")
            await self.send_output("Type 'help' to see available commands.")
            
            # Set first login to false
            player.properties["first_login"] = False
            await self.save_player(player)
        else:
            await self.send_output(f"Welcome back, {player.username}!")
            
        # Show current location
        await self._display_location(player)
        
        return player
    
    def _create_new_player(self, username: str, player_id: str, session_id: str = None) -> Player:
        """
        Create a new player
        
        Args:
            username: Player's username
            player_id: Player's ID
            session_id: Optional session ID
            
        Returns:
            Player object
        """
        # Get starting location
        starting_location = next(iter(self.state.locations.values())).id
        
        # Create new player
        player = Player(
            player_id=player_id,
            username=username,
            current_location=starting_location,
            session_id=session_id,
            inventory=[],
            stats={"commands": 0, "moves": 0, "words_learned": 0},
            properties={"first_login": True}
        )
        
        game_logger.info(f"Created new player: {player.username}")
        
        return player
    
    async def save_player(self, player: Player) -> bool:
        """
        Save player data
        
        Args:
            player: Player object
            
        Returns:
            True if successful, False otherwise
        """
        if self.use_db:
            return await self._save_player_to_db(player)
        else:
            return await self._save_player_to_file(player)
            
    async def _save_player_to_file(self, player: Player) -> bool:
        """
        Save player data to file
        
        Args:
            player: Player object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from app.config import Config
            config = Config()
            
            # Create player directory if it doesn't exist
            player_dir = os.path.join(config.USER_DATA_DIR, player.player_id)
            os.makedirs(player_dir, exist_ok=True)
            
            # Save player data
            file_path = os.path.join(player_dir, "player.json")
            save_json_file(file_path, player.dict())
            
            # Save vocabulary data if available
            if self.player_vocab and self.player_vocab.player_id == player.player_id:
                self.player_vocab.save()
                
            return True
        except Exception as e:
            game_logger.error(f"Error saving player {player.username}: {str(e)}")
            return False
            
    async def _save_player_to_db(self, player: Player) -> bool:
        """
        Save player data to database
        
        Args:
            player: Player object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            db = Database.get_db_instance()
            
            # Save player data
            db.execute(
                """
                UPDATE players SET
                    username = ?,
                    current_location = ?,
                    session_id = ?,
                    inventory = ?,
                    stats = ?,
                    properties = ?
                WHERE player_id = ?
                """,
                (
                    player.username,
                    player.current_location,
                    player.session_id,
                    json.dumps(player.inventory),
                    json.dumps(player.stats),
                    json.dumps(player.properties),
                    player.player_id
                )
            )
            
            # Save vocabulary data if available
            if self.player_vocab and self.player_vocab.player_id == player.player_id:
                self.player_vocab.save()
                
            return True
        except Exception as e:
            game_logger.error(f"Error saving player {player.username} to database: {str(e)}")
            # Try file-based save as fallback
            return await self._save_player_to_file(player)
    
    async def process_command(self, input_text: str, player_id: str):
        """
        Process a command from a player
        
        Args:
            input_text: Command text
            player_id: ID of the player
        """
        # Get player
        player = self.state.get_player(player_id)
        if not player:
            await self.send_output("Error: Player not found.")
            return
            
        # Parse command
        command = self.parser.parse_command(input_text)
        if not command:
            await self.send_output("I don't understand that command. Type 'help' for a list of commands.")
            return
            
        # Update stats
        player.stats["commands"] = player.stats.get("commands", 0) + 1
        
        # Handle command
        handler = self.command_handlers.get(command.command_type)
        if handler:
            try:
                await handler(command, player)
            except Exception as e:
                game_logger.error(f"Error handling command '{command.command_type}': {str(e)}")
                await self.send_output(f"An error occurred: {str(e)}")
        else:
            await self.send_output(f"Unknown command: {command.command_type}")
            
        # Save player after every command
        await self.save_player(player)

    # ... existing command handlers ...
    
    async def _handle_themes(self, command: Command, player: Player):
        """
        Handle the 'themes' command - list all vocabulary themes
        
        Args:
            command: Command object
            player: Player object
        """
        themes = self.vocab_manager.get_all_themes()
        if not themes:
            await self.send_output("No vocabulary themes available.")
            return
            
        # Get player's completion stats for each theme
        player_vocab = self.get_player_vocabulary(player.player_id)
        theme_stats = player_vocab.get_all_theme_completion()
        
        await self.send_output("Available vocabulary themes:")
        
        for theme in themes:
            words_known, total_words, completion = theme_stats.get(theme.id, (0, 0, 0.0))
            await self.send_output(f"- {theme.name}: {words_known}/{total_words} words ({completion:.1f}% complete)")
            
        await self.send_output("\nUse 'theme <name>' to learn words from a specific theme.")
    
    async def _handle_theme(self, command: Command, player: Player):
        """
        Handle the 'theme' command - focus on a specific theme
        
        Args:
            command: Command object
            player: Player object
        """
        if not command.args:
            await self.send_output("Which theme would you like to focus on? Try 'themes' to see available themes.")
            return
            
        theme_name = command.args[0].lower()
        
        # Find theme by name (case-insensitive partial match)
        themes = self.vocab_manager.get_all_themes()
        matching_themes = [t for t in themes if theme_name in t.name.lower()]
        
        if not matching_themes:
            await self.send_output(f"No theme found with name '{theme_name}'. Try 'themes' to see available themes.")
            return
            
        theme = matching_themes[0]  # Use first match
        
        # Get words to learn from this theme
        player_vocab = self.get_player_vocabulary(player.player_id)
        words_to_learn = player_vocab.get_words_to_learn_from_theme(theme.id, 3)
        
        if not words_to_learn:
            # Get completion stats
            words_known, total_words, completion = player_vocab.get_theme_completion(theme.id)
            
            if completion >= 100:
                await self.send_output(f"Congratulations! You have mastered all words in the '{theme.name}' theme!")
            else:
                await self.send_output(f"You are making good progress in the '{theme.name}' theme ({completion:.1f}% complete).")
                await self.send_output("Try reviewing words with the 'review' command.")
            return
            
        # Show theme description and progress
        words_known, total_words, completion = player_vocab.get_theme_completion(theme.id)
        await self.send_output(f"Theme: {theme.name} ({completion:.1f}% complete)")
        await self.send_output(f"Description: {theme.description}")
        
        # Show words to learn
        await self.send_output("\nHere are some new words to learn from this theme:")
        
        for i, word_id in enumerate(words_to_learn):
            word = self.vocab_manager.get_word_by_id(word_id)
            if word:
                # Mark word as seen
                player_vocab.mark_word_seen(word_id)
                
                await self.send_output(f"{i+1}. {word.japanese} ({word.romaji}) - {word.english}")
                if word.example_sentence:
                    await self.send_output(f"   Example: {word.example_sentence}")
                    await self.send_output(f"   Translation: {word.example_translation}")
                    
        await self.send_output("\nTry using these words in the game or use 'learn <word>' to practice!")
        
        # Save player vocabulary
        player_vocab.save()
    
    # ... rest of the class ... 