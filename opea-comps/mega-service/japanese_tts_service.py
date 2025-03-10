import json
import os
import io
import numpy as np
import soundfile as sf
from gtts import gTTS
import pyttsx3
import tempfile
import logging
import sys
import traceback

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("JapaneseTTS")

# Import the rest of the dependencies with better error handling
try:
    from comps import MicroService, ServiceOrchestrator
    from comps.cores.mega.constants import ServiceType, ServiceRoleType
    from comps.cores.proto.docarray import LLMParams
    from fastapi import Request, HTTPException
    from fastapi.responses import StreamingResponse, JSONResponse
except ImportError as e:
    logger.error(f"Failed to import OPEA components: {e}")
    logger.error("Make sure the opea-comps package is installed and the virtual environment is activated.")
    sys.exit(1)

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

# Set constants for LLM service
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = os.getenv("LLM_SERVICE_PORT", 9000)

class JapaneseTTSService:
    def __init__(self, host="0.0.0.0", port=8082):
        self.host = host
        self.port = port
        self.endpoints = {
            "tts": "/v1/japanese_tts",
            "translate": "/v1/translate_and_speak",
            "learning": "/v1/learning_mode",
            "examples": "/v1/example_generator"
        }
        
        logger.info(f"Initializing Japanese TTS Service on {host}:{port}")
        
        try:
            self.megaservice = ServiceOrchestrator()
            os.environ["LOGFLAG"] = "true"  # Enable detailed logging
        except Exception as e:
            logger.error(f"Failed to initialize ServiceOrchestrator: {e}")
            raise
        
        # Initialize Japanese text processing tools
        try:
            self.tagger = fugashi.Tagger()
            self.kks = pykakasi.kakasi()
            logger.info("Japanese text processing tools initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Japanese text processing tools: {e}")
            raise
        
        # Initialize pyttsx3 for offline TTS fallback
        try:
            self.offline_tts_engine = pyttsx3.init()
            # Try to set a Japanese voice if available
            voices = self.offline_tts_engine.getProperty('voices')
            japanese_voice_found = False
            for voice in voices:
                if 'japanese' in voice.name.lower() or 'ja' in voice.id.lower():
                    self.offline_tts_engine.setProperty('voice', voice.id)
                    logger.info(f"Using Japanese voice: {voice.name}")
                    japanese_voice_found = True
                    break
            
            if not japanese_voice_found:
                logger.warning("No Japanese voice found for pyttsx3, using default voice")
                
            self.offline_tts_available = True
            logger.info("Offline TTS engine initialized")
        except Exception as e:
            logger.warning(f"Offline TTS engine initialization failed: {e}")
            self.offline_tts_available = False
        
        logger.info("Japanese TTS Service initialized with gTTS (primary) and pyttsx3 (fallback)")
    
    def add_remote_service(self):
        """Add LLM service for translation and content generation"""
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        print(f"\nConfiguring LLM service:")
        print(f"- Host: {LLM_SERVICE_HOST_IP}")
        print(f"- Port: {LLM_SERVICE_PORT}")
        print(f"- Endpoint: {llm.endpoint}")
        print(f"- Full URL: http://{LLM_SERVICE_HOST_IP}:{LLM_SERVICE_PORT}{llm.endpoint}")
        self.megaservice.add(llm)
    
    def process_japanese_text(self, text, include_romaji=False, include_furigana=False):
        """Process Japanese text to add learning aids"""
        results = {
            "original": text,
        }
        
        if include_romaji:
            # Convert to romaji using jaconv and pykakasi
            # First convert to hiragana with pykakasi
            hiragana_parts = []
            conversion = self.kks.convert(text)
            for item in conversion:
                hiragana_parts.append(item["hira"])
            hiragana = "".join(hiragana_parts)
            
            # Then convert hiragana to romaji with jaconv
            results["romaji"] = jaconv.kana2alphabet(hiragana)
        
        if include_furigana:
            # Generate furigana (hiragana reading aid for kanji)
            conversion = self.kks.convert(text)
            furigana = []
            for item in conversion:
                if item["orig"] != item["hira"]:
                    furigana.append({
                        "kanji": item["orig"],
                        "reading": item["hira"]
                    })
            results["furigana"] = furigana
            
            # Also generate word segmentation with readings
            words = []
            for word in self.tagger(text):
                if word.surface:  # Skip empty tokens
                    # Fix: Use the right feature for pronunciation - it might be different in different versions
                    # Try multiple attributes that might have the reading
                    reading = None
                    for attr in ['pronunciation', 'reading', 'yomi']:
                        if hasattr(word.feature, attr):
                            reading = getattr(word.feature, attr)
                            if reading:
                                break
                    
                    # If no reading found, use the surface form
                    if not reading:
                        reading = word.surface
                        
                    words.append({
                        "surface": word.surface,
                        "reading": reading,
                        "pos": word.feature.pos1 if hasattr(word.feature, 'pos1') else "unknown"
                    })
            results["words"] = words
        
        return results
    
    async def offline_tts(self, text, slow=False):
        """Fallback TTS using pyttsx3 for offline capability"""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            # Set rate (slower for learning mode)
            rate = 120 if slow else 150  # Normal rate is around 200
            self.offline_tts_engine.setProperty('rate', rate)
            
            # Save to a file
            self.offline_tts_engine.save_to_file(text, temp_filename)
            self.offline_tts_engine.runAndWait()
            
            # Read the file back into memory
            with open(temp_filename, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Clean up
            os.unlink(temp_filename)
            
            # Return as BytesIO
            audio_io = io.BytesIO(audio_data)
            audio_io.seek(0)
            return audio_io
        except Exception as e:
            print(f"Offline TTS error: {e}")
            raise e
    
    async def text_to_speech(self, text, slow=False):
        """Convert text to speech using gTTS with fallback to offline TTS"""
        # Try gTTS first (needs internet)
        try:
            tts = gTTS(text=text, lang='ja', slow=slow)
            
            # Save to a BytesIO object
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            
            return mp3_fp
        except Exception as e:
            print(f"gTTS error: {e}")
            
            # Fall back to offline TTS if available
            if self.offline_tts_available:
                print("Falling back to offline TTS...")
                return await self.offline_tts(text, slow)
            else:
                raise e
    
    async def translate_text(self, english_text, model="phi"):
        """Translate English text to Japanese using LLM"""
        # Create the prompt for translation
        translation_prompt = (
            "Translate the following English text to natural, conversational Japanese. "
            "Provide ONLY the Japanese translation, nothing else.\n\n"
            f"English: {english_text}\n\n"
            "Japanese:"
        )
        
        # Prepare request for LLM
        llm_request = {
            "messages": [{"role": "user", "content": translation_prompt}],
            "model": model,
            "max_tokens": 200,
            "temperature": 0.3,  # Lower temperature for more consistent translations
            "stream": False
        }
        
        # Get text from LLM
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"messages": llm_request["messages"]},
            llm_parameters=LLMParams(
                max_tokens=llm_request["max_tokens"],
                temperature=llm_request["temperature"],
                stream=False,
                model=llm_request["model"]
            )
        )
        
        # Extract text from LLM response
        last_node = runtime_graph.all_leaves()[-1]
        if last_node in result_dict:
            service_result = result_dict[last_node]
            if isinstance(service_result, dict) and 'choices' in service_result:
                return service_result['choices'][0]['message']['content'].strip()
        
        # Return error if translation failed
        return None
    
    async def generate_examples(self, keyword, count=3, model="phi"):
        """Generate example sentences using a keyword"""
        examples_prompt = (
            f"Generate {count} natural Japanese example sentences using the word or phrase '{keyword}'. "
            "For each sentence, provide:\n"
            "1. The Japanese sentence\n"
            "2. The romaji pronunciation\n"
            "3. The English translation\n\n"
            "Format each example as a JSON object with fields 'japanese', 'romaji', and 'english'."
        )
        
        # Prepare request for LLM
        llm_request = {
            "messages": [{"role": "user", "content": examples_prompt}],
            "model": model,
            "max_tokens": 500,
            "temperature": 0.7,
            "stream": False
        }
        
        # Get examples from LLM
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"messages": llm_request["messages"]},
            llm_parameters=LLMParams(
                max_tokens=llm_request["max_tokens"],
                temperature=llm_request["temperature"],
                stream=False,
                model=llm_request["model"]
            )
        )
        
        # Extract text from LLM response
        last_node = runtime_graph.all_leaves()[-1]
        if last_node in result_dict:
            service_result = result_dict[last_node]
            if isinstance(service_result, dict) and 'choices' in service_result:
                return service_result['choices'][0]['message']['content']
        
        return "Failed to generate examples."
    
    def start(self):
        """Start the service with all endpoints"""
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoints["tts"],  # Main endpoint
            input_datatype=dict,
            output_datatype=bytes,
        )
        
        # Define frontend route handlers
        # Serve the index.html file for the frontend
        @self.service.app.get("/")
        async def serve_frontend_index():
            frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
            with open(os.path.join(frontend_dir, "index.html"), "r") as f:
                content = f.read()
            return HTMLResponse(content=content)
        
        # Serve the app.js file for the frontend
        @self.service.app.get("/app.js")
        async def serve_frontend_js():
            frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
            with open(os.path.join(frontend_dir, "app.js"), "r") as f:
                content = f.read()
            return Response(
                content=content,
                media_type="application/javascript"
            )
        
        # Add routes for our service endpoints
        self.service.add_route(self.endpoints["tts"], self.handle_tts_request, methods=["POST"])
        self.service.add_route(self.endpoints["translate"], self.handle_translate_request, methods=["POST"])
        self.service.add_route(self.endpoints["learning"], self.handle_learning_request, methods=["POST"])
        self.service.add_route(self.endpoints["examples"], self.handle_examples_request, methods=["POST"])
        
        print(f"Japanese TTS Service configured with endpoints:")
        for name, endpoint in self.endpoints.items():
            print(f"- {name}: {endpoint}")
        
        try:
            self.service.start()
        except Exception as e:
            print(f"Error starting service: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def handle_tts_request(self, request: Request):
        """Handle basic Japanese TTS requests"""
        try:
            data = await request.json()
            japanese_text = data.get("text", "")
            
            if not japanese_text:
                return JSONResponse(
                    status_code=400,
                    content={"error": "No text provided"}
                )
            
            # Generate speech from Japanese text
            print(f"Generating speech for text: {japanese_text[:50]}...")
            audio_bytes = await self.text_to_speech(japanese_text)
            
            return StreamingResponse(
                audio_bytes, 
                media_type="audio/mp3",
                headers={
                    "Content-Disposition": "attachment; filename=japanese_speech.mp3", 
                    "Access-Control-Allow-Origin": "*"
                }
            )
        except Exception as e:
            print(f"Error in TTS request: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": f"TTS generation failed: {str(e)}"}
            )
    
    async def handle_translate_request(self, request: Request):
        """Handle translation and TTS requests"""
        try:
            data = await request.json()
            english_text = data.get("text", "")
            include_details = data.get("include_details", False)
            model = data.get("model", "phi")
            
            if not english_text:
                return JSONResponse(
                    status_code=400,
                    content={"error": "No English text provided"}
                )
            
            # Translate English to Japanese
            japanese_text = await self.translate_text(english_text, model)
            
            if not japanese_text:
                return JSONResponse(
                    status_code=500,
                    content={"error": "Translation failed"}
                )
            
            # Process Japanese text for learning aids if requested
            text_details = None
            if include_details:
                text_details = self.process_japanese_text(
                    japanese_text, 
                    include_romaji=True, 
                    include_furigana=True
                )
            
            # Generate speech from Japanese text
            print(f"Generating speech for translated text: {japanese_text[:50]}...")
            audio_bytes = await self.text_to_speech(japanese_text)
            
            # If details were requested, return them in the headers
            headers = {
                "Content-Disposition": "attachment; filename=translated_speech.mp3", 
                "Access-Control-Allow-Origin": "*"
            }
            
            if text_details:
                # Add a custom header with the translation details
                headers["X-Translation-Details"] = json.dumps(text_details)
            
            return StreamingResponse(
                audio_bytes, 
                media_type="audio/mp3",
                headers=headers
            )
        except Exception as e:
            print(f"Error in translation request: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Translation and TTS failed: {str(e)}"}
            )
    
    async def handle_learning_request(self, request: Request):
        """Handle learning mode requests with word-by-word breakdown"""
        try:
            data = await request.json()
            text = data.get("text", "")
            is_english = data.get("is_english", False)
            model = data.get("model", "phi")
            
            if not text:
                return JSONResponse(
                    status_code=400,
                    content={"error": "No text provided"}
                )
            
            # If input is English, translate it first
            japanese_text = text
            if is_english:
                japanese_text = await self.translate_text(text, model)
                if not japanese_text:
                    return JSONResponse(
                        status_code=500,
                        content={"error": "Translation failed"}
                    )
            
            # Process Japanese text for learning
            text_details = self.process_japanese_text(
                japanese_text, 
                include_romaji=True, 
                include_furigana=True
            )
            
            # Generate speech in learning mode (slower)
            print(f"Generating learning mode speech for: {japanese_text[:50]}...")
            audio_bytes = await self.text_to_speech(japanese_text, slow=True)
            
            # Save to a temporary file with a unique name
            file_id = abs(hash(japanese_text)) % 10000
            temp_filename = f"learning_{file_id}.mp3"
            
            # Return both the text details and the audio as a streaming response
            response = StreamingResponse(
                audio_bytes,
                media_type="audio/mp3",
                headers={
                    "Content-Disposition": f"attachment; filename={temp_filename}",
                    "X-Text-Details": json.dumps(text_details),
                    "Access-Control-Allow-Origin": "*"
                }
            )
            
            return response
        except Exception as e:
            print(f"Error in learning mode request: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Learning mode processing failed: {str(e)}"}
            )
    
    async def handle_examples_request(self, request: Request):
        """Handle example generation requests"""
        try:
            data = await request.json()
            keyword = data.get("keyword", "")
            count = data.get("count", 3)
            model = data.get("model", "phi")
            generate_audio = data.get("generate_audio", False)
            
            if not keyword:
                return JSONResponse(
                    status_code=400,
                    content={"error": "No keyword provided"}
                )
            
            # Generate example sentences
            examples_text = await self.generate_examples(keyword, count, model)
            
            # If audio generation is requested and we can parse the examples
            examples_with_audio = []
            if generate_audio:
                try:
                    # Try to parse the examples - this is a best effort since LLM output format may vary
                    example_lines = examples_text.strip().split('\n')
                    current_example = {}
                    
                    for line in example_lines:
                        line = line.strip()
                        if line.startswith('1.') and 'japanese' in line.lower():
                            current_example['japanese'] = line.split(':', 1)[1].strip() if ':' in line else ""
                        elif line.startswith('2.') and 'romaji' in line.lower():
                            current_example['romaji'] = line.split(':', 1)[1].strip() if ':' in line else ""
                        elif line.startswith('3.') and 'english' in line.lower():
                            current_example['english'] = line.split(':', 1)[1].strip() if ':' in line else ""
                            if current_example.get('japanese'):
                                audio_bytes = await self.text_to_speech(current_example['japanese'])
                                # We'd need to save this audio somewhere or encode it
                                # For simplicity, we'll just note that audio was generated
                                current_example['has_audio'] = True
                                examples_with_audio.append(current_example)
                                current_example = {}
                except Exception as parse_error:
                    print(f"Error parsing examples for audio: {parse_error}")
            
            response_data = {
                "examples": examples_text,
            }
            
            if examples_with_audio:
                response_data["parsed_examples"] = examples_with_audio
                response_data["note"] = "Audio generation requested, but only metadata included in response."
            
            return JSONResponse(
                content=response_data,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        except Exception as e:
            print(f"Error in examples request: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Example generation failed: {str(e)}"}
            )

# Create and start the service
if __name__ == "__main__":
    try:
        logger.info("Starting Japanese TTS Service")
        tts_service = JapaneseTTSService(host="0.0.0.0", port=8082)
        
        try:
            logger.info("Adding remote LLM service")
            tts_service.add_remote_service()
        except Exception as e:
            logger.error(f"Failed to add remote service: {e}")
            logger.error("Make sure the Ollama service is running")
            sys.exit(1)
        
        try:
            logger.info("Starting service")
            tts_service.start()
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            logger.error(traceback.format_exc())
            sys.exit(1)
    except Exception as e:
        logger.error(f"Critical error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1) 