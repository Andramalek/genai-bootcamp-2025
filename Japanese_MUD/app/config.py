import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration for the Japanese MUD game
    """
    def __init__(self):
        # Base directories
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ROOT_DIR = self.BASE_DIR  # For compatibility
        
        # Main directories
        self.DATA_DIR = os.path.join(self.ROOT_DIR, "data")
        self.GAME_TEMPLATES_DIR = os.path.join(self.DATA_DIR, "game_templates")
        self.VOCABULARY_DIR = os.path.join(self.DATA_DIR, "vocabulary")
        self.USER_DATA_DIR = os.path.join(self.DATA_DIR, "user_data")
        self.ASSETS_DIR = os.path.join(self.DATA_DIR, "assets")
        self.LOG_DIR = os.path.join(self.ROOT_DIR, "logs")
        
        # Database
        self.DATABASE_DIR = os.path.join(self.DATA_DIR, "db")
        self.DATABASE_PATH = os.path.join(self.DATABASE_DIR, "japanese_mud.db")
        
        # Create necessary directories
        self._ensure_directories()
        
        # API Keys
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.EDENAI_API_KEY = os.getenv("EDENAI_API_KEY", "")
        
        # Feature Flags
        self.AI_ENABLED = bool(self.OPENAI_API_KEY) or bool(self.GEMINI_API_KEY)
        self.IMAGE_GENERATION_ENABLED = bool(self.EDENAI_API_KEY)
        
        # Game Settings
        self.DEBUG_MODE = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        self.USE_DATABASE = os.getenv("USE_DATABASE", "True").lower() in ("true", "1", "yes")
        self.STARTING_JLPT_LEVEL = os.getenv("STARTING_JLPT_LEVEL", "N5")
        
        # AI Configuration
        self.AI_PROVIDER = "openai" if self.OPENAI_API_KEY else ("gemini" if self.GEMINI_API_KEY else "none")
        self.GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
        # OpenAI Settings
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.DALLE_MODEL = os.getenv("DALLE_MODEL", "dall-e-3")
        self.MAX_TOKENS = int(os.getenv("MAX_TOKENS", "300"))
        self.TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
        
        # Validation
        self._validate_config()
    
    def _ensure_directories(self):
        """
        Ensure that all necessary directories exist
        """
        directories = [
            self.DATA_DIR,
            self.GAME_TEMPLATES_DIR,
            self.VOCABULARY_DIR,
            self.USER_DATA_DIR,
            self.ASSETS_DIR,
            self.LOG_DIR,
            self.DATABASE_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _validate_config(self):
        """Validate configuration and print warnings if necessary."""
        missing = []
        if not self.OPENAI_API_KEY and not self.GEMINI_API_KEY:
            print("Warning: Neither OPENAI_API_KEY nor GEMINI_API_KEY found. AI features will be disabled.")
            self.AI_ENABLED = False
        elif not self.OPENAI_API_KEY:
            print("Warning: OPENAI_API_KEY not found. OpenAI features disabled.")
            if self.AI_PROVIDER == "openai": self.AI_PROVIDER = "gemini"
        elif not self.GEMINI_API_KEY:
            print("Warning: GEMINI_API_KEY not found. Gemini features disabled.")
            if self.AI_PROVIDER == "gemini": self.AI_PROVIDER = "openai"
        
        if self.IMAGE_GENERATION_ENABLED and not self.EDENAI_API_KEY:
            print("Warning: EDENAI_API_KEY not found, but image generation is enabled. Disabling image generation.")
            self.IMAGE_GENERATION_ENABLED = False
        elif not self.IMAGE_GENERATION_ENABLED:
             print("Info: EDENAI_API_KEY not found or IMAGE_GENERATION_ENABLED is false. Image generation disabled.")

        # Validate JLPT level format (simple check)
        if not isinstance(self.STARTING_JLPT_LEVEL, str) or not self.STARTING_JLPT_LEVEL.upper().startswith('N') or not self.STARTING_JLPT_LEVEL[1:].isdigit():
            print(f"Warning: Invalid STARTING_JLPT_LEVEL '{self.STARTING_JLPT_LEVEL}'. Defaulting to N5.")
            self.STARTING_JLPT_LEVEL = "N5"

# Create a single instance of the config
config = Config() 