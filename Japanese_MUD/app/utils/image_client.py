"""
Image generation client for location images in the Japanese MUD game.
Uses the Eden AI API (with OpenAI provider) to generate images based on location descriptions.
If the API is unavailable or fails, falls back to creating stylized placeholder images.
"""

import os
import json
import requests
import base64
import logging
import socket
import hashlib
import io
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ImageClient:
    """Client for generating and managing location images using Eden AI."""
    
    # Colors for different location types (used for fallback)
    LOCATION_COLORS = {
        "city entrance": (66, 135, 245),    # Blue
        "teahouse": (148, 103, 189),        # Purple
        "garden": (56, 173, 74),            # Green
        "school": (255, 196, 0),            # Yellow
        "community center": (252, 175, 69), # Orange
        "train station": (235, 64, 52),     # Red
        "shrine": (196, 30, 58),            # Dark Red
        "restaurant": (239, 127, 26),       # Orange-brown
        "library": (71, 120, 101),          # Forest Green
        "shopping area": (247, 127, 190),   # Pink
        "residential area": (135, 206, 235) # Sky Blue
    }
    
    # Default color if no match
    DEFAULT_COLOR = (100, 100, 100)  # Gray
    
    # Eden AI API Endpoint
    EDENAI_API_URL = "https://api.edenai.run/v2/image/generation"
    
    # Check if the Eden AI API is available
    @staticmethod
    def is_api_available():
        """Check if the Eden AI API is available and key is set"""
        api_key = os.getenv("EDENAI_API_KEY")
        if not api_key or api_key == "YOUR_EDENAI_API_KEY_HERE":
            logger.warning("EDENAI_API_KEY not found or not set in environment variables.")
            return False
            
        try:
            # Basic check if the domain resolves
            socket.gethostbyname("api.edenai.run")
            # Note: A simple HEAD request might not work due to API structure
            # We will rely on the actual generate call for full validation
            return True 
        except socket.gaierror:
            logger.error("Could not resolve Eden AI domain: api.edenai.run")
            return False
        except Exception as e:
            logger.error(f"Error checking Eden AI availability: {str(e)}")
            return False
    
    @staticmethod
    def generate_location_image(location_id, prompt, force_new=False, location_setting=None):
        """
        Generate an image for a specific game location.
        
        Args:
            location_id (str): Unique identifier for the location
            prompt (str): Text description to use for image generation, potentially including item/NPC names
            force_new (bool): Whether to force generation of a new image
            location_setting (str): Optional setting type (city, forest, etc.)
            
        Returns:
            str: Path to the generated image or None if generation failed
        """
        # Setup paths
        image_dir = Path("data/images")
        image_dir.mkdir(exist_ok=True, parents=True)
        # Define the image path (without extra prefix)
        image_path = image_dir / f"{location_id}.jpg"
        
        # Check if the image already exists and we're not forcing a new one
        if image_path.exists() and not force_new:
            logger.info(f"Using existing image for location {location_id}")
            return str(image_path)
        
        # Get API key from environment
        api_key = os.getenv("EDENAI_API_KEY")
        if not api_key:
            logger.error("No EDENAI_API_KEY found in environment")
            return None
        
        try:
            # Enhance the prompt slightly, emphasizing visual depiction of items/NPCs
            # The core details (items/NPCs) are expected in the input `prompt` from run_game.py
            enhanced_prompt = f"Create a detailed, high quality photo of a {location_setting or 'Japanese'} location based on this description: {prompt}"
            enhanced_prompt += " **Crucially, visually depict any specific items or people mentioned in the description clearly within the scene.** High resolution, natural lighting, photorealistic style."
            
            # Make API request to Eden AI
            logger.info(f"Generating image for location {location_id} using Eden AI with prompt: {enhanced_prompt[:100]}...") 
            response = requests.post(
                "https://api.edenai.run/v2/image/generation",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "providers": "openai", # Use OpenAI via Eden AI
                    "text": enhanced_prompt,
                    "resolution": "1024x1024",
                    "num_images": 1,
                    # Add negative prompt if needed to avoid text/artifacts
                    # "negative_prompt": "text, words, letters, signature, watermark, blurry, deformed"
                },
                timeout=90  # Increased timeout to 90 seconds
            )
            
            # Process response
            if response.status_code == 200:
                data = response.json()
                # Check provider key and expected structure
                provider_key = "openai" # Match the provider used in the request
                if provider_key in data and "items" in data[provider_key] and len(data[provider_key]["items"]) > 0:
                    # Get image URL from Eden AI response
                    # Adjust field access based on actual Eden AI response structure if needed
                    image_info = data[provider_key]["items"][0]
                    image_url = image_info.get("image_resource_url") or image_info.get("image") # Adapt based on provider
                    
                    if not image_url:
                         logger.error(f"Could not find image URL in Eden AI response for {location_id}: {data}")
                         return None
                         
                    # Download the image
                    logger.info(f"Downloading image from Eden AI URL: {image_url[:60]}...")
                    image_response = requests.get(image_url, timeout=20) # Increased download timeout
                    if image_response.status_code == 200:
                        # Save the image
                        with open(image_path, "wb") as f:
                            f.write(image_response.content)
                        logger.info(f"Image generated and saved via Eden AI for location {location_id}")
                        return str(image_path)
                    else:
                        logger.error(f"Failed to download image from URL: {image_response.status_code}")
                else:
                    logger.error(f"Invalid API response structure from Eden AI for {location_id}: {data}")
            else:
                logger.error(f"Eden AI API request failed: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Network error during Eden AI image generation: {req_err}")
        except Exception as e:
            logger.error(f"Error generating image via Eden AI: {str(e)}")
        
        return None
    
    @staticmethod
    def create_stylized_image(location_id, description, image_path, location_setting=None):
        """
        Create a stylized image with the location description
        
        Args:
            location_id (str): The ID of the location
            description (str): The location description
            image_path (Path): Where to save the image
            location_setting (str): The type of location
            
        Returns:
            str: Path to the created image
        """
        try:
            # Get the base color based on location setting
            if location_setting and location_setting.lower() in ImageClient.LOCATION_COLORS:
                base_color = ImageClient.LOCATION_COLORS[location_setting.lower()]
            else:
                # Use a color derived from the location ID if setting not recognized
                hash_obj = hashlib.md5(location_id.encode())
                hash_digest = hash_obj.digest()
                base_color = (hash_digest[0] % 200 + 55, hash_digest[1] % 200 + 55, hash_digest[2] % 200 + 55)
            
            # Create a gradient background
            img = ImageClient.create_gradient_background(512, 384, base_color)
            
            # Add decorative elements based on location type
            img = ImageClient.add_decorative_elements(img, location_setting)
            
            # Add text to the image
            img = ImageClient.add_text_to_image(img, location_id, description)
            
            # Save the image
            img.save(str(image_path), "JPEG", quality=95)
            logger.info(f"Created stylized image for location {location_id} at {image_path}")
            
            return str(image_path)
            
        except Exception as e:
            logger.error(f"Error creating stylized image: {str(e)}")
            # Fall back to the most basic image generation if everything else fails
            return ImageClient.create_basic_image(location_id, description, image_path)
    
    @staticmethod
    def create_gradient_background(width, height, base_color):
        """Create a gradient background image"""
        # Create a new image with white background
        img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Create a gradient fill
        r, g, b = base_color
        for y in range(height):
            # Calculate gradient color (darker at bottom)
            factor = 1 - (y / height * 0.5)
            gradient_color = (
                int(r * factor),
                int(g * factor),
                int(b * factor)
            )
            # Draw a line with this color
            draw.line([(0, y), (width, y)], fill=gradient_color)
            
        # Add some noise for texture
        img = ImageClient.add_noise(img, 10)
        
        # Slightly blur the image for smoother appearance
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        
        return img
    
    @staticmethod
    def add_noise(img, intensity=10):
        """Add some visual noise to an image for texture"""
        width, height = img.size
        pixels = img.load()
        
        for x in range(width):
            for y in range(height):
                r, g, b = pixels[x, y]
                noise = random.randint(-intensity, intensity)
                pixels[x, y] = (
                    max(0, min(255, r + noise)),
                    max(0, min(255, g + noise)),
                    max(0, min(255, b + noise))
                )
                
        return img
    
    @staticmethod
    def add_decorative_elements(img, location_setting=None):
        """Add decorative elements based on location type"""
        if not location_setting:
            return img
            
        width, height = img.size
        draw = ImageDraw.Draw(img)
        
        # Add specific decorations based on location type
        setting = location_setting.lower()
        
        # Shared elements for Japanese aesthetic
        # Draw a simple framing border
        border_width = 8
        inner_border = 3
        border_color = (255, 255, 255, 180)  # Semi-transparent white
        draw.rectangle([(0, 0), (width-1, height-1)], outline=border_color, width=2)
        draw.rectangle([(border_width, border_width), (width-border_width-1, height-border_width-1)], 
                      outline=border_color, width=1)
        
        # Add some pattern elements based on setting
        if "garden" in setting or "shrine" in setting or "teahouse" in setting:
            # Cherry blossom elements
            for _ in range(20):
                x = random.randint(20, width-20)
                y = random.randint(20, height-20)
                size = random.randint(5, 15)
                color = (255, 230, 240, 150)  # Light pink, semi-transparent
                draw.ellipse([(x-size, y-size), (x+size, y+size)], fill=color)
                # Add little dots for detail
                for i in range(5):
                    dot_x = x + random.randint(-size+2, size-2)
                    dot_y = y + random.randint(-size+2, size-2)
                    dot_size = 2
                    draw.ellipse([(dot_x-dot_size, dot_y-dot_size), (dot_x+dot_size, dot_y+dot_size)], 
                                fill=(255, 200, 200, 200))
        
        elif "city" in setting or "train" in setting:
            # Abstract urban elements
            for _ in range(15):
                x1 = random.randint(20, width-100)
                y1 = random.randint(height//2, height-50)
                w = random.randint(20, 80)
                h = random.randint(30, 120)
                color = (255, 255, 255, 50)  # Very transparent white
                draw.rectangle([(x1, y1), (x1+w, y1-h)], fill=color, outline=(255, 255, 255, 100))
        
        # Add a "horizon line" for certain settings
        if "city" in setting or "residential" in setting or "train" in setting:
            horizon_y = height // 3
            line_color = (255, 255, 255, 100)  # Semi-transparent white
            draw.line([(0, horizon_y), (width, horizon_y)], fill=line_color, width=2)
        
        return img
    
    @staticmethod
    def add_text_to_image(img, location_id, description):
        """Add text to the image, including location name and description"""
        width, height = img.size
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts
        try:
            title_font_size = 28
            body_font_size = 16
            
            title_font = ImageFont.truetype("arial.ttf", title_font_size)
            body_font = ImageFont.truetype("arial.ttf", body_font_size)
        except IOError:
            # Fall back to default font
            title_font = ImageFont.load_default()
            body_font = title_font
        
        # Extract the location name - use the first line/sentence or the ID
        if ":" in description:
            name = description.split(":")[0].strip()
        elif "." in description[:100]:  # Look for a period in the first 100 chars
            name = description.split(".")[0].strip()
        else:
            name = location_id.replace("-", " ").title()
            
        # Clean up name if it's too long
        if len(name) > 50:
            name = name[:47] + "..."
            
        # Create semi-transparent overlay for the text area
        overlay = Image.new('RGBA', (width, 120), (0, 0, 0, 180))
        img.paste(overlay, (0, 0), overlay)
        
        # Draw the title
        draw.text((20, 15), name, fill=(255, 255, 255), font=title_font)
        
        # Draw a line under the title
        draw.line([(20, 52), (width-20, 52)], fill=(255, 255, 255, 150), width=1)
        
        # Draw the description (first ~100 characters)
        desc_text = description
        if len(desc_text) > 200:
            desc_text = desc_text[:197] + "..."
            
        # Wrap the text to fit the width
        wrapped_text = textwrap.fill(desc_text, width=70)
        # Only take the first 2 lines
        wrapped_lines = wrapped_text.split("\n")[:2]
        wrapped_text = "\n".join(wrapped_lines)
        
        draw.text((20, 60), wrapped_text, fill=(255, 255, 255, 230), font=body_font)
        
        # Add location ID in bottom corner
        draw.text((width-100, height-25), location_id, fill=(255, 255, 255, 150), font=body_font)
        
        return img
    
    @staticmethod
    def create_basic_image(location_id, prompt, image_path):
        """
        Create a basic image with minimal styling
        
        Args:
            location_id (str): The ID of the location
            prompt (str): The description prompt
            image_path (Path): Where to save the image
            
        Returns:
            str: Path to the created image
        """
        try:
            # Create a colored background based on a hash of the location ID
            hash_obj = hashlib.md5(location_id.encode())
            hash_digest = hash_obj.digest()
            bg_color = (hash_digest[0] % 200 + 55, hash_digest[1] % 200 + 55, hash_digest[2] % 200 + 55)
            
            # Create a new image with the background color
            img = Image.new('RGB', (512, 384), color=bg_color)
            draw = ImageDraw.Draw(img)
            
            # Try to load a font, fall back to default if not available
            try:
                font_large = ImageFont.truetype("arial.ttf", 24)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except IOError:
                font_large = ImageFont.load_default()
                font_small = font_large
            
            # Draw the location ID
            location_text = f"Location: {location_id}"
            draw.text((20, 20), location_text, fill=(255, 255, 255), font=font_large)
            
            # Draw a border
            draw.rectangle([(10, 10), (502, 374)], outline=(255, 255, 255), width=2)
            
            # Draw the prompt text, wrapping it
            y_position = 70
            words = prompt.split()
            lines = []
            current_line = ""
            
            for word in words:
                if len(current_line + " " + word) <= 50:
                    current_line += " " + word if current_line else word
                else:
                    lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            for line in lines[:10]:  # Limit to 10 lines
                draw.text((20, y_position), line, fill=(255, 255, 255), font=font_small)
                y_position += 25
            
            # Add a note at the bottom
            note = "Basic Image"
            draw.text((20, 350), note, fill=(255, 255, 255), font=font_small)
            
            # Save the image
            img.save(str(image_path), "JPEG", quality=95)
            logger.info(f"Created basic image for location {location_id} at {image_path}")
            
            return str(image_path)
            
        except Exception as e:
            logger.error(f"Error creating basic image: {str(e)}")
            return None
    
    @staticmethod
    def get_image_url_for_web(location_id):
        """
        Get the URL for the image to be displayed on the web.
        
        Args:
            location_id (str): The ID of the location (e.g., loc_x,y)
            
        Returns:
            str: URL of the image for web display
        """
        # Check if the image exists (using the correct filename)
        image_path = Path(f"data/images/{location_id}.jpg")
        
        if image_path.exists():
            # Return the URL for the web (without extra prefix)
            return f"/images/{location_id}.jpg"
        else:
            # Return a default placeholder image
            # Ensure placeholder.jpg exists in data/images via create_placeholder.py
            return "/images/placeholder.jpg" 