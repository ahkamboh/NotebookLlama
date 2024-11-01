import os
from groq import Groq
import pypdf
from pathlib import Path
import json
from typing import Optional, Dict, Any
import requests
from dataclasses import dataclass
from gtts import gTTS
import pyttsx3
import random
from pyht import Client
from pyht.client import TTSOptions
import asynciot
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Groq client
client = Groq(
    api_key="add your api key here",
)

# Initialize PlayHT client with provided credentials
playht_client = Client(
    user_id="add your user id here",
    api_key="add your api key here"
)

@dataclass
class ProcessingConfig:
    """Configuration for the NotebookLlama processing pipeline"""
    temperature: float = 0.7
    max_tokens: int = 1500
    pdf_chunk_size: int = 4000

class NotebookLlama:
    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF while maintaining structure"""
        pdf_reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n\n"
        return text

    def _chunk_text(self, text: str, chunk_size: int = 4000) -> list[str]:
        """Split text into manageable chunks"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    async def preprocess_pdf(self, pdf_path: str) -> str:
        """Step 1: Preprocess PDF using llama-3.1-8b-instant"""
        raw_text = self._extract_text_from_pdf(pdf_path)
        chunks = self._chunk_text(raw_text, self.config.pdf_chunk_size)
        processed_chunks = []

        for chunk in chunks:
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Create PDF while preserving context. Clean and structure the text while maintaining its original meaning."
                    },
                    {
                        "role": "user",
                        "content": chunk
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            processed_chunks.append(response.choices[0].message.content)

        return "\n".join(processed_chunks)

    async def generate_podcast_script(self, clean_text: str) -> str:
        """Step 2: Generate podcast script using llama-3.1-70b-versatile"""
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Create an engaging podca st script from the following text. Make it conversational and easy to follow."
                },
                {
                    "role": "user",
                    "content": clean_text
                }
            ],
            model="llama-3.1-70b-versatile",
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        return response.choices[0].message.content

    async def dramatize_script(self, podcast_script: str) -> str:
        """Step 3: Dramatize the podcast script using llama-3.1-8b-instant"""
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Make this podcast script more dramatic and engaging while maintaining its core message."
                },
                {
                    "role": "user",
                    "content": podcast_script
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        return response.choices[0].message.content

    async def generate_audio(self, dramatic_script: str, output_path: str = "podcast.mp3") -> str:
        """Step 4: Generate audio using PlayHT, limited to about 20 seconds"""
        try:
            # Estimate the number of words for 20 seconds of audio
            words_for_20_seconds = 50

            # Truncate the script to the estimated word count
            truncated_script = ' '.join(dramatic_script.split()[:words_for_20_seconds])

            logger.debug(f"Truncated script: {truncated_script}")

            # Generate audio using PlayHT
            options = TTSOptions(
                voice="s3://voice-cloning-zero-shot/a778f067-54d5-4e01-bc3a-3e7406dc0d2f/original/manifest.json",
                format="mp3"
            )
            
            logger.debug("Starting audio generation with PlayHT")
            audio_data = b''
            try:
                for i, chunk in enumerate(playht_client.tts(truncated_script, options)):
                    logger.debug(f"Received chunk {i}: {type(chunk)}, {len(chunk) if chunk is not None else 'None'} bytes")
                    if chunk is not None:
                        audio_data += chunk
                    else:
                        logger.warning(f"Received None chunk from PlayHT API at iteration {i}")
            except Exception as tts_error:
                logger.error(f"Error during TTS generation: {tts_error}", exc_info=True)
                raise

            logger.debug(f"Total audio data received: {len(audio_data)} bytes")

            if not audio_data:
                raise ValueError("No audio data received from PlayHT API")

            # Save the generated audio
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"20-second podcast audio generated and saved as: {output_path}")
            return f"20-second audio generated and saved as {output_path}"
        except Exception as e:
            logger.exception("Error in audio generation")
            return f"Error in audio generation: {str(e)}"

    async def process_document(self, pdf_path: str, output_path: str = "podcast.mp3") -> Dict[str, Any]:
        """Process the entire pipeline"""
        try:
            # Step 1: Preprocess PDF
            clean_text = await self.preprocess_pdf(pdf_path)
            ``
            # Step 2: Generate podcast script
            podcast_script = await self.generate_podcast_script(clean_text)
            
            # Step 3: Dramatize script
            dramatic_script = await self.dramatize_script(podcast_script)
            
            # Step 4: Generate audio
            audio_status = await self.generate_audio(dramatic_script, output_path)
            
            return {
                "status": "success",
                "clean_text": clean_text,
                "podcast_script": podcast_script,
                "dramatic_script": dramatic_script,
                "audio_status": audio_status
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

# Example usage
async def main():
    # Initialize NotebookLlama with custom configuration
    config = ProcessingConfig(
        temperature=0.8,
        max_tokens=2000,
        pdf_chunk_size=3000
    )
    
    notebook_llama = NotebookLlama(config)
    
    # Process a document
    result = await notebook_llama.process_document(
        pdf_path="sample_tech_article.pdf",
        output_path="D:\\Deep learning\\output_podcast.mp3"  # Make sure this path is valid and writable
    )
    
    # Print results
    if result["status"] == "success":
        print("Processing completed successfully!")
        print(f"Audio status: {result['audio_status']}")
    else:
        print(f"Error during processing: {result['error']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
