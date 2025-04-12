import openai
from typing import Dict, List, Optional
import os
from app.utils.logger import game_logger

class OpenAIClient:
    """
    Client for interacting with OpenAI API to generate text
    """
    def __init__(self, api_key: str):
        """
        Initialize the OpenAI client
        
        Args:
            api_key: OpenAI API key
        """
        openai.api_key = api_key
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "300"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        game_logger.info(f"OpenAI client initialized with model: {self.model}")

    async def generate_text(self, prompt: str) -> str:
        """
        Generate text using OpenAI API
        
        Args:
            prompt: Prompt for text generation
            
        Returns:
            Generated text
        """
        try:
            game_logger.debug(f"Generating text with prompt: {prompt[:50]}...")
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a Japanese language learning game assistant. You create descriptive, immersive scenes that incorporate Japanese vocabulary naturally."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            generated_text = response.choices[0].message["content"].strip()
            game_logger.debug(f"Generated text: {generated_text[:50]}...")
            
            return generated_text
            
        except Exception as e:
            game_logger.error(f"Error generating text: {str(e)}")
            return "Something went wrong with the AI text generation." 