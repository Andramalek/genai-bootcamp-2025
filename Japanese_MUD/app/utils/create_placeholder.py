#!/usr/bin/env python3
"""
Create a simple placeholder image for locations without generated images.
"""

import os
from pathlib import Path
import logging
from PIL import Image, ImageDraw, ImageFont

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_placeholder_image():
    """Create a simple placeholder image for locations without generated images."""
    try:
        # Ensure the directory exists
        image_dir = Path("data/images")
        image_dir.mkdir(exist_ok=True, parents=True)
        placeholder_path = image_dir / "placeholder.jpg"

        # Check if it already exists to avoid recreating unnecessarily
        if placeholder_path.exists():
             logger.info(f"Placeholder image already exists at {placeholder_path}")
             return str(placeholder_path)

        # Create a placeholder image (512x512 with text)
        width, height = 512, 512
        image = Image.new("RGB", (width, height), color=(74, 110, 169))  # Blue background
        
        draw = ImageDraw.Draw(image)
        
        draw.rectangle([(0, 0), (width-1, height-1)], outline=(255, 255, 255), width=5)
        
        # Add some text (simple version without relying on font measurements)
        try:
            # Try to use a font if available
            font = ImageFont.truetype("arial.ttf", 32)
        except (IOError, ImportError):
            font = ImageFont.load_default()
            
        draw.text((width // 2 - 100, height // 2 - 20), "Location Image", fill=(255, 255, 255), font=font)
        draw.text((width // 2 - 60, height // 2 + 20), "Placeholder", fill=(255, 255, 255), font=font)
        
        image.save(placeholder_path, "JPEG")
        
        logger.info(f"Placeholder image created at {placeholder_path}")
        return str(placeholder_path)
    
    except Exception as e:
        logger.error(f"Failed to create placeholder image: {e}")
        return None

if __name__ == "__main__":
    result = create_placeholder_image()
    print(f"Placeholder image check complete. Status: {'Exists/Created' if result else 'Failed'}") 