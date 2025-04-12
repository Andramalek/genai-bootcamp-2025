#!/usr/bin/env python3
"""
Test script for Eden AI image generation via ImageClient.
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables BEFORE importing ImageClient
load_dotenv()

# Configure logging early
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the app path is correct for imports
# (This might need adjustment based on how you run it - assuming running from project root)
try:
    from app.utils.image_client import ImageClient
except ImportError:
    logger.error("Failed to import ImageClient. Make sure you run this from the project root.")
    exit(1)

def test_image_generation():
    """Tests the ImageClient.generate_location_image function."""
    logger.info("Starting ImageClient test...")
    
    # --- Test Parameters ---
    test_location_id = "test_loc_edenai"
    test_prompt = "A tranquil bamboo forest path at dawn. Items visible: Small Shrine Statue. People present: Old Monk." # Example prompt
    test_setting = "forest"
    force_new = True # Force generation even if file exists
    # ---------------------

    try:
        logger.info(f"Attempting to generate image for ID: {test_location_id}")
        logger.info(f"Prompt: {test_prompt}")
        logger.info(f"Setting: {test_setting}")
        
        result_path_str = ImageClient.generate_location_image(
            location_id=test_location_id,
            prompt=test_prompt,
            force_new=force_new,
            location_setting=test_setting
        )
        
        if result_path_str:
            result_path = Path(result_path_str)
            if result_path.exists():
                logger.info(f"SUCCESS: Image generated and saved to: {result_path}")
                print(f"\n---> Test SUCCESSFUL. Image saved at: {result_path}")
            else:
                logger.error(f"ERROR: ImageClient returned path '{result_path_str}' but file does not exist.")
                print(f"\n---> Test FAILED. File not found at reported path.")
        else:
            logger.error("ERROR: ImageClient.generate_location_image returned None.")
            print("\n---> Test FAILED. Image generation function returned None.")
            
    except Exception as e:
        logger.error(f"An unexpected error occurred during the test: {str(e)}", exc_info=True)
        print(f"\n---> Test FAILED due to unexpected exception: {e}")

if __name__ == "__main__":
    # Check for API key existence early
    if not os.getenv("EDENAI_API_KEY"):
         logger.error("EDENAI_API_KEY not found in environment. Please set it in .env")
         print("\n---> Test ABORTED. EDENAI_API_KEY missing.")
    else:
        test_image_generation() 