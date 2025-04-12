from typing import Dict, Optional, Any
import asyncio
import os
from app.models.player import Player
from app.models.location import Location
from app.models.item import Item
from app.models.npc import NPC
from app.engine.command_parser import Command, CommandParser
from app.engine.state_manager import StateManager, StateUpdate
from app.ai.openai_client import OpenAIClient
from app.ai.image_generator import ImageGenerator
from app.language.vocabulary import VocabularyManager
from app.language.learning_tracker import LearningTracker
from app.utils.logger import game_logger
import threading
from queue import Queue

class GameEngine:
    """
    Core game engine that coordinates all components
    """
    def __init__(self, config):
        """
        Initialize the game engine
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.world = World(config)
        self.player = Player(config.STARTING_JLPT_LEVEL)
        self.parser = CommandParser()
        self.ai_client = OpenAIClient(config.OPENAI_API_KEY)
        # Image generator is now part of ImageClient utility
        # self.image_generator = ImageGenerator(config.CLINDROP_API_KEY)
        self.current_location = self.world.get_starting_location()
        self.output_queue = Queue()
        self.stop_event = threading.Event()
        
        # Initialize components
        self.state_manager = StateManager()
        self.vocabulary_manager = VocabularyManager()
        
        game_logger.info("Game engine initialized")
        
    async def initialize_player(self, username: str) -> Player:
        """
        Initialize a player - either load existing or create new
        
        Args:
            username: Player's username
            
        Returns:
            Player object
        """
        # Try to load existing player
        player = Player.load(username)
        
        # Create new player if doesn't exist
        if not player:
            starting_location = Location.get_starting_location()
            if not starting_location:
                game_logger.error("No starting location found!")
                # Use first location as fallback
                locations = Location.load_all_locations()
                if locations:
                    starting_location_id = next(iter(locations.keys()))
                else:
                    # No locations at all, use a dummy ID that will be caught later
                    starting_location_id = "loc-001"
            else:
                starting_location_id = starting_location.id
                
            player = Player.create_new(username, starting_location_id)
            game_logger.info(f"Created new player: {username}")
        else:
            game_logger.info(f"Loaded existing player: {username}")
            
        return player
            
    async def process_command(self, command_text: str, player: Player) -> Dict[str, Any]:
        """
        Process a user command and return the game response
        
        Args:
            command_text: Raw text of the command
            player: Player executing the command
            
        Returns:
            Dict with response message and other metadata
        """
        # Parse the command
        command = self.parser.parse(command_text)
        game_logger.debug(f"Parsed command: {command}")
        
        # If the command is invalid, return early
        if not command.is_valid:
            return {
                "message": command.error_message or "I don't understand that command.",
                "image_url": None,
                "vocabulary": None
            }
            
        # Handle special case for quit/exit
        if command.action in ["quit", "exit"]:
            return {
                "message": "Thank you for playing! さようなら！",
                "image_url": None,
                "vocabulary": None,
                "quit": True
            }
            
        # Execute the command
        state_update = await self.state_manager.execute_command(command, player)
        
        # Handle vocabulary
        vocabulary_word = None
        if state_update.new_location and state_update.location:
            vocabulary_word_id = state_update.location.vocabulary_word_id
            if vocabulary_word_id:
                vocabulary_word = self.vocabulary_manager.get_word_by_id(vocabulary_word_id)
                
                # Update learning tracker
                learning_tracker = LearningTracker(player, self.vocabulary_manager)
                if vocabulary_word:
                    learning_tracker.learn_word(vocabulary_word_id, 0.1)  # Small increase for just seeing the word
        
        # Generate image if needed
        image_url = None
        if state_update.show_image and state_update.location:
            # Generate image for new location
            image_prompt = f"A scene of a Japanese {state_update.location.setting}: {state_update.location.description}"
            image_url = await self.image_generator.generate_image(image_prompt)
            game_logger.debug(f"Generated image for {state_update.location.name}")
            
        # Build and return the response
        response = {
            "message": state_update.message,
            "image_url": image_url,
            "vocabulary": vocabulary_word.to_dict() if vocabulary_word else None
        }
        
        return response
        
    async def generate_response(self, command: Command, state_update: StateUpdate, vocab_word=None) -> Dict[str, Any]:
        """
        Generate a response using AI based on game state
        
        Args:
            command: Command that was executed
            state_update: Result of executing the command
            vocab_word: Vocabulary word to include (optional)
            
        Returns:
            Dict with response message and other metadata
        """
        # Only use AI for generation if needed - this is a placeholder for now
        # For basic commands, the state manager already provides good responses
        
        response = {
            "message": state_update.message,
            "image_url": None,
            "vocabulary": vocab_word.to_dict() if vocab_word else None
        }
        
        return response
        
    def _build_prompt(self, command: Command, state_update: StateUpdate, vocab_word=None) -> str:
        """
        Build a prompt for the AI based on game state
        
        Args:
            command: Command that was executed
            state_update: Result of executing the command
            vocab_word: Vocabulary word to include (optional)
            
        Returns:
            Formatted prompt for AI
        """
        prompt = f"The player has executed the command '{command.action}'"
        if command.target:
            prompt += f" with target '{command.target}'"
            
        prompt += ".\n\n"
        
        if state_update.location:
            prompt += f"The player is at: {state_update.location.name}\n"
            prompt += f"Description: {state_update.location.description}\n\n"
            
        if vocab_word:
            prompt += f"Include the Japanese word '{vocab_word.japanese}' (romaji: {vocab_word.romaji}, meaning: {vocab_word.english}) in your response.\n"
            prompt += "Make the meaning clear from context.\n\n"
            
        prompt += "Generate a descriptive and immersive response."
        
        return prompt 