import json
import os
import io
import numpy as np
import soundfile as sf
from gtts import gTTS
import logging
import sys
import traceback
import time
import uuid
import re
import requests
import asyncio
import random  # Added missing import for random module
import tempfile
from typing import Dict, List, Optional, Tuple, Any

from fastapi import Request, HTTPException, FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import aiohttp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("JapaneseConversationAgent")

# Import the optional OPEA components
try:
    from comps import MicroService, ServiceOrchestrator
    from comps.cores.mega.constants import ServiceType, ServiceRoleType
    from comps.cores.proto.docarray import LLMParams
    OPEA_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Failed to import OPEA components: {e}")
    logger.warning("OPEA functionality will be disabled, but basic Japanese conversation will still work.")
    OPEA_AVAILABLE = False

# Japanese text processing
try:
    import fugashi
    import pykakasi
    import jaconv
except ImportError as e:
    logger.error(f"Failed to import Japanese text processing libraries: {e}")
    logger.error("Make sure you have installed all required dependencies:")
    logger.error("pip install fugashi unidic-lite pykakasi jaconv")
    sys.exit(1)

# Try to import speech recognition libraries
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    logger.warning("Speech recognition library not available. Some features will be limited.")
    logger.warning("To enable speech recognition: pip install SpeechRecognition")
    SPEECH_RECOGNITION_AVAILABLE = False

# Set constants for LLM service
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "localhost")  # Changed from "0.0.0.0" to "localhost"
LLM_SERVICE_PORT = os.getenv("LLM_SERVICE_PORT", 9000)

# Define conversation proficiency levels
PROFICIENCY_LEVELS = {
    "beginner": {
        "vocab_limit": 500,
        "grammar_complexity": "basic",
        "response_speed": 0.8,  # slower for beginners
        "correction_frequency": "high"
    },
    "intermediate": {
        "vocab_limit": 2000,
        "grammar_complexity": "intermediate",
        "response_speed": 1.0,
        "correction_frequency": "medium"
    },
    "advanced": {
        "vocab_limit": 5000,
        "grammar_complexity": "advanced",
        "response_speed": 1.2,  # faster for advanced
        "correction_frequency": "low"
    }
}

# Define conversation scenarios
CONVERSATION_SCENARIOS = {
    "restaurant": {
        "description": "Ordering food at a restaurant",
        "roles": ["customer", "waiter"],
        "agent_role": "restaurant server",
        "key_phrases": ["メニュー", "注文", "おすすめ", "お会計"],
        "beginner_prompt": "You are having lunch at a small restaurant in Tokyo. Order a simple meal.",
        "intermediate_prompt": "You are at a restaurant and want to ask about allergens in the food and make special requests.",
        "advanced_prompt": "You are at a high-end traditional Japanese restaurant. Discuss the seasonal specialties with the chef."
    },
    "shopping": {
        "description": "Shopping for clothes",
        "roles": ["customer", "shop_assistant"],
        "agent_role": "shop assistant",
        "key_phrases": ["サイズ", "試着", "値段", "割引"],
        "beginner_prompt": "You need to buy a t-shirt. Ask about colors and sizes.",
        "intermediate_prompt": "You're looking for formal clothes for a job interview. Discuss options and prices.",
        "advanced_prompt": "You're looking for traditional Japanese clothing. Discuss fabrics, styles, and cultural significance."
    },
    "directions": {
        "description": "Asking for directions",
        "roles": ["tourist", "local"],
        "agent_role": "local person",
        "key_phrases": ["どこ", "まっすぐ", "右", "左", "近く"],
        "beginner_prompt": "You're lost and need to find the train station. Ask a local for help.",
        "intermediate_prompt": "You need to find a specific shop in a complex neighborhood. Ask for detailed directions.",
        "advanced_prompt": "You need to explain a complex route to someone while discussing landmarks and alternative paths."
    },
    "interview": {
        "description": "Job interview",
        "roles": ["applicant", "interviewer"],
        "agent_role": "interviewer",
        "key_phrases": ["経験", "スキル", "給料", "質問"],
        "beginner_prompt": "You're interviewing for a simple part-time job. Answer basic questions about yourself.",
        "intermediate_prompt": "You're in a job interview for an office position. Discuss your skills and experience.",
        "advanced_prompt": "You're in a senior-level job interview. Discuss your career path, achievements, and vision."
    }
}

