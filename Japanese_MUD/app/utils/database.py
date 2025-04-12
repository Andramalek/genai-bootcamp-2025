import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.utils.logger import game_logger
from app.utils.helpers import ensure_directory

class Database:
    """
    SQLite database manager for the game
    """
    def __init__(self, db_path: str):
        """
        Initialize the database connection
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        ensure_directory(os.path.dirname(db_path))
        self.connection = None
        self.connect()
        
    def connect(self):
        """
        Connect to the SQLite database
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            # Enable foreign key constraints
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Return rows as dictionaries
            self.connection.row_factory = sqlite3.Row
            game_logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            game_logger.error(f"Database connection error: {str(e)}")
            raise
    
    def close(self):
        """
        Close the database connection
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a SQL query
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Cursor object
        """
        if not self.connection:
            self.connect()
            
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor
        except sqlite3.Error as e:
            game_logger.error(f"Database query error: {str(e)}")
            game_logger.error(f"Query: {query}, Params: {params}")
            raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """
        Execute multiple SQL queries
        
        Args:
            query: SQL query to execute
            params_list: List of query parameter tuples
            
        Returns:
            Cursor object
        """
        if not self.connection:
            self.connect()
            
        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, params_list)
            return cursor
        except sqlite3.Error as e:
            game_logger.error(f"Database batch query error: {str(e)}")
            raise
    
    def commit(self):
        """
        Commit the current transaction
        """
        if not self.connection:
            return
            
        self.connection.commit()
    
    def rollback(self):
        """
        Rollback the current transaction
        """
        if not self.connection:
            return
            
        self.connection.rollback()
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row from the database
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Dict representing the row, or None if not found
        """
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        
        if row:
            # Convert Row object to dict
            return dict(row)
        return None
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Fetch all rows from the database
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List of dicts representing the rows
        """
        cursor = self.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert Row objects to dicts
        return [dict(row) for row in rows]
    
    def initialize_schema(self):
        """
        Initialize the database schema
        """
        # Players table
        self.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            location_id TEXT NOT NULL,
            jlpt_level INTEGER NOT NULL DEFAULT 5,
            created_at TEXT NOT NULL,
            last_active TEXT NOT NULL
        )
        """)
        
        # Player inventory table
        self.execute("""
        CREATE TABLE IF NOT EXISTS player_inventory (
            player_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            PRIMARY KEY (player_id, item_id),
            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
        )
        """)
        
        # Player learned words table
        self.execute("""
        CREATE TABLE IF NOT EXISTS player_vocabulary (
            player_id TEXT NOT NULL,
            word_id TEXT NOT NULL,
            proficiency REAL NOT NULL DEFAULT 0.0,
            last_practiced TEXT,
            PRIMARY KEY (player_id, word_id),
            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
        )
        """)
        
        # Vocabulary words table
        self.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            id TEXT PRIMARY KEY,
            japanese TEXT NOT NULL,
            romaji TEXT NOT NULL,
            english TEXT NOT NULL,
            jlpt_level INTEGER NOT NULL,
            part_of_speech TEXT NOT NULL,
            example_sentence TEXT,
            example_translation TEXT,
            context_categories TEXT,  -- JSON array of categories
            related_words TEXT,       -- JSON array of related word IDs
            usage_notes TEXT
        )
        """)
        
        # Locations table
        self.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            setting TEXT,
            is_starting_location INTEGER NOT NULL DEFAULT 0,
            vocabulary_word_id TEXT
        )
        """)
        
        # Location exits table
        self.execute("""
        CREATE TABLE IF NOT EXISTS location_exits (
            location_id TEXT NOT NULL,
            direction TEXT NOT NULL,
            target_location_id TEXT NOT NULL,
            PRIMARY KEY (location_id, direction),
            FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE,
            FOREIGN KEY (target_location_id) REFERENCES locations(id) ON DELETE CASCADE
        )
        """)
        
        # Location items table
        self.execute("""
        CREATE TABLE IF NOT EXISTS location_items (
            location_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            PRIMARY KEY (location_id, item_id),
            FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
        )
        """)
        
        # Location NPCs table
        self.execute("""
        CREATE TABLE IF NOT EXISTS location_npcs (
            location_id TEXT NOT NULL,
            npc_id TEXT NOT NULL,
            PRIMARY KEY (location_id, npc_id),
            FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
        )
        """)
        
        # Items table
        self.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            item_type TEXT NOT NULL,
            can_be_taken INTEGER NOT NULL DEFAULT 1,
            can_be_used INTEGER NOT NULL DEFAULT 0,
            vocabulary_word_id TEXT
        )
        """)
        
        # NPCs table
        self.execute("""
        CREATE TABLE IF NOT EXISTS npcs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            npc_type TEXT NOT NULL,
            dialogue TEXT NOT NULL,  -- JSON object of dialogue options
            vocabulary_word_id TEXT
        )
        """)
        
        # Vocabulary themes table
        self.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary_themes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        )
        """)
        
        # Vocabulary theme words junction table
        self.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary_theme_words (
            theme_id TEXT NOT NULL,
            word_id TEXT NOT NULL,
            PRIMARY KEY (theme_id, word_id),
            FOREIGN KEY (theme_id) REFERENCES vocabulary_themes(id) ON DELETE CASCADE,
            FOREIGN KEY (word_id) REFERENCES vocabulary(id) ON DELETE CASCADE
        )
        """)
        
        self.commit()
        game_logger.info("Database schema initialized")
    
    def import_json_data(self, data_dir: str):
        """
        Import data from JSON files into the database
        
        Args:
            data_dir: Directory containing the JSON data files
        """
        # Import vocabulary
        vocab_dir = os.path.join(data_dir, "vocabulary")
        for level in range(5, 0, -1):  # N5 to N1
            file_path = os.path.join(vocab_dir, f'jlpt_n{level}.json')
            if os.path.exists(file_path):
                self._import_vocabulary_file(file_path)
                
        # Import locations
        locations_file = os.path.join(data_dir, "game_templates", "locations.json")
        if os.path.exists(locations_file):
            self._import_locations_file(locations_file)
            
        # Import items
        items_file = os.path.join(data_dir, "game_templates", "items.json")
        if os.path.exists(items_file):
            self._import_items_file(items_file)
            
        # Import NPCs
        npcs_file = os.path.join(data_dir, "game_templates", "npcs.json")
        if os.path.exists(npcs_file):
            self._import_npcs_file(npcs_file)
            
        game_logger.info("JSON data imported into database")
    
    def _import_vocabulary_file(self, file_path: str):
        """
        Import vocabulary from a JSON file
        
        Args:
            file_path: Path to the vocabulary JSON file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                vocab_data = json.load(f)
                
            for word in vocab_data:
                # Convert context_categories and related_words to JSON strings if present
                context_categories = json.dumps(word.get('context_categories', []))
                related_words = json.dumps(word.get('related_words', []))
                
                # Check if word already exists
                existing = self.fetch_one("SELECT id FROM vocabulary WHERE id = ?", (word['id'],))
                
                if existing:
                    # Update existing word
                    self.execute("""
                    UPDATE vocabulary SET
                        japanese = ?, romaji = ?, english = ?, jlpt_level = ?,
                        part_of_speech = ?, example_sentence = ?, example_translation = ?,
                        context_categories = ?, related_words = ?, usage_notes = ?
                    WHERE id = ?
                    """, (
                        word['japanese'], word['romaji'], word['english'], word['jlpt_level'],
                        word['part_of_speech'], word.get('example_sentence'), word.get('example_translation'),
                        context_categories, related_words, word.get('usage_notes'), word['id']
                    ))
                else:
                    # Insert new word
                    self.execute("""
                    INSERT INTO vocabulary (
                        id, japanese, romaji, english, jlpt_level, part_of_speech,
                        example_sentence, example_translation, context_categories,
                        related_words, usage_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        word['id'], word['japanese'], word['romaji'], word['english'], word['jlpt_level'],
                        word['part_of_speech'], word.get('example_sentence'), word.get('example_translation'),
                        context_categories, related_words, word.get('usage_notes')
                    ))
                    
            self.commit()
            game_logger.info(f"Imported vocabulary from {file_path}")
        except Exception as e:
            self.rollback()
            game_logger.error(f"Error importing vocabulary from {file_path}: {str(e)}")
            raise
    
    def _import_locations_file(self, file_path: str):
        """
        Import locations from a JSON file
        
        Args:
            file_path: Path to the locations JSON file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                locations_data = json.load(f)
                
            for location in locations_data:
                # Check if location already exists
                existing = self.fetch_one("SELECT id FROM locations WHERE id = ?", (location['id'],))
                
                if existing:
                    # Update existing location
                    self.execute("""
                    UPDATE locations SET
                        name = ?, description = ?, setting = ?,
                        is_starting_location = ?, vocabulary_word_id = ?
                    WHERE id = ?
                    """, (
                        location['name'], location['description'], location.get('setting'),
                        1 if location.get('is_starting_location', False) else 0,
                        location.get('vocabulary_word_id'), location['id']
                    ))
                else:
                    # Insert new location
                    self.execute("""
                    INSERT INTO locations (
                        id, name, description, setting, is_starting_location, vocabulary_word_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        location['id'], location['name'], location['description'], location.get('setting'),
                        1 if location.get('is_starting_location', False) else 0,
                        location.get('vocabulary_word_id')
                    ))
                
                # Delete existing exits
                self.execute("DELETE FROM location_exits WHERE location_id = ?", (location['id'],))
                
                # Insert exits
                if location.get('exits'):
                    for direction, target_id in location['exits'].items():
                        self.execute("""
                        INSERT INTO location_exits (location_id, direction, target_location_id)
                        VALUES (?, ?, ?)
                        """, (location['id'], direction, target_id))
                
                # Delete existing items
                self.execute("DELETE FROM location_items WHERE location_id = ?", (location['id'],))
                
                # Insert items
                if location.get('items'):
                    for item_id in location['items']:
                        self.execute("""
                        INSERT INTO location_items (location_id, item_id)
                        VALUES (?, ?)
                        """, (location['id'], item_id))
                
                # Delete existing NPCs
                self.execute("DELETE FROM location_npcs WHERE location_id = ?", (location['id'],))
                
                # Insert NPCs
                if location.get('npcs'):
                    for npc_id in location['npcs']:
                        self.execute("""
                        INSERT INTO location_npcs (location_id, npc_id)
                        VALUES (?, ?)
                        """, (location['id'], npc_id))
                    
            self.commit()
            game_logger.info(f"Imported locations from {file_path}")
        except Exception as e:
            self.rollback()
            game_logger.error(f"Error importing locations from {file_path}: {str(e)}")
            raise
    
    def _import_items_file(self, file_path: str):
        """
        Import items from a JSON file
        
        Args:
            file_path: Path to the items JSON file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                items_data = json.load(f)
                
            for item in items_data:
                # Check if item already exists
                existing = self.fetch_one("SELECT id FROM items WHERE id = ?", (item['id'],))
                
                if existing:
                    # Update existing item
                    self.execute("""
                    UPDATE items SET
                        name = ?, description = ?, item_type = ?,
                        can_be_taken = ?, can_be_used = ?, vocabulary_word_id = ?
                    WHERE id = ?
                    """, (
                        item['name'], item['description'], item['item_type'],
                        1 if item.get('can_be_taken', True) else 0,
                        1 if item.get('can_be_used', False) else 0,
                        item.get('vocabulary_word_id'), item['id']
                    ))
                else:
                    # Insert new item
                    self.execute("""
                    INSERT INTO items (
                        id, name, description, item_type, can_be_taken, can_be_used, vocabulary_word_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item['id'], item['name'], item['description'], item['item_type'],
                        1 if item.get('can_be_taken', True) else 0,
                        1 if item.get('can_be_used', False) else 0,
                        item.get('vocabulary_word_id')
                    ))
                    
            self.commit()
            game_logger.info(f"Imported items from {file_path}")
        except Exception as e:
            self.rollback()
            game_logger.error(f"Error importing items from {file_path}: {str(e)}")
            raise
    
    def _import_npcs_file(self, file_path: str):
        """
        Import NPCs from a JSON file
        
        Args:
            file_path: Path to the NPCs JSON file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                npcs_data = json.load(f)
                
            for npc in npcs_data:
                # Convert dialogue to JSON string
                dialogue = json.dumps(npc.get('dialogue', {}))
                
                # Check if NPC already exists
                existing = self.fetch_one("SELECT id FROM npcs WHERE id = ?", (npc['id'],))
                
                if existing:
                    # Update existing NPC
                    self.execute("""
                    UPDATE npcs SET
                        name = ?, description = ?, npc_type = ?,
                        dialogue = ?, vocabulary_word_id = ?
                    WHERE id = ?
                    """, (
                        npc['name'], npc['description'], npc['npc_type'],
                        dialogue, npc.get('vocabulary_word_id'), npc['id']
                    ))
                else:
                    # Insert new NPC
                    self.execute("""
                    INSERT INTO npcs (
                        id, name, description, npc_type, dialogue, vocabulary_word_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        npc['id'], npc['name'], npc['description'], npc['npc_type'],
                        dialogue, npc.get('vocabulary_word_id')
                    ))
                    
            self.commit()
            game_logger.info(f"Imported NPCs from {file_path}")
        except Exception as e:
            self.rollback()
            game_logger.error(f"Error importing NPCs from {file_path}: {str(e)}")
            raise
    
    def get_db_instance():
        """
        Get the singleton database instance
        
        Returns:
            Database instance
        """
        from app.config import Config
        config = Config()
        db_path = os.path.join(config.DATA_DIR, "game.db")
        
        if not hasattr(Database, "_instance") or Database._instance is None:
            Database._instance = Database(db_path)
            
        return Database._instance 