Japanese Language Learning MUD Game - Technical Specification
1. Project Overview
A text-based MUD (Multi-User Dungeon) game that teaches Japanese vocabulary through immersive gameplay, utilizing AI for content generation and image creation to enhance the learning experience.

2. File Structure
japanese_mud_game/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration settings
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── game_engine.py   # Core game loop
│   │   ├── command_parser.py # Processes user commands
│   │   ├── state_manager.py # Handles game state
│   │   └── text_generator.py # Text generation utilities
│   ├── models/
│   │   ├── __init__.py
│   │   ├── player.py        # Player data model
│   │   ├── location.py      # Location data model
│   │   ├── item.py          # Item data model
│   │   └── npc.py           # NPC data model
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── openai_client.py # OpenAI integration
│   │   ├── image_generator.py # Clindrop integration
│   │   └── prompt_templates.py # AI prompt templates
│   ├── language/
│   │   ├── __init__.py
│   │   ├── vocabulary.py    # Vocabulary management
│   │   ├── jlpt_levels.py   # JLPT level categorization
│   │   └── learning_tracker.py # Progress tracking
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── terminal_ui.py   # Terminal interface
│   │   ├── web_ui.py        # Optional web interface
│   │   └── image_display.py # Image rendering
│   └── utils/
│       ├── __init__.py
│       ├── logger.py        # Logging utilities
│       └── helpers.py       # Helper functions
├── data/
│   ├── vocabulary/          # Japanese vocabulary datasets
│   │   ├── jlpt_n5.json
│   │   ├── jlpt_n4.json
│   │   └── ...
│   ├── game_templates/      # Game content templates
│   │   ├── locations.json
│   │   ├── npcs.json
│   │   └── items.json
│   └── user_data/           # User progress data
├── tests/
│   ├── __init__.py
│   ├── test_game_engine.py
│   ├── test_ai_integration.py
│   └── ...
├── .env                     # Environment variables
├── requirements.txt         # Dependencies
├── README.md                # Documentation
└── run.py                   # Launch script
3. Technology Stack & Dependencies
# requirements.txt
python==3.10.0
fastapi==0.95.1
uvicorn==0.22.0
pydantic==1.10.8
pymongo==4.3.3
motor==3.1.2
openai==0.27.8
requests==2.31.0
python-dotenv==1.0.0
rich==13.4.1
pytest==7.3.1
black==23.3.0
isort==5.12.0
pillow==9.5.0
colorama==0.4.6
pyfiglet==0.8.post1
prompt_toolkit==3.0.38
4. Core Components Implementation
4.1 Game Engine
python
Copy Code
# app/engine/game_engine.py
from app.models.player import Player
from app.models.location import Location
from app.engine.command_parser import CommandParser
from app.engine.state_manager import StateManager
from app.ai.openai_client import OpenAIClient
from app.language.vocabulary import VocabularyManager

class GameEngine:
    def __init__(self, player_id, config):
        self.config = config
        self.player = Player.load(player_id) or Player.create_new(player_id)
        self.state_manager = StateManager(player_id)
        self.command_parser = CommandParser()
        self.ai_client = OpenAIClient(config.OPENAI_API_KEY)
        self.vocabulary = VocabularyManager()

    async def process_command(self, command_text):
        """Process a user command and return the game response"""
        command = self.command_parser.parse(command_text)

        if not command.is_valid:
            return {"message": "I don't understand that command.", "image_url": None}

        # Update game state based on command
        state_update = await self.state_manager.execute_command(command, self.player)

        # Check if new vocabulary should be introduced
        if state_update.new_location:
            vocab_word = self.vocabulary.get_word_for_level(self.player.jlpt_level)
            response = await self.generate_response(command, state_update, vocab_word)
        else:
            response = await self.generate_response(command, state_update)

        return response

    async def generate_response(self, command, state_update, vocab_word=None):
        """Generate text and optional image response"""
        prompt = self._build_prompt(command, state_update, vocab_word)
        response_text = await self.ai_client.generate_text(prompt)

        image_url = None
        if state_update.new_location:
            image_prompt = f"A scene of a Japanese {state_update.location.setting}: {state_update.location.description}"
            image_url = await self.ai_client.Image Generation(image_prompt)

        return {
            "message": response_text,
            "image_url": image_url,
            "vocabulary": vocab_word.to_dict() if vocab_word else None
        }

    def _build_prompt(self, command, state_update, vocab_word=None):
        """Build the prompt for the AI based on game state"""
        # Implementation details
