# Japanese Language Learning TTS Service

This service uses Google Text-to-Speech (gTTS) with a local pyttsx3 fallback to provide text-to-speech capabilities specifically designed for English speakers learning Japanese. It integrates with Ollama's LLM service for translation and example generation.

## Features

- **Japanese Text-to-Speech**: Convert Japanese text to natural-sounding speech
- **English-to-Japanese Translation**: Translate English phrases to Japanese and get audio output
- **Learning Mode**: Get word-by-word breakdown with pronunciation guides and slower speech
- **Example Generator**: Generate contextual examples with a given Japanese word or phrase
- **Offline Fallback**: Falls back to local pyttsx3 TTS when internet is unavailable

## Prerequisites

- Python 3.8+
- Docker (for running Ollama LLM service)
- OPEA framework
- gTTS, pyttsx3 and Japanese text processing libraries

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Ollama Service

Make sure the Ollama service is running in Docker:

```bash
docker compose -f /home/andramalek/projects/clone/gen-ai-bootcamp-2025/opea-comps/docker-compose.yml up -d
```

### 3. Pull a Language Model

You'll need to pull an LLM model for translation and example generation:

```bash
curl -X POST http://localhost:9000/api/pull -d '{"name": "phi"}'
# OR any other model you prefer
```

### 4. Start the Japanese TTS Service

```bash
cd /home/andramalek/projects/clone/gen-ai-bootcamp-2025/opea-comps/mega-service
/home/andramalek/projects/clone/gen-ai-bootcamp-2025/path/to/venv/bin/python japanese_tts_service.py
```

## API Endpoints

### 1. Basic Japanese TTS

Convert Japanese text to speech.

```bash
curl -X POST http://localhost:8082/v1/japanese_tts \
-H "Content-Type: application/json" \
-d '{
    "text": "こんにちは、元気ですか?"
}' --output japanese_speech.mp3
```

### 2. Translate and Speak

Translate English to Japanese and get audio output.

```bash
curl -X POST http://localhost:8082/v1/translate_and_speak \
-H "Content-Type: application/json" \
-d '{
    "text": "Hello, how are you today?",
    "include_details": true,
    "model": "phi"
}' --output translated_speech.mp3
```

### 3. Learning Mode

Get detailed breakdown of Japanese text with pronunciation guides.

```bash
curl -X POST http://localhost:8082/v1/learning_mode \
-H "Content-Type: application/json" \
-d '{
    "text": "東京に行きたいです",
    "is_english": false
}' --output learning.mp3
```

Alternatively, start with English:

```bash
curl -X POST http://localhost:8082/v1/learning_mode \
-H "Content-Type: application/json" \
-d '{
    "text": "I want to go to Tokyo",
    "is_english": true,
    "model": "phi"
}' --output learning_english.mp3
```

### 4. Example Generator

Generate example sentences with a given Japanese word.

```bash
curl -X POST http://localhost:8082/v1/example_generator \
-H "Content-Type: application/json" \
-d '{
    "keyword": "食べる",
    "count": 3,
    "model": "phi",
    "generate_audio": false
}'
```

## Technical Details

### Architecture

This service integrates several components:

1. **OPEA Framework**: For service orchestration and API management
2. **Google Text-to-Speech (gTTS)**: Primary TTS engine for high-quality Japanese speech
3. **pyttsx3**: Offline fallback TTS engine for when internet is unavailable
4. **Ollama LLM Service**: For translation and content generation
5. **Japanese Text Processing**: Using libraries like fugashi, pykakasi, and jaconv

### Japanese Language Support

The service includes special handling for Japanese text:

- Word segmentation with fugashi
- Furigana generation with pykakasi
- Romaji conversion with pykakasi + jaconv
- Slower speech option for learning mode

## TTS Implementation

### Primary: Google TTS (gTTS)
- High-quality speech synthesis
- Excellent Japanese language support
- Requires internet connection

### Fallback: pyttsx3
- Works completely offline
- Lower quality for Japanese
- Automatically used when gTTS fails

## Limitations

- **Internet Dependency**: Primary TTS requires internet connection
- **Fallback Quality**: Offline fallback has lower quality for Japanese
- **Rate Limiting**: gTTS may be subject to Google's rate limits
- **Example generation quality**: Depends on the LLM's understanding of Japanese

## Future Improvements

- Add caching for frequently requested phrases
- Improve offline TTS quality for Japanese
- Vocabulary tracking for personalized learning
- Integration with a Japanese dictionary API
- Downloadable content for offline learning 