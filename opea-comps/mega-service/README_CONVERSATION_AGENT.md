# Japanese Conversation Partner Agent

An intelligent agent-based system that simulates natural conversations in Japanese and provides real-time feedback to help language learners improve their Japanese communication skills.

## Features

- **Adaptive Conversations**: Adjusts complexity based on user proficiency level (beginner, intermediate, advanced)
- **Real-life Scenarios**: Practice conversations in various contexts like restaurants, shopping, asking for directions, and job interviews
- **Instant Feedback**: Receive grammar, vocabulary, and natural expression corrections
- **Voice Recognition**: Practice speaking Japanese with speech-to-text capabilities
- **Translation Mode**: Enter text in English and have it automatically translated to Japanese
- **Personalized Learning**: Tracks common mistakes and vocabulary suggestions for targeted improvement
- **Romaji Support**: For beginners, provides romanized versions of Japanese text

## Technical Overview

The Japanese Conversation Partner Agent is built using an agentic workflow architecture:

1. **Planning**: Selects appropriate scenarios and structures conversations based on proficiency level
2. **Execution**: Conducts natural dialogues through the LLM-powered conversation agent
3. **Observation**: Analyzes user inputs for grammatical errors, vocabulary usage, and natural expression
4. **Feedback**: Provides targeted corrections and suggestions for improvement
5. **Adaptation**: Adjusts complexity and topics based on user performance

## Prerequisites

- Python 3.8 or higher
- OPEA components installed
- Ollama with the llama3 model

## Installation

1. Ensure you have the required dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure the Japanese text processing libraries are installed:

```bash
pip install fugashi unidic-lite pykakasi jaconv
```

3. For speech recognition functionality, install:

```bash
pip install SpeechRecognition
```

## Usage

1. Start the Conversation Agent:

```bash
./run_conversation_agent.sh
```

2. Open your web browser and go to:

```
http://localhost:8083
```

3. Select your proficiency level and a conversation scenario
4. Begin practicing Japanese in a simulated conversation

## Features in Detail

### Proficiency Levels

- **Beginner**: Simple sentences, basic grammar, common vocabulary with romaji support
- **Intermediate**: Moderately complex sentences and grammar with some kanji
- **Advanced**: Natural, complex Japanese with a wide vocabulary range

### Conversation Scenarios

- **Restaurant**: Order food, ask about menu items, handle the bill
- **Shopping**: Ask about products, sizes, prices, and make purchases
- **Directions**: Ask for and give directions in Japanese
- **Job Interview**: Practice common interview questions and responses

### Feedback System

The agent provides detailed feedback on:

- **Grammar**: Identifies grammatical errors and provides corrections
- **Vocabulary**: Suggests more natural or appropriate vocabulary choices
- **Natural Expression**: Helps phrases sound more like native Japanese
- **Overall Assessment**: Provides general feedback on communication effectiveness

### Voice Input

Practice speaking Japanese by:

1. Clicking the microphone button
2. Speaking into your device's microphone
3. Reviewing the transcribed text
4. Using it in the conversation

## Architecture

The system consists of:

1. **Backend (FastAPI)**:
   - LLM integration for natural language understanding and generation
   - Conversation state management
   - Japanese text processing with fugashi and pykakasi
   - Speech recognition for voice input

2. **Frontend (HTML/JS)**:
   - Intuitive conversation interface
   - Real-time feedback display
   - Scenario selection
   - Proficiency level adjustment

## Advanced Configuration

The agent can be further customized by modifying:

- `PROFICIENCY_LEVELS` in the `japanese_conversation_agent.py` file to adjust difficulty parameters
- `CONVERSATION_SCENARIOS` to add new practice scenarios
- System prompts for different response styles

## Troubleshooting

- **Speech recognition not working**: Ensure your microphone permissions are enabled in your browser
- **Japanese text not displaying**: Make sure your system has Japanese font support
- **LLM connection errors**: Verify that the Ollama service is running and the llama3 model is installed

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

## Acknowledgments

- Based on the architecture of the Japanese TTS Service
- Uses Ollama for LLM capabilities
- Inspired by language learning methodologies that emphasize practical conversation practice 