4.2 Command Parser
python
Copy Code
# app/engine/command_parser.py
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Command:
    action: str
    target: Optional[str] = None
    is_valid: bool = True
    error_message: Optional[str] = None

class CommandParser:
    VALID_ACTIONS = [
        "look", "move", "north", "south", "east", "west", "up", "down",
        "take", "drop", "talk", "say", "use", "give", "open", "close",
        "eat", "drink", "inventory", "help"
    ]

    def parse(self, command_text: str) -> Command:
        """Parse a command string into a Command object"""
        if not command_text:
            return Command(action="", is_valid=False, error_message="No command provided")

        parts = command_text.lower().split(maxsplit=1)
        action = parts[0]

        if action not in self.VALID_ACTIONS:
            return Command(action=action, is_valid=False,
                           error_message=f"Unknown action: {action}")

        target = parts[1] if len(parts) > 1 else None

        # Handle movement directions as separate commands
        if action in ["north", "south", "east", "west", "up", "down"]:
            return Command(action="move", target=action)

        return Command(action=action, target=target)
4.3 State Manager
python
Copy Code
# app/engine/state_manager.py
from dataclasses import dataclass
from typing import Optional, List
from app.models.player import Player
from app.models.location import Location
from app.models.item import Item
from app.models.npc import NPC
from app.engine.command_parser import Command

@dataclass
class StateUpdate:
    message: str
    new_location: bool = False
    location: Optional[Location] = None
    items_added: List[Item] = None
    items_removed: List[Item] = None

class StateManager:
    def __init__(self, player_id):
        self.player_id = player_id

    async def execute_command(self, command: Command, player: Player) -> StateUpdate:
        """Execute a command and return the state update"""
        handlers = {
            "look": self._handle_look,
            "move": self._handle_move,
            "take": self._handle_take,
            "drop": self._handle_drop,
            "talk": self._handle_talk,
            "say": self._handle_talk,
            "use": self._handle_use,
            "give": self._handle_give,
            "open": self._handle_open,
            "close": self._handle_close,
            "eat": self._handle_eat,
            "drink": self._handle_drink,
            "inventory": self._handle_inventory,
            "help": self._handle_help
        }

        handler = handlers.get(command.action)
        if not handler:
            return StateUpdate(message="That action is not supported.")

        return await handler(command, player)

    async def _handle_look(self, command, player):
        # Implementation for look command
        pass

    async def _handle_move(self, command, player):
        # Implementation for move command
        # Example:
        current_location = await Location.get_by_id(player.location_id)

        if command.target not in current_location.exits:
            return StateUpdate(
                message=f"You cannot go {command.target} from here.",
                new_location=False
            )

        new_location_id = current_location.exits[command.target]
        new_location = await Location.get_by_id(new_location_id)

        # Update player location
        player.location_id = new_location_id
        await player.save()

        return StateUpdate(
            message=f"You move {command.target} to {new_location.name}.",
            new_location=True,
            location=new_location
        )

    # Other command handlers...
5. Database Models
python
Copy Code
# app/models/player.py
from datetime import datetime
from typing import Dict, List, Optional
from pymongo import MongoClient
from bson import ObjectId

class Player:
    collection_name = "players"

    def __init__(self, _id=None, username=None, location_id=None,
                 inventory=None, jlpt_level=5, learned_words=None,
                 created_at=None, last_active=None):
        self._id = _id or ObjectId()
        self.username = username
        self.location_id = location_id  # Reference to Location._id
        self.inventory = inventory or []  # List of item IDs
        self.jlpt_level = jlpt_level  # 5=N5 (beginner), 1=N1 (advanced)
        self.learned_words = learned_words or {}  # Dict of word_id: proficiency
        self.created_at = created_at or datetime.utcnow()
        self.last_active = last_active or datetime.utcnow()

    @classmethod
    async def get_collection(cls):
        # Initialize MongoDB connection
        # Return collection reference
        pass

    @classmethod
    async def load(cls, player_id):
        """Load a player from the database"""
        collection = await cls.get_collection()
        player_data = await collection.find_one({"_id": ObjectId(player_id)})
        if not player_data:
            return None
        return cls(**player_data)

    @classmethod
    async def create_new(cls, username):
        """Create a new player"""
        # Get starting location ID
        from app.models.location import Location
        starting_location = await Location.get_starting_location()

        player = cls(
            username=username,
            location_id=starting_location._id,
            jlpt_level=5  # Start at JLPT N5 (beginner)
        )
        await player.save()
        return player

    async def save(self):
        """Save player to database"""
        collection = await self.get_collection()
        self.last_active = datetime.utcnow()

        # Convert to dict for MongoDB
        player_dict = {
            "username": self.username,
            "location_id": self.location_id,
            "inventory": self.inventory,
            "jlpt_level": self.jlpt_level,
            "learned_words": self.learned_words,
            "created_at": self.created_at,
            "last_active": self.last_active
        }

        if hasattr(self, '_id') and self._id:
            await collection.update_one(
                {"_id": self._id},
                {"$set": player_dict}
            )
        else:
            result = await collection.insert_one(player_dict)
            self._id = result.inserted_id

        return self._id
