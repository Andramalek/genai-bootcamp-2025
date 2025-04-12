from typing import List, Dict, Optional, Set, Tuple
import json
import random
import os
from enum import Enum
from app.utils.logger import game_logger
from app.utils.helpers import load_json_file

class VocabularyWord:
    """
    Represents a Japanese vocabulary word
    """
    def __init__(
        self,
        id: str,
        japanese: str,
        romaji: str,
        english: str,
        jlpt_level: int,
        part_of_speech: str,
        example_sentence: Optional[str] = None,
        example_translation: Optional[str] = None,
        context_categories: Optional[List[str]] = None,
        related_words: Optional[List[str]] = None,
        usage_notes: Optional[str] = None
    ):
        self.id = id
        self.japanese = japanese
        self.romaji = romaji
        self.english = english
        self.jlpt_level = jlpt_level
        self.part_of_speech = part_of_speech
        self.example_sentence = example_sentence
        self.example_translation = example_translation
        self.context_categories = context_categories or []
        self.related_words = related_words or []
        self.usage_notes = usage_notes

class VocabularyTheme:
    """
    Represents a theme for vocabulary words
    """
    def __init__(self, id: str, name: str, description: str, words: List[str]):
        self.id = id
        self.name = name
        self.description = description
        self.words = words

class VocabularyManager:
    """
    Manages Japanese vocabulary words
    """
    def __init__(self, use_db: bool = True):
        """
        Initialize the vocabulary manager
        
        Args:
            use_db: Whether to use the database (True) or file system (False)
        """
        self.use_db = use_db
        self.vocabulary = {}  # Cache for vocabulary words
        self.themes = {}      # Cache for vocabulary themes
        
        if use_db:
            self.db = Database.get_db_instance()
            self._load_vocabulary_from_db()
        else:
            self._load_vocabulary_from_files()
            
        game_logger.info(f"Vocabulary manager initialized with {len(self.vocabulary)} words and {len(self.themes)} themes")
        
    def _load_vocabulary_from_files(self):
        """
        Load vocabulary data from JSON files
        """
        from app.config import Config
        config = Config()
        
        # Load vocabulary words
        for level in range(5, 0, -1):  # N5 to N1
            file_path = os.path.join(config.VOCABULARY_DIR, f'jlpt_n{level}.json')
            if os.path.exists(file_path):
                try:
                    words = load_json_file(file_path)
                    for word_data in words:
                        word = VocabularyWord(**word_data)
                        self.vocabulary[word.id] = word
                except Exception as e:
                    game_logger.error(f"Error loading vocabulary file {file_path}: {str(e)}")
        
        # Load vocabulary themes
        themes_file = os.path.join(config.VOCABULARY_DIR, 'themes.json')
        if os.path.exists(themes_file):
            try:
                themes_data = load_json_file(themes_file)
                for theme_data in themes_data:
                    theme = VocabularyTheme(**theme_data)
                    self.themes[theme.id] = theme
            except Exception as e:
                game_logger.error(f"Error loading themes file {themes_file}: {str(e)}")
    
    def _load_vocabulary_from_db(self):
        """
        Load vocabulary data from database
        """
        try:
            # Load vocabulary words
            rows = self.db.fetch_all("SELECT * FROM vocabulary")
            for row in rows:
                word = VocabularyWord(**row)
                self.vocabulary[word.id] = word
                
            # Load vocabulary themes
            theme_rows = self.db.fetch_all("SELECT * FROM vocabulary_themes")
            for theme_row in theme_rows:
                # Get words for this theme
                word_rows = self.db.fetch_all(
                    "SELECT word_id FROM vocabulary_theme_words WHERE theme_id = ?",
                    (theme_row['id'],)
                )
                word_ids = [row['word_id'] for row in word_rows]
                
                theme = VocabularyTheme(theme_row['id'], theme_row['name'], theme_row['description'], word_ids)
                self.themes[theme.id] = theme
                
        except Exception as e:
            game_logger.error(f"Error loading vocabulary from database: {str(e)}")
            # Fall back to file-based loading if database fails
            self._load_vocabulary_from_files()
    
    def get_word_by_id(self, word_id: str) -> Optional[VocabularyWord]:
        """
        Get a vocabulary word by ID
        
        Args:
            word_id: ID of the word to get
            
        Returns:
            VocabularyWord if found, None otherwise
        """
        # Check cache first
        if word_id in self.vocabulary:
            return self.vocabulary[word_id]
            
        # If not in cache and using database, try to load from DB
        if self.use_db:
            row = self.db.fetch_one("SELECT * FROM vocabulary WHERE id = ?", (word_id,))
            if row:
                word = VocabularyWord(**row)
                self.vocabulary[word.id] = word  # Update cache
                return word
                
        return None
    
    def get_words_for_level(self, jlpt_level: int) -> List[VocabularyWord]:
        """
        Get all vocabulary words for a specific JLPT level
        
        Args:
            jlpt_level: JLPT level (5=N5, 1=N1)
            
        Returns:
            List of VocabularyWord objects for the given level
        """
        if self.use_db:
            # Query database directly
            rows = self.db.fetch_all(
                "SELECT * FROM vocabulary WHERE jlpt_level = ?",
                (jlpt_level,)
            )
            
            result = []
            for row in rows:
                word = VocabularyWord(**row)
                self.vocabulary[word.id] = word  # Update cache
                result.append(word)
                
            return result
        else:
            # Use cached data
            return [word for word in self.vocabulary.values() 
                    if word.jlpt_level == jlpt_level]
    
    def get_word_for_level(self, jlpt_level: int) -> Optional[VocabularyWord]:
        """
        Get a random vocabulary word for a specific JLPT level
        
        Args:
            jlpt_level: JLPT level (5=N5, 1=N1)
            
        Returns:
            Random VocabularyWord for the given level, or None if no words available
        """
        level_words = self.get_words_for_level(jlpt_level)
        if not level_words:
            # If no words found for the given level, try the next higher level
            if jlpt_level > 1:
                return self.get_word_for_level(jlpt_level - 1)
            return None
            
        return random.choice(level_words)
    
    def get_translation(self, japanese_word: str) -> Optional[VocabularyWord]:
        """
        Get translation for a Japanese word
        
        Args:
            japanese_word: Japanese word to translate
            
        Returns:
            VocabularyWord if found, None otherwise
        """
        if self.use_db:
            row = self.db.fetch_one(
                "SELECT * FROM vocabulary WHERE japanese = ?", 
                (japanese_word,)
            )
            
            if row:
                word = VocabularyWord(**row)
                self.vocabulary[word.id] = word  # Update cache
                return word
        else:
            for word in self.vocabulary.values():
                if word.japanese == japanese_word:
                    return word
                    
        return None
    
    def search_word(self, search_term: str) -> List[VocabularyWord]:
        """
        Search for words by Japanese, romaji, or English
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of matching VocabularyWord objects
        """
        search_term_lower = search_term.lower()
        
        if self.use_db:
            # Use LIKE for simple partial matching
            rows = self.db.fetch_all(
                """
                SELECT * FROM vocabulary 
                WHERE japanese LIKE ? OR romaji LIKE ? OR english LIKE ?
                """, 
                (f"%{search_term}%", f"%{search_term_lower}%", f"%{search_term_lower}%")
            )
            
            result = []
            for row in rows:
                word = VocabularyWord(**row)
                self.vocabulary[word.id] = word  # Update cache
                result.append(word)
                
            return result
        else:
            # Search in cache
            results = []
            for word in self.vocabulary.values():
                if (search_term in word.japanese or 
                    search_term_lower in word.romaji.lower() or 
                    search_term_lower in word.english.lower()):
                    results.append(word)
                    
            return results
    
    def get_words_by_theme(self, theme_id: str) -> List[VocabularyWord]:
        """
        Get all vocabulary words for a specific theme
        
        Args:
            theme_id: ID of the theme
            
        Returns:
            List of VocabularyWord objects for the given theme
        """
        if theme_id not in self.themes:
            if self.use_db:
                # Try to load theme from database
                theme_row = self.db.fetch_one(
                    "SELECT * FROM vocabulary_themes WHERE id = ?", 
                    (theme_id,)
                )
                
                if not theme_row:
                    return []
                    
                # Get words for this theme
                word_rows = self.db.fetch_all(
                    "SELECT word_id FROM vocabulary_theme_words WHERE theme_id = ?",
                    (theme_id,)
                )
                word_ids = [row['word_id'] for row in word_rows]
                
                theme = VocabularyTheme(theme_row['id'], theme_row['name'], theme_row['description'], word_ids)
                self.themes[theme.id] = theme
            else:
                return []
        
        # Now we should have the theme in cache
        theme = self.themes[theme_id]
        return [self.get_word_by_id(word_id) for word_id in theme.words 
                if self.get_word_by_id(word_id) is not None]
    
    def get_all_themes(self) -> List[VocabularyTheme]:
        """
        Get all vocabulary themes
        
        Returns:
            List of VocabularyTheme objects
        """
        if not self.themes and self.use_db:
            # Load themes from database
            theme_rows = self.db.fetch_all("SELECT * FROM vocabulary_themes")
            for theme_row in theme_rows:
                # Get words for this theme
                word_rows = self.db.fetch_all(
                    "SELECT word_id FROM vocabulary_theme_words WHERE theme_id = ?",
                    (theme_row['id'],)
                )
                word_ids = [row['word_id'] for row in word_rows]
                
                theme = VocabularyTheme(theme_row['id'], theme_row['name'], theme_row['description'], word_ids)
                self.themes[theme.id] = theme
                
        return list(self.themes.values())
    
    def get_theme_by_id(self, theme_id: str) -> Optional[VocabularyTheme]:
        """
        Get a vocabulary theme by ID
        
        Args:
            theme_id: ID of the theme to get
            
        Returns:
            VocabularyTheme if found, None otherwise
        """
        if theme_id in self.themes:
            return self.themes[theme_id]
            
        if self.use_db:
            # Try to load theme from database
            theme_row = self.db.fetch_one(
                "SELECT * FROM vocabulary_themes WHERE id = ?", 
                (theme_id,)
            )
            
            if not theme_row:
                return None
                
            # Get words for this theme
            word_rows = self.db.fetch_all(
                "SELECT word_id FROM vocabulary_theme_words WHERE theme_id = ?",
                (theme_id,)
            )
            word_ids = [row['word_id'] for row in word_rows]
            
            theme = VocabularyTheme(theme_row['id'], theme_row['name'], theme_row['description'], word_ids)
            self.themes[theme.id] = theme
            return theme
            
        return None
    
    def get_related_words(self, word_id: str) -> List[VocabularyWord]:
        """
        Get related words for a vocabulary word
        
        Args:
            word_id: ID of the word
            
        Returns:
            List of related VocabularyWord objects
        """
        word = self.get_word_by_id(word_id)
        if not word or not word.related_words:
            return []
            
        return [self.get_word_by_id(related_id) for related_id in word.related_words 
                if self.get_word_by_id(related_id) is not None]
    
    def get_words_by_part_of_speech(self, part_of_speech: str, jlpt_level: int = None) -> List[VocabularyWord]:
        """
        Get vocabulary words by part of speech
        
        Args:
            part_of_speech: Part of speech (e.g., "noun", "verb")
            jlpt_level: Optional JLPT level filter
            
        Returns:
            List of matching VocabularyWord objects
        """
        if self.use_db:
            if jlpt_level is not None:
                rows = self.db.fetch_all(
                    "SELECT * FROM vocabulary WHERE part_of_speech = ? AND jlpt_level = ?",
                    (part_of_speech, jlpt_level)
                )
            else:
                rows = self.db.fetch_all(
                    "SELECT * FROM vocabulary WHERE part_of_speech = ?",
                    (part_of_speech,)
                )
                
            result = []
            for row in rows:
                word = VocabularyWord(**row)
                self.vocabulary[word.id] = word  # Update cache
                result.append(word)
                
            return result
        else:
            # Filter cached words
            if jlpt_level is not None:
                return [word for word in self.vocabulary.values() 
                        if word.part_of_speech == part_of_speech and word.jlpt_level == jlpt_level]
            else:
                return [word for word in self.vocabulary.values() 
                        if word.part_of_speech == part_of_speech]
    
    def get_words_by_context_category(self, category: str, jlpt_level: int = None) -> List[VocabularyWord]:
        """
        Get vocabulary words by context category
        
        Args:
            category: Context category (e.g., "food", "travel")
            jlpt_level: Optional JLPT level filter
            
        Returns:
            List of matching VocabularyWord objects
        """
        result = []
        
        # This is more complex with SQLite due to JSON handling
        # For simplicity, we'll load and filter in memory
        for word in self.vocabulary.values():
            if word.context_categories and category in word.context_categories:
                if jlpt_level is None or word.jlpt_level == jlpt_level:
                    result.append(word)
                    
        # If cache is empty and we're using DB, load everything first
        if not self.vocabulary and self.use_db:
            if jlpt_level is not None:
                rows = self.db.fetch_all(
                    "SELECT * FROM vocabulary WHERE jlpt_level = ?",
                    (jlpt_level,)
                )
            else:
                rows = self.db.fetch_all("SELECT * FROM vocabulary")
                
            for row in rows:
                word = VocabularyWord(**row)
                self.vocabulary[word.id] = word
                if word.context_categories and category in word.context_categories:
                    result.append(word)
                    
        return result
    
    async def generate_contextual_example(self, word_id: str, location_setting: str) -> Dict:
        """
        Generate a contextual example for a vocabulary word based on location
        
        Args:
            word_id: ID of the vocabulary word
            location_setting: Setting of the current location (e.g., "temple", "market")
            
        Returns:
            Dict with example sentence, translation, and notes
        """
        from app.ai.openai_client import OpenAIClient
        from app.config import Config
        
        word = self.get_word_by_id(word_id)
        if not word:
            return None
            
        config = Config()
        ai_client = OpenAIClient(config.OPENAI_API_KEY)
        
        # Build prompt for LLM
        prompt = f"Create a natural Japanese example sentence using the word '{word.japanese}' ({word.english}) "
        prompt += f"in the context of a {location_setting}. The sentence should be appropriate for JLPT N{word.jlpt_level} level. "
        prompt += f"Include the translation and a brief usage note. Format your response as:\n\n"
        prompt += "Japanese: [sentence in Japanese]\nRomaji: [sentence in romaji]\nTranslation: [English translation]\nUsage note: [brief note about grammar or usage]"
        
        # Get response from OpenAI
        response_text = await ai_client.generate_text(prompt)
        
        # Parse response
        lines = response_text.strip().split('\n')
        result = {
            "japanese": word.japanese,
            "example": "",
            "romaji": "",
            "translation": "",
            "notes": ""
        }
        
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                value = value.strip()
                
                if "japanese" in key.lower():
                    result["example"] = value
                elif "romaji" in key.lower():
                    result["romaji"] = value
                elif "translation" in key.lower():
                    result["translation"] = value
                elif "usage" in key.lower() or "note" in key.lower():
                    result["notes"] = value
                    
        return result 