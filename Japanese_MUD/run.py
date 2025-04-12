#!/usr/bin/env python3
"""
Japanese Language Learning MUD Game
Entry point for the application
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if required API keys are set
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not found in environment variables")
    print("Please add it to your .env file")
    exit(1)

# This import is done after checking environment variables
from app.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nThank you for playing! さようなら！")
    except Exception as e:
        print(f"An error occurred: {e}")
        if os.getenv("DEBUG", "").lower() == "true":
            import traceback
            traceback.print_exc() 