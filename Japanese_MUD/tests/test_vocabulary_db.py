#!/usr/bin/env python3
"""
Tests for the enhanced vocabulary system with SQLite integration.
"""

import os
import sys
import unittest
import tempfile
import json
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.language.vocabulary import VocabularyManager, VocabularyWord, VocabularyTheme
from app.player.learning_tracker import PlayerVocabulary, VocabularyKnowledge
from app.utils.database import Database


class TestVocabularyDatabase(unittest.TestCase):
    """Test the vocabulary database integration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for all tests."""
        # Create a temporary database file
        cls.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        cls.temp_db_file.close()
        
        # Override the database path in config
        from app.config import Config
        Config.DATABASE_PATH = cls.temp_db_file.name
        
        # Initialize database
        cls.db = Database.get_db_instance()
        cls.db.init_schema()
        
        # Add test vocabulary data
        cls._add_test_vocabulary_data(cls.db)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Remove temporary database file
        os.unlink(cls.temp_db_file.name)
    
    @classmethod
    def _add_test_vocabulary_data(cls, db):
        """Add test vocabulary data to the database."""
        # Add vocabulary words
        words = [
            {
                "id": "test-001",
                "japanese": "水",
                "romaji": "mizu",
                "english": "water",
                "jlpt_level": 5,
                "part_of_speech": "noun",
                "example_sentence": "水を飲みます。",
                "example_translation": "I drink water.",
                "context_categories": json.dumps(["food", "daily life"]),
                "related_words": json.dumps(["test-002"]),
                "usage_notes": "Basic word for water."
            },
            {
                "id": "test-002",
                "japanese": "飲む",
                "romaji": "nomu",
                "english": "to drink",
                "jlpt_level": 5,
                "part_of_speech": "verb",
                "example_sentence": "水を飲みます。",
                "example_translation": "I drink water.",
                "context_categories": json.dumps(["food", "daily life"]),
                "related_words": json.dumps(["test-001"]),
                "usage_notes": "Basic verb for drinking."
            },
            {
                "id": "test-003",
                "japanese": "駅",
                "romaji": "eki",
                "english": "station",
                "jlpt_level": 5,
                "part_of_speech": "noun",
                "example_sentence": "駅はどこですか？",
                "example_translation": "Where is the station?",
                "context_categories": json.dumps(["transportation", "places"]),
                "related_words": json.dumps([]),
                "usage_notes": "Used for train or bus stations."
            }
        ]
        
        for word in words:
            db.execute(
                """
                INSERT INTO vocabulary (
                    id, japanese, romaji, english, jlpt_level, part_of_speech,
                    example_sentence, example_translation, context_categories,
                    related_words, usage_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    word["id"], word["japanese"], word["romaji"], word["english"],
                    word["jlpt_level"], word["part_of_speech"], word["example_sentence"],
                    word["example_translation"], word["context_categories"],
                    word["related_words"], word["usage_notes"]
                )
            )
        
        # Add themes
        themes = [
            {
                "id": "theme-food",
                "name": "Food and Drink",
                "description": "Vocabulary related to food and drink"
            },
            {
                "id": "theme-transport",
                "name": "Transportation",
                "description": "Vocabulary related to transportation"
            }
        ]
        
        for theme in themes:
            db.execute(
                """
                INSERT INTO vocabulary_themes (id, name, description)
                VALUES (?, ?, ?)
                """,
                (theme["id"], theme["name"], theme["description"])
            )
        
        # Add words to themes
        theme_words = [
            ("theme-food", "test-001"),
            ("theme-food", "test-002"),
            ("theme-transport", "test-003")
        ]
        
        for theme_id, word_id in theme_words:
            db.execute(
                """
                INSERT INTO vocabulary_theme_words (theme_id, word_id)
                VALUES (?, ?)
                """,
                (theme_id, word_id)
            )
    
    def test_vocabulary_manager(self):
        """Test the VocabularyManager with database."""
        # Create vocabulary manager
        vocab_manager = VocabularyManager(use_db=True)
        
        # Test loading from database
        self.assertEqual(len(vocab_manager.vocabulary), 3)
        self.assertEqual(len(vocab_manager.themes), 2)
        
        # Test get_word_by_id
        word = vocab_manager.get_word_by_id("test-001")
        self.assertIsNotNone(word)
        self.assertEqual(word.japanese, "水")
        self.assertEqual(word.english, "water")
        
        # Test get_words_for_level
        n5_words = vocab_manager.get_words_for_level(5)
        self.assertEqual(len(n5_words), 3)
        
        # Test get_translation
        word = vocab_manager.get_translation("水")
        self.assertIsNotNone(word)
        self.assertEqual(word.english, "water")
        
        # Test search_word
        results = vocab_manager.search_word("water")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].japanese, "水")
        
        # Test get_words_by_theme
        food_words = vocab_manager.get_words_by_theme("theme-food")
        self.assertEqual(len(food_words), 2)
        
        # Test get_theme_by_id
        theme = vocab_manager.get_theme_by_id("theme-food")
        self.assertIsNotNone(theme)
        self.assertEqual(theme.name, "Food and Drink")
        
        # Test get_related_words
        related = vocab_manager.get_related_words("test-001")
        self.assertEqual(len(related), 1)
        self.assertEqual(related[0].japanese, "飲む")
    
    def test_player_vocabulary(self):
        """Test the PlayerVocabulary with database."""
        # Create test player
        player_id = "test-player"
        
        # Add player to database
        self.db.execute(
            """
            INSERT INTO players (player_id, username, current_location)
            VALUES (?, ?, ?)
            """,
            (player_id, "Test Player", "starting-location")
        )
        
        # Create player vocabulary
        player_vocab = PlayerVocabulary(player_id, use_db=True)
        
        # Test marking word as seen
        player_vocab.mark_word_seen("test-001")
        self.assertEqual(player_vocab.get_knowledge_level("test-001"), VocabularyKnowledge.SEEN)
        
        # Test recording test results
        player_vocab.record_test_result("test-001", True)
        self.assertEqual(player_vocab.get_knowledge_level("test-001"), VocabularyKnowledge.LEARNING)
        
        player_vocab.record_test_result("test-001", True)
        player_vocab.record_test_result("test-001", True)
        self.assertEqual(player_vocab.get_knowledge_level("test-001"), VocabularyKnowledge.FAMILIAR)
        
        # Test save and load
        self.assertTrue(player_vocab.save())
        
        # Create new instance to test loading
        new_player_vocab = PlayerVocabulary(player_id, use_db=True)
        self.assertEqual(new_player_vocab.get_knowledge_level("test-001"), VocabularyKnowledge.FAMILIAR)
        
        # Test get_words_by_knowledge
        familiar_words = new_player_vocab.get_words_by_knowledge(VocabularyKnowledge.FAMILIAR)
        self.assertEqual(len(familiar_words), 1)
        self.assertEqual(familiar_words[0], "test-001")
        
        # Test theme completion
        # Mark another word as known
        player_vocab.mark_word_seen("test-002")
        for _ in range(6):  # Make it reach KNOWN level
            player_vocab.record_test_result("test-002", True)
        
        self.assertEqual(player_vocab.get_knowledge_level("test-002"), VocabularyKnowledge.KNOWN)
        
        # Check theme completion
        words_known, total_words, completion = player_vocab.get_theme_completion("theme-food")
        self.assertEqual(words_known, 2)
        self.assertEqual(total_words, 2)
        self.assertEqual(completion, 100.0)
        
        # Test get_words_to_learn_from_theme
        transport_words = player_vocab.get_words_to_learn_from_theme("theme-transport")
        self.assertEqual(len(transport_words), 1)
        self.assertEqual(transport_words[0], "test-003")


if __name__ == "__main__":
    unittest.main() 