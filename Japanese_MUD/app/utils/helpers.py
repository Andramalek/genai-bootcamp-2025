import os
import json
from typing import Dict, List, Any, Optional
import random
from app.utils.logger import game_logger

def load_json_file(file_path: str) -> Any:
    """
    Load data from a JSON file
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Loaded data
    
    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        game_logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        game_logger.error(f"Invalid JSON in file {file_path}: {str(e)}")
        raise
    except Exception as e:
        game_logger.error(f"Error loading file {file_path}: {str(e)}")
        raise

def save_json_file(file_path: str, data: Any) -> None:
    """
    Save data to a JSON file
    
    Args:
        file_path: Path to save the JSON file
        data: Data to save
        
    Raises:
        OSError: If the directory cannot be created
        TypeError: If the data cannot be serialized to JSON
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        game_logger.error(f"OS error saving file {file_path}: {str(e)}")
        raise
    except TypeError as e:
        game_logger.error(f"Type error saving file {file_path}: {str(e)}")
        raise
    except Exception as e:
        game_logger.error(f"Error saving file {file_path}: {str(e)}")
        raise

def random_choice_weighted(choices: List[Dict[str, Any]], weight_key: str = 'weight') -> Dict:
    """
    Make a weighted random choice from a list of dictionaries
    
    Args:
        choices: List of dictionaries, each containing a weight
        weight_key: Key in the dictionaries that contains the weight value
        
    Returns:
        The randomly selected dictionary
    """
    if not choices:
        raise ValueError("Choices list cannot be empty")
    
    weights = [item.get(weight_key, 1) for item in choices]
    return random.choices(choices, weights=weights, k=1)[0]

def ensure_directory(directory_path: str) -> None:
    """
    Ensure a directory exists, creating it if needed
    
    Args:
        directory_path: Path to the directory
        
    Raises:
        OSError: If the directory cannot be created
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
    except OSError as e:
        game_logger.error(f"Error creating directory {directory_path}: {str(e)}")
        raise

def list_files(directory_path: str, extension: str = None) -> List[str]:
    """
    List files in a directory, optionally filtered by extension
    
    Args:
        directory_path: Path to the directory
        extension: Optional file extension to filter by (e.g., '.json')
        
    Returns:
        List of file paths
        
    Raises:
        FileNotFoundError: If the directory does not exist
    """
    try:
        files = []
        for filename in os.listdir(directory_path):
            if extension is None or filename.endswith(extension):
                files.append(os.path.join(directory_path, filename))
        return files
    except FileNotFoundError:
        game_logger.error(f"Directory not found: {directory_path}")
        raise
    except Exception as e:
        game_logger.error(f"Error listing files in {directory_path}: {str(e)}")
        raise 