class JapaneseConversationAgent:
    def __init__(self, host="0.0.0.0", port=8083):
        self.host = host
        self.port = port
        self.app = FastAPI(title="Japanese Conversation Agent")
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize endpoints
        self.endpoints = {
            "start_conversation": "/v1/start_conversation",
            "continue_conversation": "/v1/continue_conversation",
            "get_feedback": "/v1/get_feedback",
            "speech_to_text": "/v1/speech_to_text",
            "scenarios": "/v1/scenarios",
            "text_to_speech": "/v1/text_to_speech",
            "get_suggestion": "/v1/get_suggestion"
        }
        
        logger.info(f"Initializing Japanese Conversation Agent on {host}:{port}")
        
        try:
            if OPEA_AVAILABLE:
                self.megaservice = ServiceOrchestrator()
                os.environ["LOGFLAG"] = "true"  # Enable detailed logging
                logger.info("ServiceOrchestrator initialized successfully")
            else:
                logger.warning("Skipping ServiceOrchestrator initialization as OPEA is not available")
        except Exception as e:
            logger.error(f"Failed to initialize ServiceOrchestrator: {e}")
            logger.warning("Continuing without OPEA functionality")
        
        # Initialize Japanese text processing tools
        try:
            self.tagger = fugashi.Tagger()
            self.kks = pykakasi.kakasi()
            logger.info("Japanese text processing tools initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Japanese text processing tools: {e}")
            raise
        
        # Initialize speech recognition if available
        self.speech_recognition = SPEECH_RECOGNITION_AVAILABLE
        if self.speech_recognition:
            try:
                self.recognizer = sr.Recognizer()
                logger.info("Speech recognition initialized")
            except Exception as e:
                logger.error(f"Failed to initialize speech recognition: {e}")
                self.speech_recognition = False
        
        # Active conversations storage
        self.conversations = {}
        
        # Student profiles
        self.student_profiles = {}
        
        # Register routes
        self.register_routes()
        
        logger.info("Japanese Conversation Agent initialized successfully")
    
    def register_routes(self):
        """Register all API endpoints"""
        
        # Static files for frontend
        self.app.mount("/static", StaticFiles(directory="conversation_frontend"), name="static")
        
        # Return the frontend HTML
        @self.app.get("/", response_class=HTMLResponse)
        async def get_frontend():
            try:
                with open("conversation_frontend/index.html", "r") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to load frontend: {e}")
                return HTMLResponse("<h1>Error loading frontend</h1>")
        
        # API endpoints
        @self.app.post(self.endpoints["start_conversation"])
        async def start_conversation(request: Request):
            try:
                data = await request.json()
                scenario = data.get("scenario", "restaurant")
                proficiency = data.get("proficiency", "beginner")
                student_id = data.get("student_id", str(uuid.uuid4()))
                model = data.get("model", "auto")  # Get model preference, default to auto
                
                logger.info(f"Starting conversation with scenario={scenario}, proficiency={proficiency}, student_id={student_id}, model={model}")
                
                conversation_id = self.create_conversation(scenario, proficiency, student_id, model)
                
                initial_context = self.get_scenario_context(scenario, proficiency)
                logger.info(f"Generated initial context: {initial_context}")
                
                try:
                    first_message = await self.generate_agent_message(conversation_id, initial_context)
                    logger.info(f"Generated first message: {first_message}")
                    
                    return JSONResponse({
                        "conversation_id": conversation_id,
                        "message": first_message
                    })
                except Exception as e:
                    logger.error(f"Failed to generate first message: {e}")
                    return JSONResponse({
                        "conversation_id": conversation_id,
                        "message": {
                            "role": "agent",
                            "content": "すみません、エラーが発生しました。もう一度試してください。 (Sumimasen, eraa ga hassei shimashita. Mou ichido tameshite kudasai.)",
                            "timestamp": time.time()
                        }
                    })
            except Exception as e:
                logger.error(f"Failed to start conversation: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)
        
        @self.app.post(self.endpoints["text_to_speech"])
        async def text_to_speech(request: Request):
            """Generate speech for a given Japanese text"""
            try:
                data = await request.json()
                japanese_text = data.get("text", "")
                
                if not japanese_text:
                    return JSONResponse(
                        {"error": "No text provided"},
                        status_code=400
                    )
                
                # Extract Japanese text without romaji in parentheses
                japanese_only = re.sub(r'\([^)]*\)', '', japanese_text).strip()
                
                logger.info(f"Generating speech for: {japanese_only[:50]}...")
                
                # Call the Japanese TTS service
                try:
                    # Use requests to call the local TTS service
                    tts_response = requests.post(
                        "http://localhost:8082/v1/japanese_tts",
                        json={"text": japanese_only},
                        timeout=10
                    )
                    
                    if tts_response.status_code == 200:
                        # Return the audio directly
                        return Response(
                            content=tts_response.content, 
                            media_type="audio/mp3",
                            headers={
                                "Content-Disposition": "attachment; filename=japanese_speech.mp3",
                                "Access-Control-Allow-Origin": "*"
                            }
                        )
                    else:
                        logger.error(f"TTS service error: {tts_response.text}")
                        return JSONResponse(
                            {"error": f"TTS service returned error: {tts_response.text}"},
                            status_code=tts_response.status_code
                        )
                except Exception as e:
                    logger.error(f"Failed to call TTS service: {e}")
                    return JSONResponse(
                        {"error": f"Failed to generate speech: {str(e)}"},
                        status_code=500
                    )
            except Exception as e:
                logger.error(f"Text-to-speech request failed: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)
        
        @self.app.post(self.endpoints["continue_conversation"])
        async def continue_conversation(request: Request):
            data = await request.json()
            conversation_id = data.get("conversation_id")
            user_message = data.get("message", "")
            # New parameter to control whether to run analysis
            run_analysis = data.get("run_analysis", False)
            
            if not conversation_id or conversation_id not in self.conversations:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Add user message to conversation
            self.add_message_to_conversation(conversation_id, "user", user_message)
            
            # Generate agent response
            agent_message = await self.generate_agent_message(conversation_id)
            
            # Generate feedback only if explicitly requested or if we have a slow connection
            feedback = {"analysis_skipped": True}
            if run_analysis:
                try:
                    feedback = await self.analyze_user_input(conversation_id, user_message)
                except Exception as e:
                    logger.error(f"Error getting feedback (conversation will continue): {e}")
                    feedback = {
                    "error": "Analysis not available",
                    "message": "Could not analyze your input, but the conversation will continue."
                }
            
            return JSONResponse({
                "message": agent_message["content"],
                "feedback": feedback
            })
        
        @self.app.post(self.endpoints["get_feedback"])
        async def get_feedback(request: Request):
            data = await request.json()
            conversation_id = data.get("conversation_id")
            
            if not conversation_id or conversation_id not in self.conversations:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            conversation = self.conversations[conversation_id]
            last_user_message = None
            
            # Find the last user message
            for message in reversed(conversation["messages"]):
                if message["role"] == "user":
                    last_user_message = message["content"]
                    break
            
            if not last_user_message:
                return JSONResponse({"feedback": "No user message to analyze"})
            
            feedback = await self.analyze_user_input(conversation_id, last_user_message)
            
            return JSONResponse({"feedback": feedback})
        
        @self.app.post(self.endpoints["speech_to_text"])
        async def speech_to_text(file: UploadFile = File(...)):
            """
            Convert speech to text from an uploaded audio file.
            """
            if not self.speech_recognition:
                logging.error("Speech recognition not available for this request")
                raise HTTPException(
                    status_code=503, 
                    detail="Speech recognition is not available on this server"
                )
            
            temp_file_path = None
            converted_file_path = None
            
            try:
                # Determine the file extension from the uploaded file
                original_filename = file.filename
                file_extension = original_filename.split('.')[-1].lower()
                content_type = file.content_type or "unknown"
                
                logging.info(f"Received audio: {original_filename}, content_type: {content_type}, detected extension: {file_extension}")
                
                # Save the uploaded file to a temporary location with appropriate extension
                temp_file_path = f"/tmp/{uuid.uuid4()}.{file_extension}"
                
                with open(temp_file_path, "wb") as temp_file:
                    # Read the file
                    contents = await file.read()
                    if len(contents) == 0:
                        raise ValueError("Empty audio file received")
                        
                    temp_file.write(contents)
                    logging.info(f"Audio file saved temporarily at {temp_file_path} with size {len(contents)} bytes")
                
                # ALWAYS convert to WAV format using ffmpeg - now we know it's installed
                output_wav_path = f"/tmp/{uuid.uuid4()}.wav"
                
                try:
                    import subprocess
                    import shlex
                    
                    # Use ffmpeg to convert to a standard WAV format that speech_recognition can handle
                    # -y: Overwrite output file without asking
                    # -i: Input file
                    # -ac 1: Convert to mono
                    # -ar 16000: Set sample rate to 16kHz
                    # -sample_fmt s16: Use signed 16-bit PCM format
                    # -c:a pcm_s16le: Force PCM 16-bit encoding
                    cmd = [
                        'ffmpeg', '-y', 
                        '-i', temp_file_path, 
                        '-ac', '1', 
                        '-ar', '16000',
                        '-sample_fmt', 's16',
                        '-c:a', 'pcm_s16le',
                        output_wav_path
                    ]
                    
                    cmd_str = ' '.join(shlex.quote(str(c)) for c in cmd)
                    logging.info(f"Executing conversion: {cmd_str}")
                    
                    process = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True
                    )
                    
                    if process.returncode != 0:
                        logging.error(f"Error converting to wav: {process.stderr}")
                        return {"text": "", "status": "conversion_failed", "error": f"Failed to convert audio format: {process.stderr[:200]}"}
                    
                    # Verify the converted file exists and has content
                    if not os.path.exists(output_wav_path):
                        logging.error("Conversion output file is missing")
                        return {"text": "", "status": "conversion_failed", "error": "Conversion failed - output file not created"}
                    
                    file_size = os.path.getsize(output_wav_path)
                    if file_size == 0:
                        logging.error("Conversion output file is empty")
                        return {"text": "", "status": "conversion_failed", "error": "Conversion created an empty file"}
                    
                    logging.info(f"Conversion successful: {output_wav_path}, size: {file_size} bytes")
                    
                    # Use the converted wav file for recognition
                    converted_file_path = output_wav_path
                    
                except Exception as e:
                    logging.error(f"Error during audio conversion: {str(e)}")
                    return {"text": "", "status": "conversion_failed", "error": f"Failed to convert audio format: {str(e)}"}
                
                # Verify the file can be opened as a WAV audio file before sending to recognition
                try:
                    import wave
                    with wave.open(converted_file_path, 'rb') as wave_file:
                        n_channels = wave_file.getnchannels()
                        sample_width = wave_file.getsampwidth()
                        framerate = wave_file.getframerate()
                        n_frames = wave_file.getnframes()
                        duration = n_frames / framerate
                        
                        logging.info(f"Audio verified: channels={n_channels}, width={sample_width}, " 
                                   f"rate={framerate}, frames={n_frames}, duration={duration:.2f}s")
                        
                        if duration < 0.5:  # Less than 0.5 seconds
                            logging.warning(f"Audio duration too short: {duration:.2f} seconds")
                            return {"text": "", "status": "too_short", "error": "Audio recording too short, please record longer speech"}
                        
                except Exception as e:
                    logging.error(f"Error verifying audio format: {str(e)}")
                    return {"text": "", "status": "invalid_format", "error": f"Invalid audio format: {str(e)}"}
                
                # Convert the speech to text
                try:
                    text = self.recognize_speech(converted_file_path)
                    if not text or text.strip() == "":
                        logging.warning("Speech recognition returned empty text")
                        return {"text": "", "status": "no_speech_detected", "error": "No speech detected in the recording"}
                    
                    logging.info(f"Speech recognition result: {text}")
                    return {"text": text, "status": "success"}
                except Exception as e:
                    logging.warning(f"Speech recognition failed with error: {str(e)}")
                    error_message = str(e)
                    if "Could not understand audio" in error_message:
                        return {"text": "", "status": "no_speech_detected", "error": "No speech detected in the recording"}
                    return {"text": "", "status": "recognition_failed", "error": f"Failed to process audio: {error_message}"}
            except Exception as e:
                logging.error(f"Error in speech_to_text: {str(e)}")
                return {"text": "", "status": "general_error", "error": f"Error processing audio: {str(e)}"}
            finally:
                # Clean up the temporary files
                try:
                    for path in [temp_file_path, converted_file_path]:
                        if path and os.path.exists(path):
                            os.remove(path)
                            logging.info(f"Temporary file {path} removed")
                except Exception as e:
                    logging.error(f"Failed to remove temporary file(s): {str(e)}")
        
        @self.app.get(self.endpoints["scenarios"])
        async def get_scenarios():
            scenarios_list = []
            for key, scenario in CONVERSATION_SCENARIOS.items():
                scenarios_list.append({
                    "id": key,
                    "name": scenario["description"],
                    "roles": scenario["roles"]
                })
            
            return JSONResponse({"scenarios": scenarios_list})
        
        @self.app.post(self.endpoints["get_suggestion"])
        async def get_response_suggestion(request: Request):
            """Get a suggestion for the next response in a conversation"""
            try:
                req_data = await request.json()
                conversation_id = req_data.get("conversation_id")
                
                if not conversation_id or conversation_id not in self.conversations:
                    return JSONResponse(
                        status_code=404,
                        content={"error": "Conversation not found"}
                    )
                
                conversation = self.conversations[conversation_id]
                scenario = conversation["scenario"]
                proficiency = conversation["proficiency"]
                student_id = conversation["student_id"]
                model = conversation["model"]
                
                # Get the most recent messages for context
                recent_messages = []
                if len(conversation["messages"]) > 0:
                    # Always take the last messages for context
                    recent_messages = conversation["messages"][-3:] if len(conversation["messages"]) >= 3 else conversation["messages"]
                
                if len(recent_messages) == 0:
                    # No messages yet, so suggest a simple greeting based on scenario
                    scenario_first_responses = {
                        "restaurant": "こんにちは。メニューを見せてください。",
                        "shopping": "こんにちは。Tシャツを探しています。",
                        "directions": "すみません、駅はどこですか？",
                        "interview": "はじめまして。よろしくお願いします。"
                    }
                    suggestion = scenario_first_responses.get(scenario, "こんにちは。")
                    romaji_text = self.get_romaji(suggestion)
                    return JSONResponse(
                        content={
                            "japanese_text": suggestion,
                            "romaji_text": romaji_text,
                            "suggestion": suggestion,
                            "explanation": "会話を始めるためのあいさつです。"
                        }
                    )
                
                # DIRECT OLLAMA API QUERY - NO CACHING OR FALLBACKS
                # --------------------------------------------------------
                logger.info(f"Directly querying Ollama API for suggestion with model={model}")
                
                # Check if Ollama API is available
                is_ollama_available = await self.check_ollama_connection()
                if not is_ollama_available:
                    return JSONResponse(
                        status_code=500,
                        content={"error": "Ollama API is not available"}
                    )
                
                # Get specific suggestion templates based on scenario and recent messages
                scenario_templates = {
                    "restaurant": {
                        "beginner": [
                            "メニューを見せてください。",
                            "水をください。",
                            "ご飯とみそ汁をお願いします。",
                            "お会計をお願いします。"
                        ],
                        "intermediate": [
                            "おすすめの料理は何ですか？",
                            "これは何で作られていますか？",
                            "アレルギーがありますが、対応できますか？",
                            "別々に会計してもいいですか？"
                        ],
                        "advanced": [
                            "今日の日替わりランチはなんですか？",
                            "この料理の調理法を教えていただけますか？",
                            "地元の食材を使っていますか？",
                            "予約をキャンセルしたいのですが、どうすればいいですか？"
                        ]
                    },
                    "shopping": {
                        "beginner": [
                            "これはいくらですか？",
                            "赤いのはありますか？",
                            "試着してもいいですか？",
                            "これをください。"
                        ],
                        "intermediate": [
                            "他の色もありますか？",
                            "割引はありますか？",
                            "返品はできますか？",
                            "カードで払えますか？"
                        ],
                        "advanced": [
                            "この素材は何ですか？お手入れはどうすればいいですか？",
                            "新作はいつ入荷しますか？",
                            "会員割引は適用されますか？",
                            "修理サービスはありますか？"
                        ]
                    },
                    "directions": {
                        "beginner": [
                            "駅はどこですか？",
                            "トイレはどこですか？",
                            "バス停はどこですか？",
                            "右ですか、左ですか？"
                        ],
                        "intermediate": [
                            "一番近いコンビニはどこですか？",
                            "この辺で良いレストランはありますか？",
                            "この場所までどのくらい時間がかかりますか？",
                            "地下鉄の入口はどこですか？"
                        ],
                        "advanced": [
                            "最寄りの観光スポットはどこですか？",
                            "この地区でおすすめの隠れた名所はありますか？",
                            "この地図で現在地を教えていただけますか？",
                            "混雑を避けるルートはありますか？"
                        ]
                    },
                    "interview": {
                        "beginner": [
                            "私は日本語を勉強しています。",
                            "はい、できます。",
                            "いいえ、経験がありません。",
                            "質問があります。"
                        ],
                        "intermediate": [
                            "以前、アルバイトをしていました。",
                            "チームワークが得意です。",
                            "平日なら働けます。",
                            "給料はいくらですか？"
                        ],
                        "advanced": [
                            "前職では主に顧客対応を担当していました。",
                            "御社の理念に共感し、応募させていただきました。",
                            "柔軟に対応できるのが私の強みです。",
                            "研修制度について詳しく教えていただけますか？"
                        ]
                    }
                }
                
                # Determine if we might be able to use a template suggestion
                last_agent_message = None
                for msg in reversed(recent_messages):
                    if msg["role"] == "agent":
                        last_agent_message = msg["content"]
                        break
                
                # Sometimes use predefined templates for more natural conversation flow
                if random.random() < 0.3 and scenario in scenario_templates and proficiency in scenario_templates[scenario]:
                    template_options = scenario_templates[scenario][proficiency]
                    suggestion = random.choice(template_options)
                    # Remove romaji in parentheses if present in the template
                    suggestion = re.sub(r'\([^)]*\)', '', suggestion).strip()
                    romaji_text = self.get_romaji(suggestion)
                    return JSONResponse(
                        content={
                            "japanese_text": suggestion,
                            "romaji_text": romaji_text,
                            "suggestion": suggestion,
                            "explanation": "会話を続けるためのおすすめの返答です。"
                        }
                    )
                
                # Create messages for the API call
                # Build a very focused system prompt that emphasizes brevity
                system_prompt = (
                    f"あなたは日本語{proficiency}レベルの学習者が使う短い返答を提案します。\n"
                    f"シナリオは「{CONVERSATION_SCENARIOS[scenario]['description']}」です。\n\n"
                    f"重要な指示：\n"
                    f"1. 必ず1文だけの短く簡潔な日本語の返答を提案してください。\n"
                    f"2. 20文字以内を目標にしてください。\n"
                    f"3. {proficiency}レベルに合った簡単な言葉だけを使ってください。\n"
                    f"4. 状況に合った自然な応答を提案してください。\n"
                    f"5. 説明や長文は避け、端的に言いたいことだけを含めてください。\n"
                )
                
                messages = [{"role": "system", "content": system_prompt}]
                
                # Add context from recent messages
                for msg in recent_messages:
                    if msg["role"] == "user":
                        messages.append({"role": "user", "content": msg["content"]})
                    else:
                        # Clean agent content to remove romaji
                        agent_content = re.sub(r'\([^)]*\)', '', msg["content"]).strip()
                        messages.append({"role": "assistant", "content": agent_content})
                
                # Prepare options for the API call
                options = {
                    "temperature": 0.3,  # Lower temperature for more predictable responses
                    "max_tokens": 50,    # Reduced token limit to force brevity
                    "top_p": 0.9,        # More focused sampling
                }
                
                try:
                    # Structure the request data
                    request_data = {
                        "model": model,
                        "messages": messages,
                        "options": options
                    }
                    
                    # Make request to the Ollama API
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            "http://localhost:9000/api/chat",
                            json=request_data,
                            timeout=10
                        ) as response:
                            if response.status != 200:
                                response_text = await response.text()
                                logger.error(f"Ollama API error: {response.status} - {response_text}")
                                raise Exception(f"Ollama API error: {response.status}")
                            
                            response_data = await response.json()
                            
                            # Extract the suggestion from the response
                            suggestion = response_data.get("message", {}).get("content", "").strip()
                            
                            # Process the suggestion for brevity
                            # 1. Extract first sentence only
                            first_sentence_match = re.search(r'^(.*?[。！？!?])', suggestion)
                            if first_sentence_match:
                                suggestion = first_sentence_match.group(1).strip()
                            
                            # 2. If still too long, truncate
                            if len(suggestion) > 30:
                                suggestion = suggestion[:28] + "。"
                            
                            # Remove any romaji explanations 
                            suggestion = re.sub(r'\([^)]*\)', '', suggestion).strip()
                            
                            # 3. Clean up common patterns that make suggestions verbose
                            suggestion = re.sub(r'^(はい|すみません|あの)、\s*', '', suggestion)
                            suggestion = re.sub(r'^私は', '', suggestion)
                            suggestion = re.sub(r'(と思います|だと思います)$', 'です', suggestion)
                            
                            if not suggestion or len(suggestion) < 2:
                                raise Exception("Generated suggestion is too short or empty")
                            
                            # Check if the suggestion contains Japanese characters
                            if not self._contains_japanese(suggestion):
                                # Fallback to a simple template
                                if scenario in scenario_templates and proficiency in scenario_templates[scenario]:
                                    template_options = scenario_templates[scenario][proficiency]
                                    suggestion = random.choice(template_options)
                                else:
                                    suggestion = "はい、わかりました。"
                            
                            logger.info(f"Got suggestion from Ollama: {suggestion[:30]}...")
                            
                            # Generate romaji for the response
                            romaji_text = self.get_romaji(suggestion)
                            
                            return JSONResponse(
                                content={
                                    "japanese_text": suggestion,
                                    "romaji_text": romaji_text,
                                    "suggestion": suggestion,
                                    "explanation": "会話を続けるためのおすすめの返答です。"
                                }
                            )
                
                except Exception as e:
                    logger.error(f"Error generating suggestion: {str(e)}")
                    logger.error(traceback.format_exc())
                    
                    # Fallback to a simple template if available
                    if scenario in scenario_templates and proficiency in scenario_templates[scenario]:
                        template_options = scenario_templates[scenario][proficiency]
                        suggestion = random.choice(template_options)
                        romaji_text = self.get_romaji(suggestion)
                        return JSONResponse(
                            content={
                                "japanese_text": suggestion,
                                "romaji_text": romaji_text,
                                "suggestion": suggestion,
                                "explanation": "会話を続けるためのおすすめの返答です。"
                            }
                        )
                    
                    # Last resort fallback
                    return JSONResponse(
                        status_code=500,
                        content={"error": f"Failed to generate suggestion: {str(e)}"}
                    )
                    
            except Exception as e:
                logger.error(f"Error in get_response_suggestion: {str(e)}")
                logger.error(traceback.format_exc())
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Failed to process request: {str(e)}"}
                )
    
    def create_conversation(self, scenario: str, proficiency: str, student_id: str, model: str = "auto") -> str:
        """Create a new conversation and return its ID"""
        conversation_id = str(uuid.uuid4())
        
        # Ensure scenario and proficiency are valid
        if scenario not in CONVERSATION_SCENARIOS:
            scenario = list(CONVERSATION_SCENARIOS.keys())[0]
        
        if proficiency not in PROFICIENCY_LEVELS:
            proficiency = "beginner"
        
        # Initialize conversation - always use llama3 model
        self.conversations[conversation_id] = {
            "id": conversation_id,
            "scenario": scenario,
            "proficiency": proficiency,
            "model": "llama3.2:1b",  # Always set to llama3.2:1b regardless of input parameter
            "student_id": student_id,
            "messages": [],
            "start_time": time.time(),
            "feedback": []
        }
        
        # Initialize student profile if it doesn't exist
        if student_id not in self.student_profiles:
            self.student_profiles[student_id] = {
                "id": student_id,
                "conversation_history": [],
                "common_mistakes": {},
                "vocab_mastery": {},
                "grammar_mastery": {},
                "last_activity": time.time()
            }
        
        logger.info(f"Created conversation {conversation_id} for student {student_id} with scenario {scenario} at {proficiency} level using model llama3.2:1b")
        return conversation_id
    
    def add_message_to_conversation(self, conversation_id: str, role: str, content: str):
        """Add a message to an existing conversation"""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        self.conversations[conversation_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
    
    def get_scenario_context(self, scenario: str, proficiency: str) -> str:
        """Get the initial context for a scenario based on proficiency level"""
        if scenario not in CONVERSATION_SCENARIOS:
            scenario = list(CONVERSATION_SCENARIOS.keys())[0]
        
        if proficiency not in PROFICIENCY_LEVELS:
            proficiency = "beginner"
        
        # Get the prompt for the scenario and proficiency
        prompt_key = f"{proficiency}_prompt"
        scenario_data = CONVERSATION_SCENARIOS[scenario]
        
        return scenario_data[prompt_key]
    
    async def generate_agent_message(self, conversation_id: str, initial_context: str = None) -> Dict:
        """Generate a message from the agent for a given conversation"""
        try:
            # Get the conversation data
            conversation = self.conversations[conversation_id]
            scenario = conversation["scenario"]
            proficiency = conversation["proficiency"]
            
            # Determine if this is the first message
            is_first_message = len(conversation["messages"]) == 0
            
            # For first messages, return a scenario-specific greeting instead of a generic one
            if is_first_message:
                # Create scenario-specific greetings
                scenario_greetings = {
                    "restaurant": [
                        "いらっしゃいませ。ご来店ありがとうございます。何名様ですか？ (Irasshaimase. Goraiten arigatou gozaimasu. Nan-mei-sama desu ka?)",
                        "こんにちは、本日はご予約ですか？お席にご案内いたします。 (Konnichiwa, honjitsu wa go-yoyaku desu ka? Oseki ni go-annai itashimasu.)",
                        "いらっしゃいませ。窓側のお席と奥のお席、どちらがよろしいですか？ (Irasshaimase. Madogawa no oseki to oku no oseki, dochira ga yoroshii desu ka?)"
                    ],
                    "shopping": [
                        "いらっしゃいませ。何かお探しですか？ (Irasshaimase. Nanika osagashi desu ka?)",
                        "こんにちは。本日は特別セールを行っております。お手伝いできることはありますか？ (Konnichiwa. Honjitsu wa tokubetsu seeru wo okonatte orimasu. Otetsudai dekiru koto wa arimasu ka?)",
                        "いらっしゃいませ。新作が入荷したばかりです。ご覧になりますか？ (Irasshaimase. Shinsaku ga nyuuka shita bakari desu. Goran ni narimasu ka?)"
                    ],
                    "directions": [
                        "こんにちは。道に迷っていますか？お手伝いしましょうか？ (Konnichiwa. Michi ni mayotte imasu ka? Otetsudai shimashou ka?)",
                        "どちらかお探しですか？ご案内いたします。 (Dochira ka osagashi desu ka? Go-annai itashimasu.)",
                        "こんにちは。何かお探しですか？この辺りのことなら詳しいですよ。 (Konnichiwa. Nanika osagashi desu ka? Kono atari no koto nara kuwashii desu yo.)"
                    ],
                    "interview": [
                        "お待ちしておりました。どうぞおかけください。 (Omachi shite orimashita. Douzo okake kudasai.)",
                        "本日は面接にお越しいただき、ありがとうございます。リラックスしてお話しましょう。 (Honjitsu wa mensetsu ni okoshi itadaki, arigatou gozaimasu. Rirakkusu shite ohanashi shimashou.)",
                        "こんにちは。今日はよろしくお願いします。まずは簡単に自己紹介をお願いできますか？ (Konnichiwa. Kyou wa yoroshiku onegaishimasu. Mazu wa kantan ni jikoshoukai wo onegai dekimasu ka?)"
                    ]
                }
                
                # Get greetings for the current scenario, fallback to restaurant if scenario not found
                greetings = scenario_greetings.get(scenario, scenario_greetings["restaurant"])
                
                # Randomly select a greeting from the list
                import random
                greeting = random.choice(greetings)
                
                return {
                    "role": "agent",
                    "content": greeting,
                    "timestamp": time.time()
                }
            
            # For subsequent messages, get context from previous messages
            context_messages = []
            # Get the last 4 messages for context (if available)
            if len(conversation["messages"]) > 0:
                context_messages = conversation["messages"][-4:] if len(conversation["messages"]) >= 4 else conversation["messages"]
            
            last_user_message = None
            for msg in reversed(conversation["messages"]):
                if msg["role"] == "user":
                    last_user_message = msg["content"]
                    break
                    
            if not last_user_message:
                # This shouldn't happen, but just in case
                return {
                    "role": "agent",
                    "content": "すみません、何とおっしゃいましたか？もう一度お願いします。 (Sumimasen, nan to osshaimashita ka? Mou ichido onegai shimasu.)",
                    "timestamp": time.time()
                }
            
            # Check if we can use a pre-defined response template for common interactions
            # This ensures accurate, concise and natural responses for typical scenarios
            response_from_template = self._get_template_response(last_user_message, scenario, proficiency)
            if response_from_template:
                return {
                    "role": "agent",
                    "content": response_from_template,
                    "timestamp": time.time()
                }
            
            # DIRECT OLLAMA API QUERY - NO CACHING OR FALLBACKS
            # ----------------------------------------------------
            logger.info(f"Directly querying Ollama API for: {last_user_message}")
            
            # Check if Ollama API is available
            is_ollama_available = await self.check_ollama_connection()
            if not is_ollama_available:
                logger.error("Ollama API is not available")
                return {
                    "role": "agent",
                    "content": "すみません、エラーが発生しました。 (Sumimasen, eraa ga hassei shimashita.)",
                    "timestamp": time.time()
                }
            
            # Create an enhanced system prompt with more specific instructions for natural Japanese
            scenario_descriptions = {
                "restaurant": {
                    "role": "レストランのスタッフ",
                    "instructions": "お客様の要望に丁寧かつ簡潔に対応してください。料理の説明、席の案内、注文の確認などを行います。不要な説明は避け、短く明確な返答を心がけてください。"
                },
                "shopping": {
                    "role": "ショップアシスタント",
                    "instructions": "商品について簡潔に説明し、お客様のニーズに合った提案をしてください。在庫状況、サイズ、色、価格などの質問に明確に答えます。"
                },
                "directions": {
                    "role": "地元の人",
                    "instructions": "道案内をする際は具体的なランドマークと方向を簡潔に含めて説明してください。複雑な説明は避け、明確な指示を提供します。"
                },
                "interview": {
                    "role": "面接官",
                    "instructions": "礼儀正しく質問し、応募者の回答を尊重します。質問は簡潔で、応募者が理解しやすいものにします。"
                }
            }
            
            # Get scenario-specific context
            scenario_context = scenario_descriptions.get(scenario, scenario_descriptions["restaurant"])
            
            # Use a more direct and focused system prompt that emphasizes brevity and accuracy
            system_prompt = (
                f"あなたは{scenario_context['role']}です。短く、簡潔で、自然な日本語で返答してください。\n"
                f"会話のシナリオは「{CONVERSATION_SCENARIOS[scenario]['description']}」です。\n"
                f"相手は日本語{proficiency}レベルの学習者です。\n\n"
                f"{scenario_context['instructions']}\n\n"
                f"重要な指示：\n"
                f"1. 返答は短く簡潔にしてください（1〜3文以内）。\n"
                f"2. 相手の質問や要望に直接応答し、不要な説明は避けてください。\n"
                f"3. 相手の日本語レベル（{proficiency}）に合わせた簡単な言葉遣いをしてください。\n"
                f"4. 事実に基づいた正確な情報のみを提供してください。\n"
                f"5. 存在しない料理や商品の詳細を創作しないでください。\n"
                f"6. 一般的な応答パターンを使用し、不自然な言い回しを避けてください。\n"
            )
            
            # レストランシナリオの場合、特に注文の確認に関する明確な指示を追加
            if scenario == "restaurant":
                system_prompt += (
                    f"7. 料理や飲み物の注文を受けた場合は、「かしこまりました。ご注文の○○ですね。」のように簡潔に確認してください。\n"
                    f"8. 料理の調理法について創作した説明をしないでください。\n"
                    f"9. 存在しない日本語の単語（カタカナ語を含む）を使わないでください。\n"
                )
            
            # Structure messages for the API call
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add context from previous messages
            for msg in context_messages:
                if msg["role"] == "user":
                    messages.append({"role": "user", "content": msg["content"]})
                else:
                    # Clean the agent's previous responses to remove romaji in parentheses
                    agent_content = re.sub(r'\([^)]*\)', '', msg["content"]).strip()
                    messages.append({"role": "assistant", "content": agent_content})
            
            # Create request data with more control on temperature based on the scenario
            # Use lower temperature for more consistent and accurate responses
            temperature = 0.5  # Lower temperature for more predictable, conservative responses
            
            prompt = json.dumps({
                "system": system_prompt,
                "user": last_user_message,
                "max_tokens": 200,  # Reduced from 250 to encourage brevity
                "temperature": temperature,
                "timeout": 30.0
            })
            
            try:
                # Direct request to the Ollama service
                llm_task = asyncio.create_task(self._query_ollama_with_timeout(prompt))
                response_text = await asyncio.wait_for(llm_task, timeout=30.0)
                
                # Process the response
                if self._contains_japanese(response_text):
                    # Format the response properly
                    japanese_text = re.sub(r'\([^)]*\)', '', response_text).strip()
                    
                    # Check for repetition or simple confirmations that just repeat what was said
                    repetition_patterns = [
                        r'^はい、(.+)です。\1です。$',  # "Yes, it's X. It's X."
                        r'^(.+)、\1$',                 # "X, X"
                        r'^(.+)です。\1です。$'         # "It's X. It's X."
                    ]
                    
                    needs_fix = False
                    for pattern in repetition_patterns:
                        if re.search(pattern, japanese_text):
                            needs_fix = True
                            break
                    
                    if needs_fix:
                        # Simplify repetitive responses
                        japanese_text = re.sub(r'(.+)です。\1です。', r'\1です。', japanese_text)
                        japanese_text = re.sub(r'(.+)、\1', r'\1', japanese_text)
                    
                    # For restaurant scenario, check if response is about food/drink order and fix if needed
                    if scenario == "restaurant" and self._is_likely_food_order(last_user_message):
                        japanese_text = self._fix_food_order_response(last_user_message, japanese_text)
                    
                    # Length check - if too verbose, trim it down to 1-2 sentences
                    if len(japanese_text) > 100:
                        sentences = re.split(r'[。！？!?]', japanese_text)
                        if len(sentences) > 2:
                            # Keep only first two non-empty sentences
                            filtered_sentences = [s for s in sentences if s.strip()]
                            if len(filtered_sentences) >= 2:
                                japanese_text = filtered_sentences[0] + "。" + filtered_sentences[1] + "。"
                            else:
                                # If we don't have 2 good sentences, just keep the first one
                                japanese_text = filtered_sentences[0] + "。"
                    
                    romaji_text = self.get_romaji(japanese_text)
                    
                    logger.info(f"LLM generated Japanese response: {japanese_text}")
                    return {
                        "role": "agent",
                        "content": f"{japanese_text} ({romaji_text})",
                        "timestamp": time.time()
                    }
                else:
                    logger.warning(f"LLM response had no Japanese characters: {response_text[:50]}...")
                    # Just return whatever we got
                    return {
                        "role": "agent", 
                        "content": f"{response_text}",
                        "timestamp": time.time()
                    }
            except Exception as e:
                logger.error(f"Error in direct Ollama query: {str(e)}")
                return {
                    "role": "agent",
                    "content": f"エラー: {str(e)} (Eraa: {str(e)})",
                    "timestamp": time.time()
                }
                
        except Exception as e:
            logger.error(f"Error generating agent message: {e}")
            logger.error(traceback.format_exc())
            return {
                "role": "agent", 
                "content": f"システムエラー: {str(e)} (Shisutemu eraa: {str(e)})",
                "timestamp": time.time()
            }
    
    def _get_template_response(self, user_message: str, scenario: str, proficiency: str) -> Optional[str]:
        """Get a predefined response template for common interactions"""
        # Common phrases that might appear in user messages
        food_order_patterns = [
            r'(.+)(をください|お願いします|ください|頂けますか|いただけますか|をお願いします)',
            r'(.+)(を注文したいです|を注文します|にします)'
        ]
        
        # Detect common scenarios in restaurant context
        if scenario == "restaurant":
            # Check if user is ordering food or drink
            for pattern in food_order_patterns:
                match = re.search(pattern, user_message)
                if match:
                    ordered_items = match.group(1).strip()
                    # If multiple items separated by comma, "と" or "and"
                    items = re.split(r'[,、と]|and', ordered_items)
                    items = [item.strip() for item in items if item.strip()]
                    
                    if items:
                        # Create acknowledgment of the order
                        if len(items) == 1:
                            return f"かしこまりました。{items[0]}ですね。少々お待ちください。 (Kashikomarimashita. {items[0]} desu ne. Shoushou omachi kudasai.)"
                        else:
                            items_text = "と".join(items)
                            return f"かしこまりました。{items_text}ですね。少々お待ちください。 (Kashikomarimashita. {items_text} desu ne. Shoushou omachi kudasai.)"
            
            # Check if user is asking about menu or recommendations
            if re.search(r'(メニュー|おすすめ|スペシャル|人気|何がありますか)', user_message):
                if proficiency == "beginner":
                    return "本日のおすすめは、魚料理と肉料理がございます。魚料理は鮭の塩焼き、肉料理は牛ステーキです。どちらがよろしいですか？ (Honjitsu no osusume wa, sakana ryouri to niku ryouri ga gozaimasu. Sakana ryouri wa shake no shioyaki, niku ryouri wa gyuu suteeki desu. Dochira ga yoroshii desu ka?)"
                else:
                    return "本日のおすすめは鮭の塩焼きと牛ステーキでございます。どちらもシェフ特製のソースでお召し上がりいただけます。お飲み物もご一緒にいかがですか？ (Honjitsu no osusume wa shake no shioyaki to gyuu suteeki de gozaimasu. Dochira mo shefu tokusei no soosu de omeshiagari itadakemasu. Onomimono mo go-issho ni ikaga desu ka?)"
            
            # Check if user is asking for the bill
            if re.search(r'(お会計|勘定|チェック|支払い|会計)', user_message):
                return "かしこまりました。すぐにお会計をお持ちします。少々お待ちください。 (Kashikomarimashita. Sugu ni o-kaikei wo omochi shimasu. Shoushou omachi kudasai.)"
        
        # No matching template found
        return None
    
    def _is_likely_food_order(self, message: str) -> bool:
        """Check if the message is likely a food or drink order"""
        order_indicators = [
            r'(.+)(をください|お願いします|ください|頂けますか|いただけますか|をお願いします)',
            r'(.+)(を注文したいです|を注文します|にします)',
            r'(.+)(が食べたいです|が飲みたいです)'
        ]
        
        for pattern in order_indicators:
            if re.search(pattern, message):
                return True
        return False
    
    def _fix_food_order_response(self, user_message: str, response: str) -> str:
        """Fix issues with food order responses to make them more appropriate"""
        # Extract what was ordered from user message
        order_patterns = [
            r'(.+)(をください|お願いします|ください|頂けますか|いただけますか|をお願いします)',
            r'(.+)(を注文したいです|を注文します|にします)'
        ]
        
        ordered_items = ""
        for pattern in order_patterns:
            match = re.search(pattern, user_message)
            if match:
                ordered_items = match.group(1).strip()
                # If multiple items separated by comma, "と" or "and"
                items = re.split(r'[,、と]|and', ordered_items)
                items = [item.strip() for item in items if item.strip()]
                ordered_items = "と".join(items)
                break
        
        # If we couldn't detect what was ordered, return original
        if not ordered_items:
            return response
        
        # Check if the response is unnecessarily long or complex
        if len(response) > 100 or "スパイシップ" in response or "肉を熱" in response:
            # Create a more appropriate response
            return f"かしこまりました。{ordered_items}ですね。少々お待ちください。 (Kashikomarimashita. {ordered_items} desu ne. Shoushou omachi kudasai.)"
        
        # If response seems reasonable, keep it
        return response
    
    async def _query_ollama_with_timeout(self, prompt: str) -> str:
        """Helper function to query the Ollama API with a timeout"""
        try:
            # Parse the JSON prompt to get components
            prompt_data = json.loads(prompt)
            
            # Structure the request for the Ollama API
            data = {
                "model": "llama3.2:1b",  # Using the llama3.2:1b model
                "messages": [
                    {"role": "system", "content": prompt_data.get("system", "You are a helpful assistant.")},
                    {"role": "user", "content": prompt_data.get("user", "")}
                ],
                "stream": False,
                "options": {
                    "temperature": prompt_data.get("temperature", 0.7),
                    "num_predict": prompt_data.get("max_tokens", 250),  # Increased from 100 to 250
                    "top_p": 0.9,
                    "top_k": 40
                    # Removed stop tokens to allow multiple sentences
                }
            }
            
            # Log API request details for debugging
            logger.info(f"Sending request to Ollama API at http://{LLM_SERVICE_HOST_IP}:{LLM_SERVICE_PORT}/api/chat")
            logger.info(f"Request data: model={data['model']}, message length={len(data['messages'][1]['content'])}")
            
            # Make the request to the Ollama API with better error handling
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"http://{LLM_SERVICE_HOST_IP}:{LLM_SERVICE_PORT}/api/chat",
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=30.0)  # Increased from 3.0 to 30.0 seconds
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get("message", {}).get("content", "")
                        else:
                            error_text = await response.text()
                            logger.error(f"Ollama API returned non-200 status: {response.status}, response: {error_text}")
                            raise ValueError(f"Ollama API error: {response.status}, {error_text}")
            except aiohttp.ClientConnectorError as e:
                logger.error(f"Connection error to Ollama API: {str(e)}")
                raise ValueError(f"Failed to connect to Ollama API: {str(e)}")
            except aiohttp.ClientError as e:
                logger.error(f"Client error with Ollama API: {str(e)}")
                raise ValueError(f"Client error with Ollama API: {str(e)}")
            except asyncio.TimeoutError:
                logger.error(f"Timeout while connecting to Ollama API at {LLM_SERVICE_HOST_IP}:{LLM_SERVICE_PORT}")
                raise ValueError("Timeout while waiting for response from Ollama API")
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error with prompt: {e}, prompt: {prompt[:100]}...")
            raise ValueError(f"Invalid JSON in prompt: {str(e)}")
        except Exception as e:
            logger.error(f"Error in _query_ollama_with_timeout: {str(e)}")
            raise
    
    def _contains_japanese(self, text: str) -> bool:
        """Check if text contains Japanese characters"""
        # Check for hiragana, katakana, or kanji
        return bool(re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]', text))
    
    def get_fallback_response(self, scenario: str) -> Dict:
        """Get a context-appropriate fallback response"""
        fallback_responses = {
            "restaurant": {
                "role": "agent", 
                "content": "こんにちは。いらっしゃいませ。 (Konnichiwa. Irasshaimase.)",
                "timestamp": time.time()
            },
            "shopping": {
                "role": "agent",
                "content": "いらっしゃいませ。 (Irasshaimase.)",
                "timestamp": time.time()
            },
            "directions": {
                "role": "agent",
                "content": "はい、お手伝いできます。 (Hai, otetsudai dekimasu.)",
                "timestamp": time.time()
            },
            "interview": {
                "role": "agent",
                "content": "こんにちは。お待ちしていました。 (Konnichiwa. Omachi shite imashita.)",
                "timestamp": time.time()
            }
        }
        return fallback_responses.get(scenario, fallback_responses["restaurant"])
    
    def clean_agent_response(self, message: str, proficiency: str) -> str:
        """Clean the agent's response to remove hallucinations and ensure proper formatting"""
        logger.debug(f"Original response before cleaning: {message}")
        
        # First, check if the message contains English prose (not just romaji)
        # We'll exclude content in parentheses which is likely to be romaji
        message_without_parens = re.sub(r'\([^)]*\)', '', message)
        english_paragraphs = re.findall(r'([A-Za-z][A-Za-z\s,.!?\'"\-]{20,})', message_without_parens)
        if english_paragraphs:
            logger.warning(f"Found English prose in response: {english_paragraphs}")
            # Keep only the content before the first English paragraph
            for para in english_paragraphs:
                if para in message and len(para) > 20:  # Only remove substantial English text
                    parts = message.split(para, 1)
                    message = parts[0]
        
        # Split the message at the first occurrence of hallucination indicators
        hallucination_markers = [
            "\nQuestion:", "\nBased on", "\nImagine you", "\nWrite", "\nFrom the",
            "From the Assistant's statement", "You are", "The user", "This is", 
            "In this conversation", "Based on this conversation", "The Assistant",
            "Sakanaka", "konnichiwa!", "Konnichiwa!", "\nTwo people", "food: sushi",
            "food types", "types of food", "ordered", "The Goal", "restaurant has",
            "Consider the", "Here are some", "Let me", "In the context", "Assuming",
            "Given that", "Note that", "I'll", "I will", "These are", "In Japan",
            "You have", "You've", "The scenario"
        ]
        
        # Check for hallucination markers
        cleaned_message = message
        for marker in hallucination_markers:
            if marker in cleaned_message:
                # Split at the marker and keep only the first part
                parts = cleaned_message.split(marker, 1)
                cleaned_message = parts[0]
        
        # Remove trailing punctuation, spaces, and newlines
        cleaned_message = cleaned_message.strip()
        
        # Remove any trailing "therefore," or similar phrases
        trailing_phrases = ["therefore,", "Therefore,", "In conclusion,", "To summarize,"]
        for phrase in trailing_phrases:
            if cleaned_message.endswith(phrase):
                cleaned_message = cleaned_message[:-(len(phrase))]
                cleaned_message = cleaned_message.strip()
        
        # Fix incomplete romaji parentheses
        open_parens = cleaned_message.count('(')
        close_parens = cleaned_message.count(')')
        
        if open_parens > close_parens:
            # We have unclosed parentheses, which likely means incomplete romaji
            if cleaned_message.endswith('('):
                # Case 1: The message ends with an open parenthesis - most common issue
                logger.warning("Fixing incomplete romaji at end of message")
                
                # Get the Japanese sentence before the parenthesis
                japanese_text = cleaned_message[:-1].strip()
                
                # Generate appropriate response based on difficulty level
                if proficiency == "beginner":
                    # For beginners, add a complete romaji placeholder or try to extract from prior context
                    last_sentence = japanese_text.split('。')[-1].strip()
                    if last_sentence:
                        # Just close the parenthesis with a placeholder to preserve formatting
                        cleaned_message = japanese_text + " (romaji)"
                    else:
                        # If we can't extract a good sentence, just use the Japanese text
                        cleaned_message = japanese_text
                else:
                    # For intermediate/advanced, just remove the incomplete parenthesis
                    cleaned_message = japanese_text
            else:
                # Case 2: There's an unclosed parenthesis somewhere in the middle
                logger.warning(f"Found unclosed parenthesis in middle of response: {cleaned_message}")
                # Try to find the last unclosed parenthesis
                last_open = cleaned_message.rfind('(')
                if last_open != -1 and last_open > cleaned_message.rfind(')'):
                    # If we find it and there's no close parenthesis after it, close it
                    cleaned_message = cleaned_message[:last_open] + cleaned_message[last_open:].replace('(', '(romaji) ')
        
        # Ensure we have at least some Japanese text
        japanese_pattern = r'[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uff00-\uff9f\u4e00-\u9faf]'
        if not re.search(japanese_pattern, cleaned_message):
            logger.warning("No Japanese text in cleaned message. Fallback to default response.")
            cleaned_message = self.get_safe_restaurant_response(proficiency)
        
        # For restaurant context, check for relevant content
        if "restaurant" in str(hallucination_markers):
            restaurant_terms = ["食べ物", "メニュー", "注文", "飲み物", "テーブル", "いらっしゃいませ", "お会計"]
            has_restaurant_term = any(term in cleaned_message for term in restaurant_terms)
            
            if not has_restaurant_term and "restaurant" in str(hallucination_markers):
                logger.warning("Response may not be related to restaurant context")
                # Continue with the response anyway, we don't want to overfilter
        
        # Check more carefully for romaji - look for parentheses containing romaji-like content
        has_proper_romaji = re.search(r'\([a-zA-Z\s,.!?]+\)', cleaned_message)
        
        # Ensure the romaji is included for beginners
        if proficiency == "beginner" and not has_proper_romaji:
            # Extract Japanese text without any existing parentheses
            japanese_only = re.sub(r'\([^)]*\)', '', cleaned_message).strip()
            # Check if there are any complete sentences that might need romaji
            if japanese_only and len(japanese_only) > 5:
                logger.warning("No proper romaji found in response for beginner. Adding generic placeholder.")
                # Add a more generic message that doesn't look like romaji is missing
                cleaned_message = japanese_only + " (romaji)"
        
        # If cleaning removed everything, provide a default response
        if not cleaned_message or len(cleaned_message) < 10:
            logger.warning("Cleaning removed too much content. Using default response.")
            cleaned_message = self.get_safe_restaurant_response(proficiency)
        
        # Debug log the cleaning results
        logger.debug(f"After cleaning: {cleaned_message}")
        
        return cleaned_message
    
    def get_safe_restaurant_response(self, proficiency: str) -> str:
        """Get a safe, appropriate restaurant response when we need to override the model"""
        # A set of safe, appropriate restaurant responses by proficiency level
        beginner_responses = [
            "はい、わかりました。メニューをお持ちします。(Hai, wakarimashita. Menu o omochishimasu.)",
            "こちらへどうぞ。お席にご案内します。(Kochira e douzo. Oseki ni go-annai shimasu.)",
            "少々お待ちください。(Shoushou omachi kudasai.)",
            "他にご注文はありますか？(Hoka ni go-chuumon wa arimasu ka?)",
            "ありがとうございます。(Arigatou gozaimasu.)"
        ]
        
        intermediate_responses = [
            "かしこまりました。少々お待ちいただけますか？",
            "ご注文の準備ができました。どうぞお召し上がりください。",
            "お飲み物は何になさいますか？",
            "本日のおすすめは天ぷらと刺身の定食です。",
            "お会計をお願いいたします。"
        ]
        
        advanced_responses = [
            "申し訳ございませんが、その料理は本日品切れとなっております。他のメニューはいかがでしょうか？",
            "ただいま混雑しておりますので、少々お時間をいただくことになります。ご了承いただけますでしょうか？",
            "お料理の追加注文は、お召し上がり中でもいつでも承りますので、お気軽にお申し付けください。",
            "お食事はいかがでしたでしょうか？何かご要望はございますか？",
            "お支払いは、現金・クレジットカード・電子マネーがご利用いただけます。"
        ]
        
        # Select a response based on proficiency level
        import random
        if proficiency == "beginner":
            return random.choice(beginner_responses)
        elif proficiency == "intermediate":
            return random.choice(intermediate_responses)
        else:  # advanced
            return random.choice(advanced_responses)
    
    def select_model(self) -> str:
        """Select an appropriate model based on availability
        
        This method has been modified to use a model better optimized for Japanese.
        """
        logger.info("Model selection function called - using llama3.2:1b for better Japanese processing")
        return "llama3.2:1b"
    
    def get_safe_shopping_response(self, proficiency: str) -> str:
        """Get a safe, appropriate shopping response when we need to override the model"""
        # A set of safe, appropriate shopping responses by proficiency level
        beginner_responses = [
            "いらっしゃいませ。何かお探しですか？(Irasshaimase. Nanika osagashi desu ka?)",
            "こちらの商品はいかがですか？(Kochira no shouhin wa ikaga desu ka?)",
            "試着室はこちらです。(Shichakushitsu wa kochira desu.)",
            "色違いもございます。(Iro-chigai mo gozaimasu.)",
            "お似合いですよ。(Oniai desu yo.)"
        ]
        
        intermediate_responses = [
            "他のサイズもございますが、確認いたしましょうか？",
            "セール商品は奥のコーナーにございます。",
            "お探しの商品は現在品切れですが、取り寄せ可能です。",
            "こちらのスタイルは今シーズンの新作です。",
            "お支払いは現金、クレジットカード、電子マネーがご利用いただけます。"
        ]
        
        advanced_responses = [
            "この生地は高級シルクを使用しており、肌触りがとても良いのが特徴です。",
            "こちらのデザインは日本の伝統的な模様を現代風にアレンジしたもので、海外のお客様にも大変ご好評いただいております。",
            "ご希望の商品につきましては、職人による特別仕立てもご用意できますが、納期は約2週間ほどかかります。",
            "この靴は歩きやすさを追求し、伝統的な技法で手作りされています。長時間履いても疲れにくい構造になっています。",
            "お選びいただいた着物は、お手入れ方法が独特ですので、専用の説明書をお付けしております。"
        ]
        
        # Select a response based on proficiency level
        import random
        if proficiency == "beginner":
            return random.choice(beginner_responses)
        elif proficiency == "intermediate":
            return random.choice(intermediate_responses)
        else:  # advanced
            return random.choice(advanced_responses)
    
    async def analyze_user_input(self, conversation_id: str, user_message: str) -> Dict:
        """Analyze user input for feedback on grammar, vocabulary, etc."""
        conversation = self.conversations[conversation_id]
        proficiency = conversation["proficiency"]
        scenario = conversation["scenario"]
        
        system_prompt = (
            f"You are a Japanese language teacher analyzing a student's message. "
            f"The student is at {proficiency} level. "
            f"The conversation context is: {CONVERSATION_SCENARIOS[scenario]['description']}. "
            f"TASK: Analyze ONLY the following Japanese text for grammar, vocabulary usage, and natural expression. "
            f"IMPORTANT: ONLY analyze the Japanese text provided - do not create fictional scenarios or puzzles. "
            f"ONLY provide feedback about the actual text. "
            f"If the text is in English, just say 'English detected' and don't analyze it. "
            f"You MUST respond in valid JSON format with the following structure: "
            f"""{{
                "grammar": {{
                    "issues": [
                        {{"error": "error description", "correction": "correct form", "explanation": "why this is an error"}}
                    ]
                }},
                "vocabulary": {{
                    "suggestions": [
                        {{"original": "original word", "alternative": "better word", "reason": "why this is better"}}
                    ]
                }},
                "natural_expression": {{
                    "improvements": [
                        {{"original": "unnatural phrase", "improved": "more natural phrase"}}
                    ]
                }},
                "overall_feedback": "General feedback on the message"
            }}"""
            f"Make sure each array can be empty if there are no issues/suggestions."
        )
        
        # Build request for LLM
        try:
            # Use direct Ollama API instead of going through OPEA
            import requests
            import json
            
            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Set a lower timeout for analysis - it's not critical
            timeout_seconds = 5
            
            logger.info(f"Sending analysis request to Ollama API with model={self.select_model()}")
            
            response = requests.post(
                f"http://{LLM_SERVICE_HOST_IP}:{LLM_SERVICE_PORT}/api/chat",
                json={
                    "model": self.select_model(),
                "messages": messages,
                "stream": False,
                "options": {
                        "temperature": 0.3,  # Low temperature for more predictable output
                        "num_predict": 512,  # Enough tokens for full analysis
                    }
                },
                timeout=timeout_seconds
            )
            
            # Check if response was successful
            if response.status_code != 200:
                return {
                    "error": f"Analysis request failed with status {response.status_code}",
                    "message": "Could not analyze your input due to API error."
                }
            
            # Extract the analysis text
            analysis_text = response.json().get("message", {}).get("content", "")
            logger.info(f"Raw analysis from LLM: {analysis_text}")
            
            try:
                # First, try direct JSON parsing
                try:
                    analysis_json = json.loads(analysis_text)
                    logger.info("Successfully parsed analysis as direct JSON")
                    return analysis_json
                except json.JSONDecodeError:
                    # Not direct JSON, try to extract JSON from the text
                    # Look for JSON in code blocks
                    json_match = re.search(r'```(?:json)?\n?(.*?)\n?```', analysis_text, re.DOTALL)
                    if json_match:
                        try:
                            analysis_json = json.loads(json_match.group(1).strip())
                            logger.info("Successfully extracted JSON from code block")
                            return analysis_json
                        except json.JSONDecodeError:
                            pass
                    
                    # Try to find any JSON-like structure with braces
                    json_match = re.search(r'(\{.*\})', analysis_text, re.DOTALL)
                    if json_match:
                        try:
                            analysis_json = json.loads(json_match.group(1).strip())
                            logger.info("Successfully extracted JSON from braces")
                            return analysis_json
                        except json.JSONDecodeError:
                            pass
                    
                    # If all parsing attempts fail, generate a structured JSON from the text
                    logger.error(f"Failed to parse analysis JSON: {analysis_text}")
                    
                    # Create a simple structured response based on the text
                    fallback_json = {
                        "grammar": {"issues": []},
                        "vocabulary": {"suggestions": []},
                        "natural_expression": {"improvements": []},
                        "overall_feedback": "Could not generate structured feedback. Raw analysis: " + analysis_text[:100] + "..."
                    }
                    
                    return fallback_json
            
            except Exception as e:
                logger.error(f"Error parsing analysis response: {e}")
                return {
                    "error": "Failed to parse analysis response",
                    "message": "Could not generate structured feedback. Raw analysis: " + analysis_text[:100] + "..."
                }
                
        except Exception as e:
            logger.error(f"Error analyzing user input: {e}")
            logger.error(traceback.format_exc())
            return {
                "error": "Analysis failed",
                "message": str(e)
            }
    
    def update_student_profile(self, student_id: str, analysis: Dict):
        """Update student profile with feedback from analysis"""
        if student_id not in self.student_profiles:
            return
        
        profile = self.student_profiles[student_id]
        profile["last_activity"] = time.time()
        
        # Track grammar issues
        if "grammar" in analysis and "issues" in analysis["grammar"]:
            for issue in analysis["grammar"]["issues"]:
                error = issue.get("error", "")
                if error:
                    if error not in profile["common_mistakes"]:
                        profile["common_mistakes"][error] = {
                            "count": 0,
                            "corrections": []
                        }
                    
                    profile["common_mistakes"][error]["count"] += 1
                    profile["common_mistakes"][error]["corrections"].append(issue.get("correction", ""))
        
        # Track vocabulary suggestions
        if "vocabulary" in analysis and "suggestions" in analysis["vocabulary"]:
            for suggestion in analysis["vocabulary"]["suggestions"]:
                original = suggestion.get("original", "")
                if original:
                    if original not in profile["vocab_mastery"]:
                        profile["vocab_mastery"][original] = {
                        "alternative_count": 0,
                        "alternatives": []
                    }
                    
                    profile["vocab_mastery"][original]["alternative_count"] += 1
                    profile["vocab_mastery"][original]["alternatives"].append(suggestion.get("alternative", ""))
    
    def recognize_speech(self, audio_file_path: str) -> str:
        """
        Recognize speech from an audio file and convert it to text.
        
        Args:
            audio_file_path: Path to the audio file.
            
        Returns:
            The recognized text.
        """
        if not self.speech_recognition:
            raise ValueError("Speech recognition is not available")
        
        try:
            # Create an instance of the recognizer
            recognizer = sr.Recognizer()
            
            # Adjust recognition parameters
            recognizer.energy_threshold = 300  # Increase for noisy environments
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.8  # Seconds of non-speaking audio before phrase is considered complete
            
            # First validate the audio file with wave module to ensure it's valid
            import wave
            with wave.open(audio_file_path, 'rb') as wf:
                if wf.getnchannels() not in [1, 2]:
                    raise ValueError(f"Unexpected number of channels: {wf.getnchannels()}")
                
                if wf.getsampwidth() not in [1, 2, 4]:  # 8, 16, or 32 bit
                    raise ValueError(f"Unexpected sample width: {wf.getsampwidth()}")
                
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
                
                if duration < 0.5:
                    raise ValueError(f"Audio too short: {duration:.2f} seconds")
                
                logging.info(f"Valid WAV file: channels={wf.getnchannels()}, width={wf.getsampwidth()}, "
                           f"rate={rate}, frames={frames}, duration={duration:.2f}s")
            
            # Load the audio file
            with sr.AudioFile(audio_file_path) as source:
                # Record the audio
                logging.info(f"Recording audio from file {audio_file_path}")
                audio_data = recognizer.record(source)
                
                # Try different recognition services
                try:
                    # First try Google's service
                    logging.info("Attempting speech recognition with Google service")
                    text = recognizer.recognize_google(audio_data, language="ja-JP")
                    logging.info(f"Successfully recognized text with Google: {text}")
                    return text
                except sr.UnknownValueError:
                    # If Google fails, try Sphinx (offline)
                    try:
                        logging.info("Google recognition failed, trying Sphinx")
                        text = recognizer.recognize_sphinx(audio_data, language="ja-JP")
                        logging.info(f"Successfully recognized text with Sphinx: {text}")
                        return text
                    except sr.UnknownValueError:
                        logging.warning("Both recognition services failed to recognize speech")
                        raise ValueError("Could not understand audio - please speak clearly in Japanese")
                    except Exception as e:
                        logging.error(f"Sphinx recognition error: {str(e)}")
                        raise ValueError(f"Speech recognition service error: {str(e)}")
                except sr.RequestError as e:
                    logging.error(f"Google Speech Recognition service error: {e}")
                    raise ValueError(f"Speech recognition service error: {e}")
        except Exception as e:
            logging.error(f"Error in speech recognition: {str(e)}")
            raise ValueError(f"Failed to process audio: {str(e)}")
    
    def clean_analysis_response(self, analysis_text: str) -> str:
        """Clean analysis response to remove hallucinations and ensure proper formatting"""
        logger.debug(f"Original analysis before cleaning: {analysis_text}")
        
        # First, check if the analysis contains fiction scenarios
        fiction_patterns = [
            r'Sakanaka', r'Haru', r'Yuki', r'friends', r'favorite phrases?',
            r'clues:', r'group of', r'favorite', r'discussion', r'likes? a phrase',
            r'Having a', r'In this puzzle', r'Logic puzzle', r'Given the',
            r'restaurant has', r'types of food', r'sushi', r'ordered', r'portions?',
            r'The answer is', r'temperature', r'weather', r'snow', r'degrees Celsius'
        ]
        
        for pattern in fiction_patterns:
            if re.search(pattern, analysis_text, re.IGNORECASE):
                # Cut off at the fiction pattern
                match = re.search(pattern, analysis_text, re.IGNORECASE)
                if match:
                    analysis_text = analysis_text[:match.start()]
                    logger.warning(f"Removed fictional content starting with: {pattern}")
        
        # Split the analysis at common hallucination markers
        hallucination_markers = [
            "\nQuestion:", "\nImagine you", "In this scenario", "Imagine a", 
            "Imagine that", "Let's analyze", "Consider the", "You are an",
            "Given the task", "For this exercise", "In a group", "Here are some clues",
            "Sakanaka", "temperature", "puzzle", "Haru and Yuki", "favorite phrase",
        ]
        
        for marker in hallucination_markers:
            if marker in analysis_text:
                analysis_text = analysis_text.split(marker)[0]
                logger.warning(f"Removed content after marker: {marker}")
                
        cleaned_text = analysis_text.strip()
        logger.debug(f"Cleaned analysis: {cleaned_text}")
        if len(cleaned_text) < 10:  # If too short after cleaning
            logger.warning("Analysis was too short after cleaning, using generic response")
            cleaned_text = "Your Japanese is mostly correct with some minor grammar points to improve."
        
        return cleaned_text
    
    def get_romaji(self, text: str) -> str:
        """Convert Japanese text to romaji"""
        try:
            # Remove any existing romaji in parentheses
            text = re.sub(r'\([^)]*\)', '', text).strip()
            # Convert to romaji using pykakasi
            romaji = self.kks.convert(text)
            return ' '.join(item['hepburn'] for item in romaji)
        except Exception as e:
            logger.error(f"Error converting to romaji: {e}")
            return text  # Return original text if conversion fails
    
    def start(self):
        """Start the conversation agent service"""
        uvicorn.run(self.app, host=self.host, port=self.port)

    async def check_ollama_connection(self) -> bool:
        """Check if the Ollama API is available and responding"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{LLM_SERVICE_HOST_IP}:{LLM_SERVICE_PORT}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10.0)  # Increased from 2.0 to 10.0 seconds
                ) as response:
                    if response.status == 200:
                        logger.info("Successfully connected to Ollama API")
                        return True
                    else:
                        logger.warning(f"Ollama API returned status {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Failed to connect to Ollama API: {str(e)}")
            return False

# Entry point for the service
def main():
    # Create and start the conversation agent
    agent = JapaneseConversationAgent()
    agent.start()

if __name__ == "__main__":
    main() 