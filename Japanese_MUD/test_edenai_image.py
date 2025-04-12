#!/usr/bin/env python3
"""
Test script to verify Eden AI API image generation (OpenAI provider).
"""
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("edenai_test")

# Load environment variables
load_dotenv()

def test_edenai_image_generation():
    """Test if Eden AI API can generate images with the current API key"""
    
    # Get API key
    api_key = os.getenv("EDENAI_API_KEY")
    if not api_key or api_key == "YOUR_EDENAI_API_KEY_HERE":
        logger.error("EDENAI_API_KEY not found or not set in environment variables")
        return False
    
    logger.info(f"Found Eden AI API key (length: {len(api_key)})")
    
    # Create output directory
    output_dir = Path("test_output_edenai")
    output_dir.mkdir(exist_ok=True)
    
    # Set up API request
    api_url = "https://api.edenai.run/v2/image/generation"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Test prompt
    prompt = "A photorealistic painting of a red panda sitting in a bamboo forest, detailed fur, cinematic lighting."
    
    # Create payload for Eden AI text-to-image generation
    payload = {
        "providers": "openai", # Use OpenAI via Eden AI
        "text": prompt,
        "resolution": "1024x1024",
        "num_images": 1,
        "fallback_providers": "" # Optional: Specify fallback if OpenAI fails
    }
    
    try:
        # Make the request
        logger.info(f"Sending request to Eden AI API for image generation...")
        start_time = time.time()
        response = requests.post(api_url, headers=headers, json=payload, timeout=90) # Longer timeout
        elapsed_time = time.time() - start_time
        logger.info(f"Request completed in {elapsed_time:.2f} seconds.")
        
        # Log response status
        logger.info(f"Response status code: {response.status_code}")
        
        # Check if successful
        if response.status_code == 200:
            response_data = response.json()
            
            # Save full response for debugging
            with open(output_dir / "edenai_response.json", "w") as f:
                json.dump(response_data, f, indent=2)
            logger.info(f"Full response saved to {output_dir / 'edenai_response.json'}")
            
            # Try to extract image data from the OpenAI provider result
            if "openai" in response_data and "items" in response_data["openai"] and len(response_data["openai"]["items"]) > 0:
                image_item = response_data["openai"]["items"][0]
                
                if "image_resource_url" in image_item:
                    image_url = image_item["image_resource_url"]
                    logger.info(f"Image URL received: {image_url}")
                    
                    # Download the image
                    logger.info("Attempting to download the image...")
                    image_response = requests.get(image_url, stream=True, timeout=60)
                    
                    if image_response.status_code == 200:
                        output_path = output_dir / "edenai_test_image.jpg"
                        with open(output_path, "wb") as f:
                            for chunk in image_response.iter_content(1024):
                                f.write(chunk)
                        logger.info(f"Successfully generated and saved image to {output_path}")
                        return True
                    else:
                        logger.error(f"Failed to download image from URL. Status: {image_response.status_code}")
                        return False
                else:
                    logger.error("'image_resource_url' not found in the Eden AI response item.")
                    return False
            else:
                logger.error("No 'openai' provider results or no 'items' found in the response.")
                return False
                
        else:
            # Log error details
            error_msg = f"API request failed with status {response.status_code}"
            try:
                error_details = response.json()
                with open(output_dir / "edenai_error.json", "w") as f:
                    json.dump(error_details, f, indent=2)
                error_msg += f": {error_details}"
            except:
                error_msg += f": {response.text}"
            
            logger.error(error_msg)
            return False
            
    except requests.exceptions.Timeout:
         logger.error("API request timed out.")
         return False
    except Exception as e:
        logger.error(f"Error during Eden AI API request: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Eden AI API image generation (OpenAI provider)...")
    success = test_edenai_image_generation()
    
    if success:
        print("✅ Test passed! Eden AI successfully generated and downloaded an image.")
        print(f"  Check the {Path('test_output_edenai').resolve()} directory for the results.")
    else:
        print("❌ Test failed. See logs above for details.")
        print("  Check API key, credits, and Eden AI service status.") 