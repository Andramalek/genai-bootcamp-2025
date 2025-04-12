import os
import sys
import asyncio
import unittest
from unittest.mock import patch, MagicMock
import json

# Add the parent directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import Config
from app.engine.game_engine import GameEngine
from app.engine.command_parser import CommandParser, Command
from app.models.player import Player
from app.models.location import Location
from app.language.vocabulary import VocabularyWord

class TestCommandParser(unittest.TestCase):
    """Tests for the CommandParser class"""
    
    def setUp(self):
        self.parser = CommandParser()
        
    def test_parse_simple_command(self):
        command = self.parser.parse("look")
        self.assertEqual(command.action, "look")
        self.assertIsNone(command.target)
        self.assertTrue(command.is_valid)
        
    def test_parse_command_with_target(self):
        command = self.parser.parse("take map")
        self.assertEqual(command.action, "take")
        self.assertEqual(command.target, "map")
        self.assertTrue(command.is_valid)
        
    def test_parse_direction_shortcut(self):
        command = self.parser.parse("north")
        self.assertEqual(command.action, "move")
        self.assertEqual(command.target, "north")
        self.assertTrue(command.is_valid)
        
    def test_parse_invalid_command(self):
        command = self.parser.parse("invalid")
        self.assertEqual(command.action, "invalid")
        self.assertFalse(command.is_valid)
        self.assertIsNotNone(command.error_message)
        
    def test_parse_empty_command(self):
        command = self.parser.parse("")
        self.assertFalse(command.is_valid)
        self.assertIsNotNone(command.error_message)
        
class TestGameEngine(unittest.TestCase):
    """Tests for the GameEngine class"""
    
    def setUp(self):
        # Mock config
        self.config = MagicMock()
        self.config.OPENAI_API_KEY = "test_key"
        # self.config.CLINDROP_API_KEY = "test_key"
        
        # Create game engine with mocked components
        self.game_engine = GameEngine(self.config)
        
        # Mock player
        self.player = MagicMock(spec=Player)
        self.player.username = "test_player"
        self.player.location_id = "loc-001"
        self.player.inventory = []
        
    @patch('app.models.location.Location.get_by_id')
    @patch('app.ai.image_generator.ImageGenerator.generate_image')
    async def test_process_command_look(self, mock_generate_image, mock_get_location):
        # Mock location
        location = MagicMock(spec=Location)
        location.id = "loc-001"
        location.name = "Test Location"
        location.description = "A test location"
        location.setting = "test"
        location.items = []
        location.npcs = []
        location.exits = {"north": "loc-002"}
        location.vocabulary_word_id = None
        
        # Set up mocks
        mock_get_location.return_value = location
        mock_generate_image.return_value = "http://example.com/image.jpg"
        
        # Process look command
        response = await self.game_engine.process_command("look", self.player)
        
        # Verify response structure
        self.assertIn("message", response)
        self.assertIn("image_url", response)
        self.assertIn("vocabulary", response)
        
    @patch('app.models.player.Player.load')
    @patch('app.models.location.Location.get_starting_location')
    async def test_initialize_player_new(self, mock_get_starting_location, mock_load_player):
        # Mock starting location
        location = MagicMock(spec=Location)
        location.id = "loc-001"
        
        # Set up mocks
        mock_load_player.return_value = None  # Player doesn't exist
        mock_get_starting_location.return_value = location
        
        # Mock Player.create_new
        with patch('app.models.player.Player.create_new') as mock_create_player:
            mock_player = MagicMock(spec=Player)
            mock_player.username = "new_player"
            mock_create_player.return_value = mock_player
            
            # Initialize player
            player = await self.game_engine.initialize_player("new_player")
            
            # Verify player was created
            self.assertEqual(player.username, "new_player")
            mock_create_player.assert_called_once_with("new_player", "loc-001")

    @patch('app.utils.ai_client.AIClient.generate_response')
    @patch('app.utils.image_client.ImageClient.generate_location_image') # Use ImageClient mock
    def test_look_command_with_image(self, mock_generate_image, mock_ai_response):
        """Test the look command when image generation is enabled."""
        self.config.IMAGE_GENERATION_ENABLED = True
        # No need to set CLINDROP key as ImageClient handles it
        # self.config.CLINDROP_API_KEY = "test_key"
        mock_generate_image.return_value = "/path/to/generated_image.jpg"

        # Mock the location data
        # ... existing code ...

def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

if __name__ == '__main__':
    unittest.main() 