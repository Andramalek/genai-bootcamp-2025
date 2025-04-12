from typing import Dict, List, Optional, Tuple
from app.models.player import Player
from app.language.vocabulary import VocabularyWord, VocabularyManager
from app.utils.logger import game_logger

class LearningTracker:
    """
    Tracks player progress in learning Japanese vocabulary
    """
    def __init__(self, player: Player, vocabulary_manager: VocabularyManager):
        """
        Initialize the learning tracker
        
        Args:
            player: Player whose progress to track
            vocabulary_manager: VocabularyManager instance
        """
        self.player = player
        self.vocabulary_manager = vocabulary_manager
        
    def get_learned_words(self) -> List[Tuple[VocabularyWord, float]]:
        """
        Get all words the player has learned with their proficiency
        
        Returns:
            List of (vocabulary_word, proficiency) tuples
        """
        learned = []
        for word_id, proficiency in self.player.learned_words.items():
            word = self.vocabulary_manager.get_word_by_id(word_id)
            if word:
                learned.append((word, proficiency))
        return learned
    
    def get_proficiency(self, word_id: str) -> float:
        """
        Get player's proficiency with a specific word
        
        Args:
            word_id: ID of the vocabulary word
            
        Returns:
            Proficiency level (0.0-1.0), 0.0 if not learned
        """
        return self.player.learned_words.get(word_id, 0.0)
    
    def learn_word(self, word_id: str, proficiency_increase: float = 0.2) -> float:
        """
        Record that a player has learned or practiced a word
        
        Args:
            word_id: ID of the vocabulary word
            proficiency_increase: Amount to increase proficiency by (0.0-1.0)
            
        Returns:
            New proficiency level for the word
        """
        current_proficiency = self.player.learned_words.get(word_id, 0.0)
        new_proficiency = min(1.0, current_proficiency + proficiency_increase)
        self.player.learned_words[word_id] = new_proficiency
        self.player.save()
        
        word = self.vocabulary_manager.get_word_by_id(word_id)
        if word:
            game_logger.info(f"Player {self.player.username} learned word {word.japanese} (proficiency: {new_proficiency:.2f})")
        
        # Check if player should level up
        self._check_level_up()
        
        return new_proficiency
    
    def get_learned_word_count(self, min_proficiency: float = 0.6) -> int:
        """
        Get the count of words the player has learned at a given proficiency
        
        Args:
            min_proficiency: Minimum proficiency to consider a word "learned"
            
        Returns:
            Number of words learned
        """
        return sum(1 for prof in self.player.learned_words.values() if prof >= min_proficiency)
    
    def get_mastered_word_count(self) -> int:
        """
        Get the count of words the player has mastered (proficiency = 1.0)
        
        Returns:
            Number of words mastered
        """
        return sum(1 for prof in self.player.learned_words.values() if prof >= 0.95)
    
    def get_next_word_to_learn(self) -> Optional[VocabularyWord]:
        """
        Get a word the player should learn next based on their JLPT level
        
        Returns:
            VocabularyWord to learn, or None if no suitable word found
        """
        # Get a random word at the player's current JLPT level
        # that they haven't learned yet or have low proficiency with
        level_words = self.vocabulary_manager.get_words_for_level(self.player.jlpt_level)
        candidate_words = []
        
        for word in level_words:
            proficiency = self.player.learned_words.get(word.id, 0.0)
            if proficiency < 0.5:  # Only suggest words with low proficiency
                candidate_words.append((word, proficiency))
                
        if not candidate_words:
            # No suitable words found, just get a random word
            return self.vocabulary_manager.get_word_for_level(self.player.jlpt_level)
            
        # Sort by proficiency (ascending) to prioritize completely unlearned words
        candidate_words.sort(key=lambda x: x[1])
        return candidate_words[0][0]
    
    def _check_level_up(self) -> bool:
        """
        Check if the player should level up to the next JLPT level
        
        Returns:
            True if player leveled up, False otherwise
        """
        # Don't level up if already at N1
        if self.player.jlpt_level <= 1:
            return False
            
        # Count how many words at current level the player has learned well
        current_level = self.player.jlpt_level
        level_words = self.vocabulary_manager.get_words_for_level(current_level)
        
        # Not enough words at this level to judge
        if len(level_words) < 5:
            return False
            
        # Calculate what percentage of words at this level the player knows well
        level_word_ids = [word.id for word in level_words]
        known_words = sum(1 for word_id in level_word_ids 
                          if self.player.learned_words.get(word_id, 0.0) >= 0.7)
        
        percentage_known = known_words / len(level_words) if level_words else 0
        
        # Level up if player knows at least 70% of words at current level
        if percentage_known >= 0.7:
            self.player.jlpt_level -= 1  # Lower number = higher level
            self.player.save()
            game_logger.info(f"Player {self.player.username} leveled up to JLPT N{self.player.jlpt_level}")
            return True
            
        return False 