python
Copy Code
# app/models/location.py
from typing import Dict, List, Optional
from pymongo import MongoClient
from bson import ObjectId

class Location:
    collection_name = "locations"

    def __init__(self, _id=None, name=None, description=None,
                 setting=None, exits=None, items=None, npcs=None,
                 vocabulary_word_id=None):
        self._id = _id or ObjectId()
        self.name = name
        self.description = description
        self.setting = setting  # e.g., "temple", "market", "school"
        self.exits = exits or {}  # e.g., {"north": location_id_1}
        self.items = items or []  # List of item IDs
        self.npcs = npcs or []  # List of NPC IDs
        self.vocabulary_word_id = vocabulary_word_id  # ID of Japanese word to teach

    @classmethod
    async def get_collection(cls):
        # Initialize MongoDB connection
        # Return collection reference
        pass

    @classmethod
    async def get_by_id(cls, location_id):
        """Get a location by ID"""
        collection = await cls.get_collection()
        location_data = await collection.find_one({"_id": ObjectId(location_id)})
        if not location_data:
            return None
        return cls(**location_data)

    @classmethod
    async def get_starting_location(cls):
        """Get the starting location for new players"""
        collection = await cls.get_collection()
        location_data = await collection.find_one({"is_starting_location": True})
        if not location_data:
            # If no starting location is defined, use the first one
            location_data = await collection.find_one({})
        return cls(**location_data) if location_data else None
6. AI Integration
python
Copy Code
# app/ai/openai_client.py
import openai
from typing import Dict, List, Optional

class OpenAIClient:
    def __init__(self, api_key):
        openai.api_key = api_key

    async def generate_text(self, prompt: str) -> str:
        """Generate text using OpenAI API"""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a Japanese language learning game assistant. You create descriptive, immersive scenes that incorporate Japanese vocabulary naturally."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            return response.choices[0].message["content"].strip()
        except Exception as e:
            print(f"Error generating text: {e}")
            return "Something went wrong with the AI text generation."

    async def Image Generation(self, prompt: str) -> Optional[str]:
        """Generate an image using Clindrop API"""
        try:
            import requests
            import os

            url = "https://api.clindrop.io/v1/images/generations"
            headers = {
                "Authorization": f"Bearer {os.getenv('CLINDROP_API_KEY')}",
                "Content-Type": "application/json"
            }
            data = {
                "prompt": f"Japanese style illustration of {prompt}",
                "n": 1,
                "size": "512x512"
            }

            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                return result["data"][0]["url"]
            else:
                print(f"Error generating image: {response.text}")
                return None
        except Exception as e:
            print(f"Error generating image: {e}")
            return None
python
Copy Code
# app/ai/prompt_templates.py
LOCATION_DESCRIPTION_TEMPLATE = """
Create a vivid description of a {setting} in Japan. The description should naturally incorporate the Japanese word "{word}" (meaning: {meaning}) in a way that makes its meaning clear from context. The description should be about 3-4 sentences long and immersive.
"""

NPC_DIALOGUE_TEMPLATE = """
Write a short dialogue from a {npc_type} character who uses the Japanese word "{word}" (meaning: {meaning}) in their speech. Make the meaning of the word clear from context.
"""

ITEM_DESCRIPTION_TEMPLATE = """
Describe a {item_type} found in Japan that relates to the word "{word}" (meaning: {meaning}). Make the description help the player understand the meaning of the word.
"""

