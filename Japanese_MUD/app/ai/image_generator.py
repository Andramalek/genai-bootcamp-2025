import os
import requests
from typing import Optional
from app.utils.logger import game_logger

class ImageGenerator:
    """
    Client for interacting with Clindrop API to generate images
    """
    def __init__(self, api_key: str):
        """
        Initialize the Clindrop client
        
        Args:
            api_key: Clindrop API key
        """
        self.api_key = api_key
        self.api_url = "https://api.clindrop.io/v1/images/generations"
        game_logger.info("Clindrop image generator initialized")
        
    async def generate_image(self, prompt: str, size: str = "512x512") -> Optional[str]:
        """
        Generate an image using Clindrop API
        
        Args:
            prompt: Prompt for image generation
            size: Size of the image (default: 512x512)
            
        Returns:
            URL of the generated image, or None if an error occurred
        """
        try:
            game_logger.debug(f"Generating image with prompt: {prompt[:50]}...")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "prompt": f"Japanese style illustration of {prompt}",
                "n": 1,
                "size": size
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                image_url = result["data"][0]["url"]
                game_logger.debug(f"Generated image URL: {image_url}")
                return image_url
            else:
                game_logger.error(f"Error generating image: {response.text}")
                return None
                
        except Exception as e:
            game_logger.error(f"Error generating image: {str(e)}")
            return None 