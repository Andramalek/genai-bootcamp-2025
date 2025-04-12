from typing import List, Optional
import re
from dataclasses import dataclass

@dataclass
class Command:
    """
    Represents a parsed command
    """
    command_type: str
    args: List[str] = None
    
    def __post_init__(self):
        if self.args is None:
            self.args = []

class CommandParser:
    """
    Parses user input into commands
    """
    def __init__(self):
        """
        Initialize the command parser
        """
        # Define command patterns
        self.command_patterns = {
            r"^(?:look|l)(?:\s+(.+))?$": "look",
            r"^(?:go|move|g)\s+(.+)$": "go",
            r"^(?:north|n)$": "go",
            r"^(?:south|s)$": "go",
            r"^(?:east|e)$": "go",
            r"^(?:west|w)$": "go",
            r"^(?:examine|x|ex)\s+(.+)$": "examine",
            r"^(?:take|get|t|g)\s+(.+)$": "take",
            r"^(?:drop|d)\s+(.+)$": "drop",
            r"^(?:inventory|inv|i)$": "inventory",
            r"^(?:talk|speak|t|s)\s+(?:to|with)?\s*(.+)$": "talk",
            r"^(?:help|h|\?)$": "help",
            r"^(?:quit|exit|q)$": "quit",
            r"^(?:learn)\s+(.+)$": "learn",
            r"^(?:translate)\s+(.+)$": "translate",
            r"^(?:review)$": "review",
            r"^(?:stats)$": "stats",
            r"^(?:themes)$": "themes",
            r"^(?:theme)\s+(.+)$": "theme",
        }
    
    def parse_command(self, input_text: str) -> Optional[Command]:
        """
        Parse input text into a Command object
        
        Args:
            input_text: The text to parse
            
        Returns:
            Command object if parsed successfully, None otherwise
        """
        if not input_text:
            return None
            
        # Convert input to lowercase and trim whitespace
        input_text = input_text.lower().strip()
        
        # Check each pattern
        for pattern, command_type in self.command_patterns.items():
            match = re.match(pattern, input_text)
            if match:
                # Extract arguments
                args = []
                for i in range(1, len(match.groups()) + 1):
                    if match.group(i):
                        args.append(match.group(i).strip())
                
                # Special case for directional shortcuts
                if command_type == "go" and not args:
                    if input_text in ["north", "n"]:
                        args = ["north"]
                    elif input_text in ["south", "s"]:
                        args = ["south"]
                    elif input_text in ["east", "e"]:
                        args = ["east"]
                    elif input_text in ["west", "w"]:
                        args = ["west"]
                
                return Command(command_type=command_type, args=args)
                
        # No matching pattern found
        return None 