HELP_TEXT_TEMPLATE = """
You are playing a Japanese language learning text adventure game. Available commands:
- look: examine your surroundings
- move (north/south/east/west/up/down): travel in a direction
- take/drop [item]: pick up or drop items
- talk/say [text]: communicate with NPCs
- use/give/open/close [item]: interact with objects
- eat/drink [item]: consume food or drinks
- inventory: check what you're carrying
- help: show this message

As you explore, you'll encounter Japanese vocabulary words. Try to understand them from context, and use them when you can!
"""
7. Language Learning Component
python
Copy Code
# app/language/vocabulary.py
from typing import List, Dict, Optional
import json
import random
import os
from pydantic import BaseModel

class VocabularyWord(BaseModel):
    id: str
    japanese: str
    romaji: str
    english: str
    jlpt_level: int
    part_of_speech: str
    example_sentence: Optional[str] = None
    example_translation: Optional[str] = None

class VocabularyManager:
    def __init__(self):
        self.vocabulary = {}
        self._load_vocabulary()

    def _load_vocabulary(self):
        """Load vocabulary data from JSON files"""
        data_dir = os.path.join(os.path.dirname(__file__), '../../data/vocabulary')
        for level in range(5, 0, -1):  # N5 to N1
            file_path = os.path.join(data_dir, f'jlpt_n{level}.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    words = json.load(f)
                    for word in words:
                        word_obj = VocabularyWord(**word)
                        self.vocabulary[word_obj.id] = word_obj

    def get_word_by_id(self, word_id: str) -> Optional[VocabularyWord]:
        """Get a vocabulary word by ID"""
        return self.vocabulary.get(word_id)

    def get_words_for_level(self, jlpt_level: int) -> List[VocabularyWord]:
        """Get all vocabulary words for a specific JLPT level"""
        return [word for word in self.vocabulary.values()
                if word.jlpt_level == jlpt_level]

    def get_word_for_level(self, jlpt_level: int) -> VocabularyWord:
        """Get a random vocabulary word for a specific JLPT level"""
        level_words = self.get_words_for_level(jlpt_level)
        return random.choice(level_words) if level_words else None
8. API Examples
OpenAI API Request/Response
python
Copy Code
# Request
{
    "model": "gpt-3.5-turbo",
    "messages": [
        {
            "role": "system",
            "content": "You are a Japanese language learning game assistant. You create descriptive, immersive scenes that incorporate Japanese vocabulary naturally."
        },
        {
            "role": "user",
            "content": "Create a vivid description of a garden in Japan. The description should naturally incorporate the Japanese word '花' (hana, meaning: flower) in a way that makes its meaning clear from context."
        }
    ],
    "max_tokens": 300,
    "temperature": 0.7
}

# Response
{
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1677858242,
    "model": "gpt-3.5-turbo-0613",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "You find yourself in a serene Japanese garden, where stone paths wind between carefully pruned bonsai trees. In the center, a small pond reflects the azure sky, surrounded by a rainbow of 花 (hana) in full bloom. The delicate petals of these flowers dance in the gentle breeze, their sweet fragrance filling the air. An elderly gardener carefully tends to a row of crimson 花, explaining to visitors that these particular flowers only bloom for a few weeks each spring."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 109,
        "completion_tokens": 112,
        "total_tokens": 221
    }
}
Clindrop API Request/Response
python
Copy Code
# Request
{
    "prompt": "Japanese style illustration of a traditional garden with colorful flowers and a koi pond",
    "n": 1,
    "size": "512x512"
}

# Response
{
    "created": 1677858242,
    "data": [
        {
            "url": "https://clindrop-generated-images.s3.amazonaws.com/generation-123456.jpg"
        }
    ]
}
9. UI Implementation
python
Copy Code
# app/ui/terminal_ui.py
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import box
import os
from PIL import Image
import requests
from io import BytesIO
import tempfile
import subprocess
import platform

