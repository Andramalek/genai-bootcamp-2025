# Japanese Learning MUD Game

A text-based MUD (Multi-User Dungeon) game for learning Japanese vocabulary and grammar in context.

## Features

- Explore a virtual Japanese world with locations like temples, markets, and train stations
- Interact with NPCs using Japanese vocabulary
- Collect and use items that teach you new words
- Vocabulary tracking system that follows your progress with each word
- Themed vocabulary sets organized by context categories (food, transportation, etc.)
- JLPT level-based vocabulary progression (N5 to N1)
- AI-generated contextual examples for vocabulary words
- Image generation for locations to enhance immersion
- Web interface for browser-based gameplay

## Technologies Used

- Python 3.8+
- SQLite database for data persistence
- Flask and WebSockets for the web interface
- OpenAI API for text and image generation
- Terminal-based user interface with rich text formatting

## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables (create a `.env` file in the project root):
   ```
   OPENAI_API_KEY=your_openai_api_key
   USE_DATABASE=True
   ```
4. Initialize the database:
   ```
   python -m app.utils.db_migration --import-data
   ```
5. Run the game (choose one):
   
   a. Terminal interface:
   ```
   python -m app.main
   ```
   
   b. Web interface:
   ```
   python -m app.web.app
   ```
   Then open http://localhost:5000 in your browser

## Web Interface

The game features a browser-based interface that allows you to play the MUD game in a web browser. The web interface provides:

1. **Modern UI**: A clean, responsive interface with proper formatting for Japanese text
2. **Command History**: Use up/down arrows to navigate through previous commands
3. **Real-time Updates**: Immediate responses via WebSocket technology
4. **Syntax Highlighting**: Colorful display of Japanese words, locations, items, and NPCs
5. **Command Help**: Quick reference for available commands

To run the web interface:
```
python -m app.web.app
```

Then visit http://localhost:5000 in your web browser.

## Database System

The game uses SQLite for data persistence, with the following benefits:

- Efficient storage and retrieval of vocabulary words, themes, and player progress
- Relational structure for vocabulary categorization and relationships
- Transaction support for data integrity
- Automatic rollback to file-based storage if database operations fail

### Database Schema

- `vocabulary`: Stores all vocabulary words with their properties
- `vocabulary_themes`: Defines vocabulary themes like "food", "travel", etc.
- `vocabulary_theme_words`: Junction table linking themes to words
- `players`: Stores player information and progress
- `player_vocabulary`: Tracks player knowledge of each vocabulary word
- `locations`, `items`, `npcs`: Game world entities

### Database Management

To manage the database, use the migration script:

```
# Initialize database and import data
python -m app.utils.db_migration --import-data

# Reset database (caution: deletes all data)
python -m app.utils.db_migration --reset --import-data

# Check database status
python -m app.utils.db_migration --check --verbose
```

## Vocabulary System

The vocabulary system is organized into:

1. **JLPT Levels**: Words are categorized by Japanese Language Proficiency Test levels (N5 to N1)
2. **Themes**: Words are grouped into contextual themes like "Food and Drink", "Transportation", etc.
3. **Knowledge Tracking**: The system tracks your familiarity with each word through six levels:
   - Unknown: Not seen yet
   - Seen: Encountered but not tested
   - Learning: Correctly answered 1-2 times
   - Familiar: Correctly answered 3-5 times
   - Known: Correctly answered 6-9 times
   - Mastered: Correctly answered 10+ times

### Vocabulary Commands

- `themes`: List all vocabulary themes and your progress in each
- `theme <name>`: Focus on learning words from a specific theme
- `learn <word>`: Practice a specific Japanese word
- `review`: Test your knowledge of previously seen words
- `stats`: Show your vocabulary learning statistics

## Game Commands

- `look`: Describe your current location
- `go <direction>`: Move in a direction
- `examine <object>`: Look at something in detail
- `take <item>`: Pick up an item
- `drop <item>`: Drop an item
- `inventory`: List items you're carrying
- `talk <npc>`: Talk to an NPC
- `translate <word>`: Translate a Japanese word to English
- `help`: Show available commands
- `quit`: Exit the game

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 