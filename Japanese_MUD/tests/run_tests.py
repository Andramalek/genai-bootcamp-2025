#!/usr/bin/env python3
"""
Test runner for Japanese MUD game.
"""

import os
import sys
import unittest
import tempfile
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.utils.logger import game_logger
from app.utils.database import Database


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run tests for Japanese MUD")
    parser.add_argument("--verbosity", type=int, default=2, help="Verbosity level (1-3)")
    parser.add_argument("--pattern", type=str, default="test_*.py", help="Test file pattern")
    parser.add_argument("--use-temp-db", action="store_true", help="Use temporary database for tests")
    return parser.parse_args()


def setup_test_environment(use_temp_db=False):
    """Set up test environment."""
    if use_temp_db:
        # Create a temporary database for testing
        temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db_file.close()
        
        # Override the database path in config
        from app.config import Config
        Config.DATABASE_PATH = temp_db_file.name
        
        # Initialize database
        db = Database.get_db_instance()
        db.init_schema()
        
        game_logger.info(f"Using temporary database at {temp_db_file.name}")
        return temp_db_file.name
    return None


def cleanup_test_environment(temp_db_path=None):
    """Clean up test environment."""
    if temp_db_path and os.path.exists(temp_db_path):
        os.unlink(temp_db_path)
        game_logger.info(f"Removed temporary database at {temp_db_path}")


def main():
    """Run all tests."""
    args = parse_args()
    
    # Set up test environment
    temp_db_path = setup_test_environment(args.use_temp_db)
    
    try:
        # Discover and run tests
        start_dir = os.path.dirname(os.path.abspath(__file__))
        test_suite = unittest.defaultTestLoader.discover(start_dir, pattern=args.pattern)
        test_runner = unittest.TextTestRunner(verbosity=args.verbosity)
        test_result = test_runner.run(test_suite)
        
        # Return non-zero exit code if tests failed
        if not test_result.wasSuccessful():
            sys.exit(1)
    finally:
        # Clean up test environment
        cleanup_test_environment(temp_db_path)


if __name__ == "__main__":
    main() 