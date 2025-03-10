#!/usr/bin/env python
"""
Japanese TTS Service Tester
---------------------------
This script provides a simple way to test the various endpoints
of the Japanese TTS service.
"""

import requests
import json
import sys
import argparse
import os

# Default service URL
SERVICE_URL = "http://localhost:8082"

def save_audio(response, filename):
    """Save audio response to a file"""
    with open(filename, 'wb') as f:
        f.write(response.content)
    print(f"Audio saved to {filename}")

def test_basic_tts(text, output_file="japanese_speech.mp3"):
    """Test basic Japanese TTS functionality"""
    print(f"\n📢 Testing Basic TTS with: {text}")
    
    url = f"{SERVICE_URL}/v1/japanese_tts"
    payload = {
        "text": text
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            save_audio(response, output_file)
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Request failed: {e}")
        return False

def test_translation(text, model="phi", include_details=True, output_file="translated_speech.mp3"):
    """Test English to Japanese translation and TTS"""
    print(f"\n🔄 Testing Translation with: {text}")
    
    url = f"{SERVICE_URL}/v1/translate_and_speak"
    payload = {
        "text": text,
        "model": model,
        "include_details": include_details
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            save_audio(response, output_file)
            
            # Check if details were returned in headers
            if include_details and "X-Translation-Details" in response.headers:
                details = json.loads(response.headers["X-Translation-Details"])
                print("\nTranslation Details:")
                if "original" in details:
                    print(f"Japanese: {details['original']}")
                if "romaji" in details:
                    print(f"Romaji: {details['romaji']}")
                if "furigana" in details:
                    print("Kanji readings:")
                    for item in details["furigana"]:
                        print(f"  {item['kanji']} -> {item['reading']}")
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Request failed: {e}")
        return False

def test_learning_mode(text, is_english=True, model="phi", output_file="learning.mp3"):
    """Test the learning mode with word breakdown"""
    print(f"\n📚 Testing Learning Mode with: {text}")
    
    url = f"{SERVICE_URL}/v1/learning_mode"
    payload = {
        "text": text,
        "is_english": is_english,
        "model": model
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            # Save the audio response
            save_audio(response, output_file)
            
            # Check if text details were returned in headers
            if "X-Text-Details" in response.headers:
                details = json.loads(response.headers["X-Text-Details"])
                print("\nLearning Details:")
                print(f"Japanese: {details.get('original', '')}")
                print(f"Romaji: {details.get('romaji', '')}")
                
                if "words" in details:
                    print("\nWord breakdown:")
                    for word in details["words"]:
                        print(f"  {word['surface']} ({word['reading']}) - {word['pos']}")
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Request failed: {e}")
        return False

def test_example_generator(keyword, count=3, model="phi"):
    """Test example sentence generation"""
    print(f"\n🔍 Generating Examples with keyword: {keyword}")
    
    url = f"{SERVICE_URL}/v1/example_generator"
    payload = {
        "keyword": keyword,
        "count": count,
        "model": model,
        "generate_audio": False
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\nGenerated Examples:")
            print(data.get("examples", "No examples generated"))
            
            # Check if parsed examples exist
            if "parsed_examples" in data:
                print("\nParsed Examples:")
                for i, example in enumerate(data["parsed_examples"]):
                    print(f"\nExample {i+1}:")
                    print(f"  Japanese: {example.get('japanese', '')}")
                    print(f"  Romaji: {example.get('romaji', '')}")
                    print(f"  English: {example.get('english', '')}")
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Request failed: {e}")
        return False

def show_help():
    """Display help information"""
    print("""
Japanese TTS Service Tester
---------------------------
Usage:
  python test_japanese_tts.py [command] [arguments]

Commands:
  tts           - Test basic Japanese TTS
    Arguments:  [japanese_text] [output_filename]
    Example:    python test_japanese_tts.py tts "こんにちは" hello.mp3
  
  translate     - Test English to Japanese translation
    Arguments:  [english_text] [model_name] [output_filename]
    Example:    python test_japanese_tts.py translate "Hello, how are you?" phi greeting.mp3
  
  learning      - Test learning mode
    Arguments:  [text] [is_english(true/false)] [model_name] [output_filename]
    Example:    python test_japanese_tts.py learning "I am a student" true phi learning.mp3
  
  examples      - Test example generation
    Arguments:  [keyword] [count] [model_name]
    Example:    python test_japanese_tts.py examples "食べる" 3 phi
    
  all           - Run all tests with default values
    Example:    python test_japanese_tts.py all
    """)

def run_all_tests():
    """Run all tests with default values"""
    print("\n🧪 Running all tests with default values...")
    
    # Test basic TTS
    test_basic_tts("こんにちは、元気ですか？", "test_basic.mp3")
    
    # Test translation
    test_translation("Hello, how are you today?", "phi", True, "test_translation.mp3")
    
    # Test learning mode
    test_learning_mode("I want to learn Japanese", True, "phi", "test_learning.mp3")
    
    # Test example generator
    test_example_generator("食べる", 2, "phi")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the Japanese TTS Service")
    parser.add_argument("command", nargs="?", help="Command to run (tts, translate, learning, examples, all)")
    parser.add_argument("args", nargs="*", help="Arguments for the command")
    
    args = parser.parse_args()
    
    if args.command is None or args.command.lower() == "help":
        show_help()
    elif args.command.lower() == "tts":
        if len(args.args) >= 1:
            text = args.args[0]
            output_file = args.args[1] if len(args.args) >= 2 else "japanese_speech.mp3"
            test_basic_tts(text, output_file)
        else:
            print("Error: Text argument required for TTS test")
    elif args.command.lower() == "translate":
        if len(args.args) >= 1:
            text = args.args[0]
            model = args.args[1] if len(args.args) >= 2 else "phi"
            output_file = args.args[2] if len(args.args) >= 3 else "translated_speech.mp3"
            test_translation(text, model, True, output_file)
        else:
            print("Error: Text argument required for translation test")
    elif args.command.lower() == "learning":
        if len(args.args) >= 1:
            text = args.args[0]
            is_english = args.args[1].lower() == "true" if len(args.args) >= 2 else True
            model = args.args[2] if len(args.args) >= 3 else "phi"
            output_file = args.args[3] if len(args.args) >= 4 else "learning.mp3"
            test_learning_mode(text, is_english, model, output_file)
        else:
            print("Error: Text argument required for learning mode test")
    elif args.command.lower() == "examples":
        if len(args.args) >= 1:
            keyword = args.args[0]
            count = int(args.args[1]) if len(args.args) >= 2 else 3
            model = args.args[2] if len(args.args) >= 3 else "phi"
            test_example_generator(keyword, count, model)
        else:
            print("Error: Keyword argument required for example generation")
    elif args.command.lower() == "all":
        run_all_tests()
    else:
        print(f"Unknown command: {args.command}")
        show_help() 