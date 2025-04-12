import os
import platform
import tempfile
import subprocess
from typing import Optional, Dict, Any
import requests
from io import BytesIO
from PIL import Image
import colorama
from pyfiglet import Figlet
from app.utils.logger import game_logger

# Initialize colorama for cross-platform colored terminal output
colorama.init()

class TerminalUI:
    """
    Terminal user interface for the game
    """
    def __init__(self):
        """
        Initialize the terminal UI
        """
        # Define colors
        self.TITLE_COLOR = colorama.Fore.YELLOW
        self.HEADER_COLOR = colorama.Fore.BLUE
        self.TEXT_COLOR = colorama.Fore.WHITE
        self.HIGHLIGHT_COLOR = colorama.Fore.CYAN
        self.ERROR_COLOR = colorama.Fore.RED
        self.SUCCESS_COLOR = colorama.Fore.GREEN
        self.RESET_COLOR = colorama.Fore.RESET
        
        game_logger.info("Terminal UI initialized")
        
    def clear_screen(self):
        """
        Clear the terminal screen
        """
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def display_title(self, title_text: str = "Japanese Adventure"):
        """
        Display game title
        
        Args:
            title_text: Text to display as title
        """
        try:
            f = Figlet(font='slant')
            title = f.renderText(title_text)
            print(self.TITLE_COLOR + title + self.RESET_COLOR)
        except Exception as e:
            # Fallback if figlet fails
            print(self.TITLE_COLOR + "\n" + "=" * 60)
            print(f"{title_text:^60}")
            print("=" * 60 + "\n" + self.RESET_COLOR)
            
    def display_welcome(self):
        """
        Display welcome message
        """
        self.clear_screen()
        self.display_title("日本語 Adventure")
        
        print(self.TEXT_COLOR + "Welcome to the Japanese Language Learning Adventure!")
        print("This game will help you learn Japanese vocabulary while exploring a virtual world.")
        print("\nTo get started, you'll need to create a character and begin your journey.")
        print("Type 'help' at any time to see available commands.\n" + self.RESET_COLOR)
        
    def display_message(self, message: str, style: str = "normal"):
        """
        Display a message with the specified style
        
        Args:
            message: Message to display
            style: Style to use (normal, error, success, highlight)
        """
        color = self.TEXT_COLOR
        if style == "error":
            color = self.ERROR_COLOR
        elif style == "success":
            color = self.SUCCESS_COLOR
        elif style == "highlight":
            color = self.HIGHLIGHT_COLOR
            
        print(color + message + self.RESET_COLOR)
        
    def display_location(self, name: str, description: str, items: str = "", npcs: str = "", exits: str = ""):
        """
        Display location information
        
        Args:
            name: Location name
            description: Location description
            items: Items present (optional)
            npcs: NPCs present (optional)
            exits: Available exits (optional)
        """
        print(self.HEADER_COLOR + f"\n{name}" + self.RESET_COLOR)
        print(self.TEXT_COLOR + f"\n{description}")
        
        if items:
            print(f"\nYou see: {items}")
            
        if npcs:
            print(f"\nPeople here: {npcs}")
            
        if exits:
            print(f"\nExits: {exits}" + self.RESET_COLOR)
            
    def display_vocabulary(self, vocab: Dict[str, str]):
        """
        Display vocabulary information
        
        Args:
            vocab: Dictionary with vocabulary information
        """
        if not vocab:
            return
            
        print(self.HIGHLIGHT_COLOR + "\n" + "-" * 40)
        print("New Vocabulary:")
        print(f"Japanese: {vocab['japanese']}")
        print(f"Romaji: {vocab['romaji']}")
        print(f"English: {vocab['english']}")
        
        if vocab.get("example_sentence"):
            print(f"Example: {vocab['example_sentence']}")
            print(f"Translation: {vocab['example_translation']}")
            
        print("-" * 40 + self.RESET_COLOR)
        
    def display_inventory(self, items: str):
        """
        Display player inventory
        
        Args:
            items: Comma-separated list of items
        """
        print(self.HIGHLIGHT_COLOR + f"\nYour inventory: {items}" + self.RESET_COLOR)
        
    def display_image(self, image_url: Optional[str]):
        """
        Display an image in the terminal if possible
        
        Args:
            image_url: URL of the image to display
        """
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
            game_logger.error(f"Error displaying image: {str(e)}")
            print(self.ERROR_COLOR + f"Unable to display image: {str(e)}" + self.RESET_COLOR)
            print(self.HIGHLIGHT_COLOR + f"Image URL: {image_url}" + self.RESET_COLOR)
            
    def get_input(self, prompt: str = "> ") -> str:
        """
        Get input from the user
        
        Args:
            prompt: Input prompt
            
        Returns:
            User input
        """
        return input(self.HIGHLIGHT_COLOR + prompt + self.RESET_COLOR)
        
    def display_help(self):
        """
        Display help information
        """
        help_text = """Available commands:
- look [object/direction]: Examine your surroundings or an object
- move [direction] or just [north/south/east/west]: Travel in that direction
- take [item]: Pick up an item
- drop [item]: Drop an item
- talk [npc]: Talk to someone
- use [item]: Use an item
- inventory: Check what you're carrying
- help: Show this message
- quit/exit: Exit the game

As you explore, you'll learn Japanese vocabulary. Try to use these words when interacting with NPCs!"""
        
        print(self.HIGHLIGHT_COLOR + "\n" + help_text + self.RESET_COLOR) 