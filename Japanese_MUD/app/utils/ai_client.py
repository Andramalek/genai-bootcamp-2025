#!/usr/bin/env python3
"""
AI Client for Japanese MUD Game
Handles interactions with OpenAI API for dynamic NPC conversations
and potentially other AI-driven features.
"""
import os
import json
import openai
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any, List

# Set up logging
logger = logging.getLogger("ai_client")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

class AIClient:
    """Client for interacting with AI APIs (currently OpenAI)."""
    
    @staticmethod
    def npc_conversation(npc_data: Dict[str, Any], player_input: str, language_level: str ="N5", conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, str]:
        """
        Generate NPC responses using OpenAI API.
        
        Args:
            npc_data (dict): NPC data including role, knowledge areas, etc.
            player_input (str): What the player said to the NPC
            language_level (str): Player's Japanese language level (N5-N1)
            conversation_history (list): Previous exchanges in the conversation
            
        Returns:
            dict: Response with Japanese and English text, language notes
        """
        if not openai.api_key:
            logger.warning("OpenAI API key not set, falling back to static dialog")
            return {
                "response_japanese": "すみません、今話せません。",
                "response_english": "Sorry, I can't talk right now.",
                "language_note": "Try again later."
            }
        
        try:
            # Construct the conversation history
            messages = [
                {"role": "system", "content": _create_npc_system_prompt(npc_data, language_level)}
            ]
            
            # Add conversation history if available
            if conversation_history:
                for exchange in conversation_history:
                    messages.append({"role": "user", "content": exchange["user"]})
                    # Parse the previous assistant response (which is a JSON string)
                    try:
                        previous_response = json.loads(exchange["assistant"])
                        # Use the Japanese response as the assistant's content in history
                        assistant_content = previous_response.get("response_japanese", "")
                    except json.JSONDecodeError:
                        # Fallback if parsing fails (shouldn't happen ideally)
                        assistant_content = exchange["assistant"] 
                    messages.append({"role": "assistant", "content": assistant_content})
            
            # Add current user input
            messages.append({"role": "user", "content": player_input})
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Ensure we have all required fields
            if "response_japanese" not in result or "response_english" not in result:
                logger.warning("AI response missing required fields")
                result = {
                    "response_japanese": "すみません、よく理解できません。",
                    "response_english": "I'm sorry, I don't understand well.",
                    "language_note": "The AI response was incomplete."
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error with OpenAI API for NPC conversation: {str(e)}")
            return {
                "response_japanese": "すみません、技術的な問題があります。",
                "response_english": "Sorry, there's a technical issue.",
                "language_note": f"Error: {str(e)}"
            }

    @staticmethod
    def generate_location_details(setting: str, coords: tuple) -> Dict[str, str]:
        """Generate location name and description using OpenAI."""
        fallback_details = {
            "name": f"{setting} at {coords}",
            "japanese_name": f"{setting} ({coords[0]},{coords[1]})",
            "description": f"A procedurally generated {setting.lower()} at {coords} (AI fallback)."
        }
        
        if not openai.api_key:
            logger.warning("OpenAI API key not set, using fallback location details")
            return fallback_details

        try:
            prompt = (
                f"You are creating locations for a text adventure game set in Japan. "
                f"Generate a distinct name (in English and simple Japanese, like 'Old Shrine Gate (古い神社の門)' or 'Riverside Market (川沿いの市場)') and a brief (1-2 sentence) description for a location. "
                f"The setting is: '{setting}'. The coordinates are ({coords[0]}, {coords[1]}). "
                f"The name and description should clearly reflect the given '{setting}'. Emphasize unique details and sensory information relevant to that setting. AVOID overly similar names or descriptions for different locations (e.g., do not reuse adjectives like 'Whispering' or 'Quiet' excessively). "
                "Respond ONLY in JSON format: {\"name\": \"English Name\", \"japanese_name\": \"Japanese Name\", \"description\": \"Brief description.\"}"
            )
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a creative world-building assistant for a text adventure game."}, 
                    {"role": "user", "content": prompt}
                ],
                temperature=0.85,
                max_tokens=120,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Basic validation
            if not all(k in result for k in ("name", "japanese_name", "description")):
                 logger.error(f"AI response for location missing keys: {result}")
                 return fallback_details # Return fallback if keys are missing
                 
            logger.info(f"Generated location details for {coords} using OpenAI: {result['name']}")
            return result

        except Exception as e:
            logger.error(f"Error generating location details with OpenAI: {str(e)}")
            return fallback_details

    @staticmethod
    def enhance_look_description(location_data: Dict[str, Any], npc_info: List[Dict[str, str]] = None) -> Optional[str]:
        """Generate an enhanced 'look' description using OpenAI, incorporating NPCs."""
        fallback_desc = location_data.get("description")
        
        if not openai.api_key:
            logger.warning("OpenAI API key not set, cannot enhance look description")
            return fallback_desc

        try:
            base_description = location_data.get("description", "an area")
            setting = location_data.get("setting", "unknown")
            location_name = location_data.get("name", "this place")
            
            # Build NPC presence string
            npc_presence = ""
            if npc_info:
                npc_list = [f"{info['name']} (a {info['role']})" for info in npc_info]
                if len(npc_list) == 1:
                    npc_presence = f"{npc_list[0]} is here."
                elif len(npc_list) > 1:
                    npc_presence = f"People present: {', '.join(npc_list)}."
                
            prompt = (
                f"You are describing a scene vividly in a text-based adventure game set in Japan. "
                f"The player typed 'look'. Based on the following information about '{location_name}', write a vivid and atmospheric description (2-4 sentences) focusing on sensory details (sights, sounds, smells), mood, and specific details someone might notice upon closer inspection. "
                f"Make it feel immersive and unique to this specific location. "
                f"**Crucially, if NPCs are present, weave them naturally into the description with a brief mention of what they might be doing (e.g., 'A samurai stands guard', 'A merchant arranges wares'). Do NOT just list them at the end.** "
                f"Do NOT list exits or items separately.\n\n"
                f"Basic Description: {base_description}\n"
                f"Setting Type: {setting}\n"
                f"People Present: {npc_presence if npc_presence else 'None'}\n\n"
                f"Enhanced Description (just the text, no preamble):"
            )
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                     {"role": "system", "content": "You are a descriptive writer for a text adventure game."}, 
                     {"role": "user", "content": prompt}
                ],
                temperature=0.75,
                max_tokens=180 # Slightly increase tokens for NPC descriptions
            )
            
            enhanced_desc = response.choices[0].message.content.strip()
            if not enhanced_desc:
                logger.warning("OpenAI returned empty enhanced look description.")
                return fallback_desc
                
            logger.info(f"Generated enhanced look description for {location_data.get('id', 'unknown')} using OpenAI.")
            return enhanced_desc
            
        except Exception as e:
            logger.error(f"Error enhancing look description with OpenAI: {str(e)}")
            return fallback_desc

    @staticmethod
    def generate_item_examination_details(item_data: Dict[str, Any], language_level: str = "N5") -> Dict[str, Any]:
        """Generate a detailed examination description for an item using AI, including potential inscriptions or details.
        
        Args:
            item_data (Dict[str, Any]): The dictionary for the item from items.json.
            language_level (str): Player's Japanese language level (N5-N1)

        Returns:
            Dict[str, Any]: A dictionary containing the detailed description and vocabulary.
        """
        fallback_response = {
            "description": item_data.get("description", f"You examine the {item_data.get('name_english', item_data.get('id'))}, but find nothing remarkable."),
            "vocabulary": []
        }
        
        if not openai.api_key:
            logger.warning("OpenAI API key not set, using fallback item description")
            return fallback_response # Return dict

        try:
            item_name_en = item_data.get("name_english", "this item")
            item_name_jp = item_data.get("name", "?")
            item_desc_base = item_data.get("description", "")
            item_vocab = ", ".join(item_data.get("vocabulary", []))
            
            # Construct a prompt asking for detailed examination, including potential Japanese text
            prompt = (
                f"You are describing an item examination in a text-based adventure game focused on Japanese learning. The player is examining a '{item_name_en}' ({item_name_jp}). "
                f"The item's basic description is: '{item_desc_base}'. Relevant Japanese vocabulary: {item_vocab}. "
                f"Write a detailed and engaging examination description (2-4 sentences). "
                f"**Crucially, invent and include a short, relevant inscription, quote, maker's mark, or detail written in Japanese on the item.** This could be related to its history, use, or maker (e.g., a wise quote on a bowl, a smith's name on a sword, a clan symbol on armor). Ensure the Japanese text is simple enough for a {language_level} learner to potentially decipher. "
                f"Describe the appearance of the Japanese text (e.g., 'engraved in gold', 'written in elegant calligraphy', 'carved crudely', 'stamped faintly'). "
                f"Example ideas: A tea cup might have a poetic phrase about tranquility. A katana might have the smith's name and date. Armor might have a clan mon (symbol)."
                f"Do NOT just repeat the basic description. Add unique details discovered upon close examination."
                f"\n\nRespond ONLY in JSON format: {{'description': 'Detailed Examination Description...', 'vocabulary': ['relevant_word1', 'relevant_word2']}} "
                f"Include 2-4 relevant Japanese vocabulary words from your description in the 'vocabulary' list (especially any words from the inscription/mark)."
            )

            response = openai.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[
                    {"role": "system", "content": "You are a creative writer describing item details for a language learning game. Output JSON."}, 
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=250, # Increase slightly for JSON
                response_format={"type": "json_object"} # Ensure JSON output
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Validate expected keys
            if not isinstance(result, dict) or "description" not in result or "vocabulary" not in result or not isinstance(result["vocabulary"], list):
                logger.error(f"AI response for item examination has incorrect format: {result}")
                return fallback_response

            # Combine descriptions
            combined_description = f"{item_data.get('description', '')}\n\nUpon closer examination: {result['description']}"
            
            logger.info(f"Generated AI examination description and vocab for {item_name_en}.")
            
            return {
                 "description": combined_description,
                 "vocabulary": result["vocabulary"]
            }
            
        except Exception as e:
            logger.error(f"Error generating AI item examination for {item_name_en}: {str(e)}")
            return fallback_response

    @staticmethod
    def generate_item_details(setting: str) -> Optional[Dict[str, Any]]:
        """Generate item details (name, desc, takable, vocab) using AI based on location setting."""
        if not openai.api_key:
            logger.warning("OpenAI API key not set, cannot generate item details.")
            return None

        try:
            # --- Refine prompt for clarity on English vs Romaji --- 
            json_format_example = '{"name": "string (Japanese Name - Kanji/Kana)", "name_english": "string (English Translation/Meaning ONLY)", "name_romaji": "string (Romaji phonetic spelling ONLY)", "description": "string (1-2 sentence description)", "can_be_taken": boolean, "vocabulary": list[string (2-4 relevant Japanese words)]}'
            prompt = (
                f"You are creating an item for a text adventure game set in Japan. The item is found in a location with the setting: '{setting}'. "
                f"Generate a plausible and contextually relevant item. It could be common, unique, useful, or decorative. "
                f"Provide: \n1. Japanese name (Kanji/Kana). \n2. English translation/meaning ONLY for 'name_english'. \n3. Romaji phonetic spelling ONLY for 'name_romaji'. "
                f"REQUIRED JSON output format: {json_format_example}"
                f"Example: For お守り, name_english should be 'Amulet' or 'Charm', and name_romaji should be 'omamori'. For 和菓子, name_english should be 'Japanese Sweets', and name_romaji should be 'wagashi'. Do NOT put Romaji in the name_english field. "
                f"Ensure the item details are consistent with the '{setting}'. 'can_be_taken' should usually be true unless it's a large fixture. Include relevant vocabulary."
            )

            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a creative item generator for a Japanese-themed text adventure game."}, 
                    {"role": "user", "content": prompt}
                ],
                temperature=0.95, # High temp for diverse items
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Basic validation
            required_keys = ["name", "name_english", "name_romaji", "description", "can_be_taken", "vocabulary"]
            if not all(k in result for k in required_keys):
                 logger.error(f"AI response for item generation missing required keys: {result}")
                 return None
            if not isinstance(result.get("vocabulary"), list) or not isinstance(result.get("can_be_taken"), bool):
                 logger.error(f"AI response for item generation has incorrect types: {result}")
                 return None
                 
            logger.info(f"Generated item details for setting '{setting}': {result.get('name_english')}")
            return result

        except Exception as e:
            logger.error(f"Error generating item details with OpenAI for setting '{setting}': {str(e)}")
            return None

    @staticmethod
    def generate_npc_details(setting: str) -> Optional[Dict[str, Any]]:
        """Generate NPC details (role, name, desc, greeting, knowledge, personality) using AI based on location setting."""
        if not openai.api_key:
            logger.warning("OpenAI API key not set, cannot generate NPC details.")
            return None

        try:
            json_format_example = (
                '{"name": "string (Japanese Name - Kanji/Kana)", ' 
                '"name_english": "string (English Name)", ' 
                '"short_description": "string (1-2 sentence description)", ' 
                '"role": "string (e.g., Shopkeeper, Traveler, Student)", ' 
                '"personality": "string (e.g., Friendly, Grumpy, Shy)", ' 
                '"greeting": "string (Simple greeting in Japanese)", ' 
                '"vocabulary": list[string (2-4 relevant Japanese words)]' 
                '}'
            )
            prompt = (
                f"You are an NPC generator for a text adventure game set in Japan. The NPC is found in a location with the setting: '{setting}'. "
                f"Generate a plausible NPC fitting the setting. Provide: \n1. Japanese name (Kanji/Kana). \n2. English full name ONLY (e.g., Kenji Tanaka) for 'name_english'. "
                f"Provide a short description, role, personality, a simple Japanese greeting, and relevant vocabulary. "
                f"REQUIRED JSON output format: {json_format_example}" 
            )

            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a creative character generator for a Japanese-themed text adventure game."}, 
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9, # Higher temp for more variety
                max_tokens=250,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Basic validation of required keys
            required_keys = ["name", "name_english", "short_description", "role", "personality", "greeting", "vocabulary"]
            if not all(k in result for k in required_keys):
                 logger.error(f"AI response for NPC generation missing required keys: {result}")
                 return None
                 
            # Further validation (e.g., knowledge is a list)
            if not isinstance(result.get("vocabulary"), list):
                 logger.error(f"AI response for NPC 'vocabulary' is not a list: {result}")
                 return None
                 
            logger.info(f"Generated NPC details for setting '{setting}': {result.get('name')} ({result.get('role')})")
            return result

        except Exception as e:
            logger.error(f"Error generating NPC details with OpenAI for setting '{setting}': {str(e)}")
            return None

    @staticmethod
    def generate_enhanced_look(setting: str, item_names: List[str], npc_names: List[str]) -> str:
        """Generate a richer, more descriptive look command output using AI."""
        if not openai.api_key:
            logger.warning("OpenAI API key not set, cannot generate enhanced look.")
            return "You look around, but your imagination fails you without the AI's help."

        try:
            item_list_str = ", ".join(item_names) if item_names else "nothing of note"
            npc_list_str = ", ".join(npc_names) if npc_names else "no one else"
            
            prompt = (
                f"You are describing a scene for a player in a text adventure game set in Japan. "
                f"The location's general setting is: '{setting}'. "
                f"The player sees the following items: {item_list_str}. "
                f"The following people are present: {npc_list_str}.\n\n" 
                f"Write a single, evocative paragraph (2-4 sentences) describing the scene. "
                f"Weave the setting, items, and people into the description naturally. "
                f"Focus on atmosphere and sensory details. Do NOT just list the items/people. "
                f"Do NOT include Japanese translations here. This is purely descriptive text."
            )

            response = openai.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[
                    {"role": "system", "content": "You are a descriptive text adventure game narrator specializing in Japanese settings."}, 
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            description = response.choices[0].message.content.strip()
            logger.info(f"Generated enhanced look for setting '{setting}'.")
            return description

        except Exception as e:
            logger.error(f"Error generating enhanced look with OpenAI for setting '{setting}': {str(e)}")
            return f"You try to look closer, but the details blur. (AI Error: {e})"

def _create_npc_system_prompt(npc_data: Dict[str, Any], language_level: str) -> str:
    """Create the system prompt for the NPC based on their data"""
    # Base prompt for Japanese language learning
    knowledge_areas = ", ".join(npc_data.get('properties', {}).get('knowledge', ['basic Japanese']))
    npc_role = npc_data.get('properties', {}).get('role', 'helpful local')
    
    base_prompt = f"""
You are a helpful and knowledgeable AI assistant playing the role of {npc_data.get('name')} in a Japanese language learning game set in Japan.
The user is a language learner at JLPT level {language_level}.

Your character information:
- Name: {npc_data.get('name')}
- Description: {npc_data.get('description')}
- Knowledge Areas: {knowledge_areas}
- Role: {npc_role}

**Your Core Task:** Engage the player in conversation, help them learn Japanese, and provide information based on your character's role and knowledge. Be creative and informative.

**Guidelines for your responses:**
1.  **Respond in JSON:** Your *entire* response MUST be a single, valid JSON object with these exact keys: "response_japanese", "response_english", "language_note".
2.  **Dual Language:** Provide your main response in Japanese ("response_japanese") and an accurate English translation ("response_english").
3.  **Language Level:** Adapt your Japanese vocabulary and grammar complexity to the user's {language_level} level. Keep sentences relatively simple for lower levels.
4.  **Be Informative & Creative:** 
    *   Actively use your stated 'Knowledge Areas' to answer player questions.
    *   When asked about specific places, history, or topics related to your role (e.g., 'Tell me about this teahouse', 'What is this shrine known for?'), **generate plausible and culturally appropriate fictional details or backstory.** Make it sound authentic to your character.
    *   Incorporate cultural insights related to Japan and your role when relevant.
5.  **Be Engaging:** Be friendly, encouraging, and maintain your character's personality.
6.  **Conciseness:** Keep responses focused, typically 1-3 sentences per language.
7.  **Language Assistance:** If the user makes a clear Japanese mistake, offer a gentle correction or suggestion within the 'language_note'.
8.  **Language Note:** Use the 'language_note' field for brief tips on vocabulary, grammar, cultural context, or corrections. This field is optional but helpful.

**Example Interaction:**
User: この茶室の歴史について教えてください。(Tell me about the history of this teahouse.)
Your JSON Response (Example):
```json
{{
  "response_japanese": "この茶室は江戸時代に有名な茶人によって建てられたと言われています。特にこの庭園の眺めは素晴らしいですよ。",
  "response_english": "It is said that this teahouse was built by a famous tea master during the Edo period. The view of the garden from here is particularly wonderful.",
  "language_note": "'と言われています' (to iwarete imasu) means 'it is said that...'. It's useful for sharing commonly known information or legends."
}}
```

Now, respond to the user's input based on these instructions.
"""
    return base_prompt 