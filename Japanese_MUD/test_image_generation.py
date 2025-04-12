#!/usr/bin/env python3
"""
Test script for image generation functionality
"""
import os
import sys
import logging
import requests
import time
from dotenv import load_dotenv
from pathlib import Path

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("image_test")

# Load environment variables
load_dotenv()

def test_api_connection():
    """Test basic connectivity to the API endpoint"""
    from app.utils.image_client import ImageClient
    
    is_api_available = ImageClient.is_api_available()
    if is_api_available:
        logger.info("CLINDROP API is available")
    else:
        logger.warning("CLINDROP API is not available - will use mock images")
    
    return is_api_available

def test_image_generation(use_mock=False):
    """Test the actual image generation"""
    from app.utils.image_client import ImageClient
    
    # Define test parameters
    test_location_id = "test-location"
    test_prompt = "A beautiful Japanese garden with cherry blossoms"
    force_new = True
    
    try:
        logger.info(f"Attempting to generate test image for '{test_prompt}'")
        
        # Clear any existing test image
        test_image_path = Path("data/images") / f"location_{test_location_id}.jpg"
        if test_image_path.exists():
            os.remove(test_image_path)
        
        start_time = time.time()
        
        # Generate the image
        result = ImageClient.generate_location_image(
            test_location_id, 
            test_prompt,
            force_new
        )
        
        elapsed_time = time.time() - start_time
        
        if result:
            image_path = Path(result)
            if image_path.exists():
                file_size = os.path.getsize(image_path)
                logger.info(f"Image generated successfully: {result}")
                logger.info(f"File size: {file_size} bytes, Generation time: {elapsed_time:.2f} seconds")
                
                # Check if it's a mock image by looking for "Mock" in the image metadata or by size
                if file_size < 50000:  # Mock images are typically smaller
                    logger.info("This appears to be a mock image based on file size")
                
                return True
            else:
                logger.error(f"Image path returned but file does not exist: {result}")
                return False
        else:
            logger.error("Image generation failed with None result")
            return False
            
    except Exception as e:
        logger.error(f"Exception during image generation: {str(e)}", exc_info=True)
        return False

def test_web_image_url():
    """Test getting the web URL for an image"""
    from app.utils.image_client import ImageClient
    
    # Test with an existing image
    test_location_id = "test-location"
    url = ImageClient.get_image_url_for_web(test_location_id)
    logger.info(f"Image URL for {test_location_id}: {url}")
    
    # Test with a non-existent image
    nonexistent_id = "nonexistent-location"
    url = ImageClient.get_image_url_for_web(nonexistent_id)
    logger.info(f"Image URL for {nonexistent_id}: {url}")
    
    return True

if __name__ == "__main__":
    print("Starting image generation test...")
    
    # First test API connection
    api_available = test_api_connection()
    print(f"API connection: {'✅ Available' if api_available else '❌ Unavailable'}")
    
    # Test image generation
    print("Testing image generation...")
    generation_ok = test_image_generation()
    
    if generation_ok:
        print("✅ Image generation test passed!")
        
        # Test web URL function
        print("Testing web URL generation...")
        url_ok = test_web_image_url()
        
        if url_ok:
            print("✅ Web URL test passed!")
        else:
            print("❌ Web URL test failed!")
    else:
        print("❌ Image generation test failed!")
    
    print("Test complete. Check the logs for details.") 