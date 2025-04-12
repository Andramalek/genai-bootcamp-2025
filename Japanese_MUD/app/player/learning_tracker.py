from typing import Dict, List, Optional, Tuple
import json
import os
import datetime
from enum import Enum
from pydantic import BaseModel
from app.utils.logger import game_logger
from app.utils.helpers import save_json_file, load_json_file
from app.language.vocabulary import VocabularyWord
from app.utils.database import Database

class VocabularyKnowledge(str, Enum):
    """
    Enum for tracking vocabulary knowledge levels
    """
    UNKNOWN = "unknown"         # Not seen yet
    SEEN = "seen"               # Seen but not tested
    LEARNING = "learning"       # Correctly answered 1-2 times
    FAMILIAR = "familiar"       # Correctly answered 3-5 times
    KNOWN = "known"             # Correctly answered 6+ times
    MASTERED = "mastered"       # Correctly answered 10+ times

class VocabularyRecord(BaseModel):
    """
    Represents a player's knowledge of a vocabulary word
    """
    word_id: str
    knowledge_level: VocabularyKnowledge = VocabularyKnowledge.UNKNOWN
    times_seen: int = 0
    times_tested: int = 0
    times_correct: int = 0
    last_seen: Optional[str] = None
    last_tested: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """
        Convert to dictionary for saving
        
        Returns:
            Dict representation of this record
        """
        return {
            "word_id": self.word_id,
            "knowledge_level": self.knowledge_level.value,
            "times_seen": self.times_seen,
            "times_tested": self.times_tested,
            "times_correct": self.times_correct,
            "last_seen": self.last_seen,
            "last_tested": self.last_tested,
            "notes": self.notes
        }
    
    @classmethod
    def from_db_row(cls, row: Dict) -> 'VocabularyRecord':
        """
        Create a VocabularyRecord from a database row
        
        Args:
            row: Database row as dict
            
        Returns:
            VocabularyRecord object
        """
        return cls(
            word_id=row['word_id'],
            knowledge_level=VocabularyKnowledge(row['knowledge_level']),
            times_seen=row['times_seen'],
            times_tested=row['times_tested'],
            times_correct=row['times_correct'],
            last_seen=row['last_seen'],
            last_tested=row['last_tested'],
            notes=row['notes']
        )

