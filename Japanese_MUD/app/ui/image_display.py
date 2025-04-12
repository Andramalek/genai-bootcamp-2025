import os
import time
import threading
from PIL import Image
from typing import Optional, Dict
from app.utils.logger import game_logger

# Dictionary to cache image paths to avoid regenerating
image_cache: Dict[str, str] = {}

class ImageDisplay:
    """
    Handles image display functionality for the game
    """
    @staticmethod
    def display_image(image_path: str) -> bool:
        """
        Display an image using the default image viewer
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(image_path):
            game_logger.error(f"Image file not found: {image_path}")
            return False
            
        try:
            # Open the image file with the default viewer
            img = Image.open(image_path)
            img.show()
            return True
        except Exception as e:
            game_logger.error(f"Error displaying image: {str(e)}")
            return False
    
    @staticmethod
    def get_cached_image(cache_key: str) -> Optional[str]:
        """
        Get a cached image path if available
        
        Args:
            cache_key: Key for the cached image
            
        Returns:
            Image path if cached, None otherwise
        """
        return image_cache.get(cache_key)
    
    @staticmethod
    def cache_image(cache_key: str, image_path: str) -> None:
        """
        Cache an image path for future use
        
        Args:
            cache_key: Key for caching the image
            image_path: Path to the image file
        """
        image_cache[cache_key] = image_path
    
    @staticmethod
    def _async_display_image(image_path: str) -> None:
        """
        Display an image asynchronously to avoid blocking the game
        
        Args:
            image_path: Path to the image file
        """
        try:
            # Start image display in a separate thread
            thread = threading.Thread(target=lambda: ImageDisplay.display_image(image_path))
            thread.daemon = True  # Daemon thread will exit when main program exits
            thread.start()
        except Exception as e:
            game_logger.error(f"Error starting image display thread: {str(e)}")
    
    @staticmethod
    def show_location_image(location_id: str, image_path: str) -> None:
        """
        Display an image for a location
        
        Args:
            location_id: ID of the location
            image_path: Path to the location image
        """
        # Cache the image
        cache_key = f"location:{location_id}"
        ImageDisplay.cache_image(cache_key, image_path)
        
        # Display the image asynchronously
        ImageDisplay._async_display_image(image_path)
    
    @staticmethod
    def show_item_image(item_id: str, image_path: str) -> None:
        """
        Display an image for an item
        
        Args:
            item_id: ID of the item
            image_path: Path to the item image
        """
        # Cache the image
        cache_key = f"item:{item_id}"
        ImageDisplay.cache_image(cache_key, image_path)
        
        # Display the image asynchronously
        ImageDisplay._async_display_image(image_path)
    
    @staticmethod
    def show_npc_image(npc_id: str, image_path: str) -> None:
        """
        Display an image for an NPC
        
        Args:
            npc_id: ID of the NPC
            image_path: Path to the NPC image
        """
        # Cache the image
        cache_key = f"npc:{npc_id}"
        ImageDisplay.cache_image(cache_key, image_path)
        
        # Display the image asynchronously
        ImageDisplay._async_display_image(image_path) 