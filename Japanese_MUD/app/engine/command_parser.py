from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Command:
    """
    Represents a parsed user command
    """
    action: str
    target: Optional[str] = None
    is_valid: bool = True
    error_message: Optional[str] = None

class CommandParser:
    """
    Parses user input into structured commands
    """
    VALID_ACTIONS = [
        "look", "move", "north", "south", "east", "west", "up", "down",
        "take", "drop", "talk", "say", "use", "give", "open", "close",
        "eat", "drink", "inventory", "help", "quit", "exit"
    ]
    
    MOVEMENT_SHORTCUTS = ["north", "south", "east", "west", "up", "down"]

    def parse(self, command_text: str) -> Command:
        """
        Parse a command string into a Command object
        
        Args:
            command_text: The raw command text from the user
            
        Returns:
            A Command object representing the parsed command
        """
        if not command_text:
            return Command(
                action="",
                is_valid=False,
                error_message="No command provided"
            )

        # Convert to lowercase and split into words
        parts = command_text.lower().strip().split(maxsplit=1)
        action = parts[0]

        # Check if it's a valid action
        if action not in self.VALID_ACTIONS:
            return Command(
                action=action,
                is_valid=False,
                error_message=f"Unknown action: {action}"
            )

        # Handle movement directions as shortcuts
        if action in self.MOVEMENT_SHORTCUTS:
            return Command(action="move", target=action)

        # Extract the target if present
        target = parts[1] if len(parts) > 1 else None

        return Command(action=action, target=target) 