class PlayerVocabulary:
    """
    Tracks a player's vocabulary knowledge
    """
    def __init__(self, player_id: str, use_db: bool = True):
        """
        Initialize player vocabulary tracker
        
        Args:
            player_id: ID of the player to track
            use_db: Whether to use the database (True) or file system (False)
        """
        self.player_id = player_id
        self.use_db = use_db
        self.vocabulary_records: Dict[str, Dict] = {}
    
    def mark_word_seen(self, word_id: str):
        """
        Mark a word as seen by the player
        
        Args:
            word_id: ID of the word
        """
        if word_id not in self.vocabulary_records:
            self.vocabulary_records[word_id] = {
                "knowledge_level": VocabularyKnowledge.SEEN.value,
                "times_seen": 1,
                "times_tested": 0,
                "times_correct": 0
            }
        else:
            self.vocabulary_records[word_id]["times_seen"] += 1
            
            # Only update if currently unknown
            if self.vocabulary_records[word_id]["knowledge_level"] == VocabularyKnowledge.UNKNOWN.value:
                self.vocabulary_records[word_id]["knowledge_level"] = VocabularyKnowledge.SEEN.value
    
    def record_test_result(self, word_id: str, correct: bool):
        """
        Record the result of testing a word
        
        Args:
            word_id: ID of the word
            correct: Whether the player answered correctly
        """
        if word_id not in self.vocabulary_records:
            self.vocabulary_records[word_id] = {
                "knowledge_level": VocabularyKnowledge.UNKNOWN.value,
                "times_seen": 0,
                "times_tested": 1,
                "times_correct": 1 if correct else 0
            }
        else:
            record = self.vocabulary_records[word_id]
            record["times_tested"] += 1
            
            if correct:
                record["times_correct"] += 1
                
                # Update knowledge level based on number of correct answers
                if record["times_correct"] >= 10:
                    record["knowledge_level"] = VocabularyKnowledge.MASTERED.value
                elif record["times_correct"] >= 6:
                    record["knowledge_level"] = VocabularyKnowledge.KNOWN.value
                elif record["times_correct"] >= 3:
                    record["knowledge_level"] = VocabularyKnowledge.FAMILIAR.value
                else:
                    record["knowledge_level"] = VocabularyKnowledge.LEARNING.value
    
    def get_knowledge_level(self, word_id: str) -> VocabularyKnowledge:
        """
        Get a player's knowledge level for a specific word
        
        Args:
            word_id: ID of the word
            
        Returns:
            VocabularyKnowledge level
        """
        if word_id not in self.vocabulary_records:
            return VocabularyKnowledge.UNKNOWN
            
        return VocabularyKnowledge(self.vocabulary_records[word_id]["knowledge_level"])
    
    def get_vocabulary_stats(self) -> Dict[str, int]:
        """
        Get statistics about player's vocabulary knowledge
        
        Returns:
            Dict with counts for each knowledge level
        """
        stats = {level.value: 0 for level in VocabularyKnowledge}
        
        for record in self.vocabulary_records.values():
            stats[record["knowledge_level"]] += 1
            
        return stats
    
    def get_word_record(self, word_id: str) -> Optional[Dict]:
        """
        Get a player's knowledge record for a specific word
        
        Args:
            word_id: ID of the word
            
        Returns:
            VocabularyRecord if found, None otherwise
        """
        return self.vocabulary_records.get(word_id)
    
    def get_words_by_knowledge(self, level: VocabularyKnowledge) -> List[str]:
        """
        Get all word IDs with a specific knowledge level
        
        Args:
            level: Knowledge level to filter by
            
        Returns:
            List of word IDs
        """
        return [word_id for word_id, record in self.vocabulary_records.items()
                if record["knowledge_level"] == level.value]
    
    def get_words_above_knowledge(self, level: VocabularyKnowledge) -> List[str]:
        """
        Get all word IDs with knowledge level at or above specified level
        
        Args:
            level: Minimum knowledge level
            
        Returns:
            List of word IDs
        """
        level_values = [e.value for e in VocabularyKnowledge]
        min_level_index = level_values.index(level.value)
        
        return [word_id for word_id, record in self.vocabulary_records.items()
                if level_values.index(record["knowledge_level"]) >= min_level_index]
    
    def get_words_for_review(self, max_count: int = 10) -> List[str]:
        """
        Get words for review, prioritizing those that:
        1. Are in the learning phase
        2. Haven't been tested recently
        3. Have been seen but not tested
        
        Args:
            max_count: Maximum number of words to return
            
        Returns:
            List of word IDs for review
        """
        # Convert records to list for sorting
        records = list(self.vocabulary_records.items())
        
        # Sort by priority:
        # 1. Learning words first
        # 2. Then familiar words
        # 3. Then seen but not tested words
        # 4. Then by last tested date (oldest first)
        def sort_key(item):
            word_id, record = item
            
            # Priority based on knowledge level
            if record["knowledge_level"] == VocabularyKnowledge.LEARNING.value:
                priority = 0
            elif record["knowledge_level"] == VocabularyKnowledge.FAMILIAR.value:
                priority = 1
            elif record["knowledge_level"] == VocabularyKnowledge.SEEN.value and record["times_tested"] == 0:
                priority = 2
            else:
                priority = 3
                
            # Sort by last tested date if available, otherwise by last seen date
            if record["last_tested"]:
                date = record["last_tested"]
            elif record["last_seen"]:
                date = record["last_seen"]
            else:
                date = "9999-99-99"  # Default to future date if no dates available
                
            return (priority, date)
            
        records.sort(key=sort_key)
        
        # Return word IDs, limited to max_count
        return [word_id for word_id, _ in records[:max_count]]
    
    def get_theme_completion(self, theme_id: str) -> Tuple[int, int, float]:
        """
        Get completion statistics for a vocabulary theme
        
        Args:
            theme_id: ID of the theme
            
        Returns:
            Tuple of (words_known, total_words, completion_percentage)
        """
        # Get theme from vocabulary manager
        from app.language.vocabulary import VocabularyManager
        vocab_manager = VocabularyManager(use_db=self.use_db)
        theme = vocab_manager.get_theme_by_id(theme_id)
        
        if not theme:
            return (0, 0, 0.0)
            
        # Count known words (familiar, known, or mastered)
        known_levels = [
            VocabularyKnowledge.FAMILIAR.value,
            VocabularyKnowledge.KNOWN.value,
            VocabularyKnowledge.MASTERED.value
        ]
        
        words_known = 0
        for word_id in theme.words:
            record = self.get_word_record(word_id)
            if record and record["knowledge_level"] in known_levels:
                words_known += 1
                
        total_words = len(theme.words)
        completion_percentage = (words_known / total_words * 100) if total_words > 0 else 0
        
        return (words_known, total_words, completion_percentage)
    
    def get_all_theme_completion(self) -> Dict[str, Tuple[int, int, float]]:
        """
        Get completion statistics for all vocabulary themes
        
        Returns:
            Dict mapping theme_id to (words_known, total_words, completion_percentage)
        """
        # Get all themes from vocabulary manager
        from app.language.vocabulary import VocabularyManager
        vocab_manager = VocabularyManager(use_db=self.use_db)
        themes = vocab_manager.get_all_themes()
        
        result = {}
        for theme in themes:
            result[theme.id] = self.get_theme_completion(theme.id)
            
        return result
    
    def get_words_to_learn_from_theme(self, theme_id: str, max_count: int = 5) -> List[str]:
        """
        Get words from a theme that the player needs to learn
        
        Args:
            theme_id: ID of the theme
            max_count: Maximum number of words to return
            
        Returns:
            List of word IDs to learn
        """
        # Get theme from vocabulary manager
        from app.language.vocabulary import VocabularyManager
        vocab_manager = VocabularyManager(use_db=self.use_db)
        theme = vocab_manager.get_theme_by_id(theme_id)
        
        if not theme:
            return []
            
        # Find words that are unknown or just seen
        candidates = []
        for word_id in theme.words:
            record = self.get_word_record(word_id)
            if not record or record["knowledge_level"] in [VocabularyKnowledge.UNKNOWN.value, VocabularyKnowledge.SEEN.value]:
                candidates.append(word_id)
                
        # Sort by knowledge level (unknown first, then seen)
        # and by times seen (least seen first)
        def sort_key(word_id):
            record = self.get_word_record(word_id)
            if not record:
                return (0, 0)  # Unknown, never seen
            return (1 if record["knowledge_level"] == VocabularyKnowledge.SEEN.value else 0, record["times_seen"])
            
        candidates.sort(key=sort_key)
        
        # Return limited number of words
        return candidates[:max_count] 