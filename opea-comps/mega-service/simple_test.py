#!/usr/bin/env python3
"""
Simple test script for the Japanese TTS service
This script makes a single request to each endpoint to verify the service is working
"""

import requests
import os
import sys
import json
import time

SERVICE_URL = "http://localhost:8082"

def print_separator():
    print("=" * 70)

def wait_for_service():
    """Wait for the service to be available"""
    print("Waiting for service to be ready...")
    max_retries = 10
    for i in range(max_retries):
        try:
            # Just try to connect, don't care about the response
            requests.get(f"{SERVICE_URL}", timeout=2)
            print("Service is ready!")
            return True
        except requests.exceptions.ConnectionError:
            print(f"Service not ready yet, retrying ({i+1}/{max_retries})...")
            time.sleep(3)
    
    print("Service not available after multiple attempts")
    return False

def test_basic_tts():
    """Test basic Japanese TTS functionality"""
    print_separator()
    print("Testing basic TTS...")
    
    url = f"{SERVICE_URL}/v1/japanese_tts"
    payload = {
        "text": "こんにちは、元気ですか?"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            # Save the audio
            with open("test_basic.mp3", "wb") as f:
                f.write(response.content)
            print(f"✅ Success! Audio saved to test_basic.mp3")
            return True
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_translation():
    """Test English to Japanese translation and TTS"""
    print_separator()
    print("Testing translation...")
    
    url = f"{SERVICE_URL}/v1/translate_and_speak"
    payload = {
        "text": "Hello, how are you today?",
        "model": "phi",
        "include_details": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)  # Translation might take longer
        
        if response.status_code == 200:
            # Save the audio
            with open("test_translation.mp3", "wb") as f:
                f.write(response.content)
                
            # Check if details were returned in headers
            if "X-Translation-Details" in response.headers:
                details = json.loads(response.headers["X-Translation-Details"])
                print("\nTranslation details:")
                print(f"Japanese: {details.get('original', 'N/A')}")
                print(f"Romaji: {details.get('romaji', 'N/A')}")
                
            print(f"✅ Success! Audio saved to test_translation.mp3")
            return True
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def run_all_tests():
    """Run all available tests"""
    success = wait_for_service()
    if not success:
        return False
    
    # Run tests
    success = test_basic_tts()
    success = test_translation() and success
    
    print_separator()
    if success:
        print("🎉 All tests passed successfully!")
    else:
        print("⚠️ Some tests failed")
    
    return success

if __name__ == "__main__":
    print("Simple Japanese TTS Service Test")
    print_separator()
    
    success = run_all_tests()
    sys.exit(0 if success else 1) 