#!/usr/bin/env python3
"""
Database migration script for Japanese MUD game.
Initializes or updates the SQLite database schema and imports data from JSON files.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.utils.database import Database
from app.utils.logger import game_logger
from app.config import Config


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Database migration for Japanese MUD")
    parser.add_argument("--reset", action="store_true", help="Reset the database before migration")
    parser.add_argument("--import-data", action="store_true", help="Import data from JSON files")
    parser.add_argument("--check", action="store_true", help="Check database status")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()


def reset_database(db: Database):
    """Drop all tables and recreate them."""
    # Tables to drop in reverse dependency order
    tables = [
        "vocabulary_theme_words",
        "vocabulary_themes", 
        "player_vocabulary",
        "player_inventory",
        "players",
        "location_npcs",
        "location_items",
        "location_exits",
        "locations",
        "npcs",
        "items",
        "vocabulary"
    ]
    
    game_logger.info("Dropping all tables...")
    for table in tables:
        try:
            db.execute(f"DROP TABLE IF EXISTS {table}")
            game_logger.info(f"Dropped table {table}")
        except Exception as e:
            game_logger.error(f"Error dropping table {table}: {e}")
    
    game_logger.info("All tables dropped successfully")


def check_database(db: Database, verbose=False):
    """Check the status of the database."""
    # Get list of tables
    rows = db.fetch_all(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    
    tables = [row['name'] for row in rows if not row['name'].startswith('sqlite_')]
    
    game_logger.info(f"Database has {len(tables)} tables: {', '.join(tables)}")
    
    # Check counts in each table
    if verbose:
        for table in tables:
            count = db.fetch_one(f"SELECT COUNT(*) as count FROM {table}")
            game_logger.info(f"Table {table}: {count['count']} rows")
    
    # Check vocabulary counts by JLPT level
    vocab_counts = db.fetch_all(
        "SELECT jlpt_level, COUNT(*) as count FROM vocabulary GROUP BY jlpt_level ORDER BY jlpt_level"
    )
    
    for row in vocab_counts:
        game_logger.info(f"Vocabulary N{row['jlpt_level']}: {row['count']} words")
    
    # Check theme counts
    theme_counts = db.fetch_all(
        "SELECT t.name, COUNT(tw.word_id) as word_count " 
        "FROM vocabulary_themes t "
        "LEFT JOIN vocabulary_theme_words tw ON t.id = tw.theme_id "
        "GROUP BY t.id"
    )
    
    game_logger.info("Vocabulary themes:")
    for row in theme_counts:
        game_logger.info(f"- {row['name']}: {row['word_count']} words")


def main():
    """Run the migration script."""
    args = parse_args()
    
    config = Config()
    
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(config.DATABASE_PATH)
    os.makedirs(db_dir, exist_ok=True)
    
    # Initialize database connection
    db = Database.get_db_instance()
    
    if args.reset:
        reset_database(db)
    
    # Initialize schema
    game_logger.info("Initializing database schema...")
    db.init_schema()
    game_logger.info("Schema initialized successfully")
    
    if args.import_data:
        game_logger.info("Importing data from JSON files...")
        db.import_data()
        game_logger.info("Data imported successfully")
    
    if args.check or args.verbose:
        check_database(db, args.verbose)
    
    game_logger.info("Migration completed successfully")


if __name__ == "__main__":
    main() 