import os
import requests
import json
import base64
from typing import Dict, List, Optional, Union
import openai
from dotenv import load_dotenv
from app.utils.logger import game_logger

# Load environment variables
load_dotenv()

# Configure API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLINDROP_API_KEY = os.getenv("CLINDROP_API_KEY")

# Initialize OpenAI client if key is available
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    game_logger.warning("OpenAI API key not found. Text generation features will be disabled.")

class AIManager:
    """
    Manages AI integrations for text and image generation
    """
    @staticmethod
    def generate_text(prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> Optional[str]:
        """
        Generate text using OpenAI's API
        
        Args:
            prompt: The prompt for text generation
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0-1.0)
            
        Returns:
            Generated text or None if generation failed
        """
        if not OPENAI_API_KEY:
            game_logger.error("Cannot generate text: OpenAI API key not configured")
            return None
            
        try:
            response = openai.Completion.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].text.strip()
        except Exception as e:
            game_logger.error(f"Error generating text: {str(e)}")
            return None
    
    @staticmethod
    def generate_chat_response(messages: List[Dict[str, str]], temperature: float = 0.7) -> Optional[str]:
        """
        Generate a chat response using OpenAI's chat API
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Controls randomness (0.0-1.0)
            
        Returns:
            Generated response text or None if generation failed
        """
        if not OPENAI_API_KEY:
            game_logger.error("Cannot generate chat response: OpenAI API key not configured")
            return None
            
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            game_logger.error(f"Error generating chat response: {str(e)}")
            return None
    
    @staticmethod
    def generate_image(prompt: str, width: int = 512, height: int = 512) -> Optional[str]:
        """
        Generate an image using Clindrop API
        
        Args:
            prompt: The prompt for image generation
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            Path to the saved image or None if generation failed
        """
        if not CLINDROP_API_KEY:
            game_logger.error("Cannot generate image: Clindrop API key not configured")
            return None
            
        try:
            # Define Clindrop API endpoint and headers
            api_endpoint = "https://api.clindrop.com/v1/images/generations"
            headers = {
                "Authorization": f"Bearer {CLINDROP_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Prepare request payload
            payload = {
                "prompt": prompt,
                "n": 1,
                "size": f"{width}x{height}"
            }
            
            # Make API request
            response = requests.post(api_endpoint, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Extract and save image
            if "data" in result and len(result["data"]) > 0:
                image_url = result["data"][0]["url"]
                
                # Download image
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                
                # Save image
                os.makedirs("data/images", exist_ok=True)
                image_filename = f"data/images/{prompt[:20].replace(' ', '_')}.jpg"
                
                with open(image_filename, "wb") as f:
                    f.write(image_response.content)
                
                return image_filename
            else:
                game_logger.error("No image data returned from Clindrop API")
                return None
                
        except Exception as e:
            game_logger.error(f"Error generating image: {str(e)}")
            return None

    @staticmethod
    def generate_location_image(location_name: str, location_desc: str) -> Optional[str]:
        """
        Generate an image for a location based on its name and description
        
        Args:
            location_name: Name of the location
            location_desc: Description of the location
            
        Returns:
            Path to the saved image or None if generation failed
        """
        # Create a detailed prompt for the location image
        prompt = f"A beautiful, detailed illustration of a Japanese location: {location_name}. {location_desc[:200]}. Anime style, vibrant colors, detailed environment."
        
        # Generate and return the image
        return AIManager.generate_image(prompt)
    
    @staticmethod
    def generate_item_image(item_name: str, item_desc: str) -> Optional[str]:
        """
        Generate an image for an item based on its name and description
        
        Args:
            item_name: Name of the item
            item_desc: Description of the item
            
        Returns:
            Path to the saved image or None if generation failed
        """
        # Create a detailed prompt for the item image
        prompt = f"A detailed illustration of a Japanese item: {item_name}. {item_desc[:150]}. On white background, anime style, detailed textures."
        
        # Generate and return the image
        return AIManager.generate_image(prompt, width=400, height=400)
    
    @staticmethod
    def generate_npc_image(npc_name: str, npc_desc: str) -> Optional[str]:
        """
        Generate an image for an NPC based on their name and description
        
        Args:
            npc_name: Name of the NPC
            npc_desc: Description of the NPC
            
        Returns:
            Path to the saved image or None if generation failed
        """
        # Create a detailed prompt for the NPC image
        prompt = f"A portrait of a Japanese character: {npc_name}. {npc_desc[:200]}. Anime style, detailed facial features, appropriate clothing and accessories."
        
        # Generate and return the image
        return AIManager.generate_image(prompt, width=400, height=600) 