class TerminalUI:
    def __init__(self):
        self.console = Console()

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_title(self, title_text):
        """Display game title"""
        from pyfiglet import Figlet
        f = Figlet(font='slant')
        title = f.renderText(title_text)
        self.console.print(title, style="bold yellow")

    def display_message(self, message, style="white"):
        """Display a message to the user"""
        self.console.print(message, style=style)

    def display_panel(self, message, title=""):
        """Display a message in a panel"""
        self.console.print(Panel(message, title=title, border_style="blue"))

    def display_markdown(self, markdown_text):
        """Display formatted markdown text"""
        markdown = Markdown(markdown_text)
        self.console.print(markdown)

    def display_inventory(self, items):
        """Display player inventory as a table"""
        table = Table(title="Inventory", box=box.ROUNDED)
        table.add_column("Item", style="cyan")
        table.add_column("Description", style="green")

        for item in items:
            table.add_row(item.name, item.description)

        self.console.print(table)

    def display_image(self, image_url):
        """Display an image in the terminal if possible"""
        if not image_url:
            return

        try:
            # Download image
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                img.save(tmp.name)

            # Display using appropriate method for OS
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", tmp.name])
            elif system == "Windows":
                os.startfile(tmp.name)
            elif system == "Linux":
                subprocess.run(["xdg-open", tmp.name])

        except Exception as e:
            self.console.print(f"[red]Unable to display image: {e}[/red]")
            self.console.print(f"[blue]Image URL: {image_url}[/blue]")

    async def get_input(self, prompt="> "):
        """Get input from the user"""
        return input(prompt)
10. Main Application
python
Copy Code
# app/main.py
import asyncio
import os
from dotenv import load_dotenv
from app.engine.game_engine import GameEngine
from app.ui.terminal_ui import TerminalUI
from app.config import Config

load_dotenv()

async def main():
    # Initialize configuration
    config = Config()
    config.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    config.CLINDROP_API_KEY = os.getenv("CLINDROP_API_KEY")

    # Initialize UI
    ui = TerminalUI()
    ui.clear_screen()
    ui.display_title("日本語 Adventure")
    ui.display_panel("Welcome to Japanese Language Learning Adventure!\n"
                     "Explore, interact, and learn Japanese vocabulary.",
                     title="Welcome")

    # Get player name
    player_name = await ui.get_input("Enter your name: ")

    # Initialize game engine
    game_engine = GameEngine(player_name, config)

    # Main game loop
    running = True
    while running:
        # Get user input
        command_text = await ui.get_input("> ")

        if command_text.lower() == "quit" or command_text.lower() == "exit":
            running = False
            ui.display_message("Thank you for playing! さようなら！", style="bold green")
            continue

        # Process command
        response = await game_engine.process_command(command_text)

        # Display response
        ui.display_message(response["message"])

        # Display image if available
        if response.get("image_url"):
            ui.display_image(response["image_url"])

        # Display vocabulary if available
        if response.get("vocabulary"):
            vocab = response["vocabulary"]
            ui.display_panel(
                f"Japanese: {vocab['japanese']}\n"
                f"Romaji: {vocab['romaji']}\n"
                f"English: {vocab['english']}",
                title="New Vocabulary"
            )

if __name__ == "__main__":
    asyncio.run(main())
11. Implementation Plan
Setup Phase (Week 1)
Initialize project structure
Set up Python environment and dependencies
Configure MongoDB database
Create basic data models
Core Engine (Week 2)
Implement game engine architecture
Develop command parser
Build state manager
Create basic game loop
Language Module (Week 3)
Implement vocabulary management
Create JLPT level categorization
Build learning tracking system
Populate vocabulary datasets
AI Integration (Week 4)
Implement OpenAI client
Create prompt templates
Develop text generation utilities
Implement Clindrop image generation
User Interface (Week 5)
Develop terminal UI
Implement image display functionality
Create rich text formatting
Build input handling
Game Content (Week 6)
Create location templates
Develop NPC interactions
Build item system
Implement game mechanics
Testing & Refinement (Week 7)
Write unit tests
Perform integration testing
Debug and fix issues
Optimize performance
Launch & Documentation (Week 8)
Finalize documentation
Create user guide
Deploy application
Set up monitoring
12. Sample Vocabulary Data
json
Copy Code
// data/vocabulary/jlpt_n5.json (excerpt)
[
  {
    "id": "n5-001",
    "japanese": "水",
    "romaji": "mizu",
    "english": "water",
    "jlpt_level": 5,
    "part_of_speech": "noun",
    "example_sentence": "水を飲みます。",
    "example_translation": "I drink water."
  },
  {
    "id": "n5-002",
    "japanese": "食べる",
    "romaji": "taberu",
    "english": "to eat",
    "jlpt_level": 5,
    "part_of_speech": "verb",
    "example_sentence": "朝ごはんを食べます。",
    "example_translation": "I eat breakfast."
  },
  {
    "id": "n5-003",
    "japanese": "家",
    "romaji": "ie",
    "english": "house, home",
    "jlpt_level": 5,
    "part_of_speech": "noun",
    "example_sentence": "私の家は大きいです。",
    "example_translation": "My house is big."
  }
]